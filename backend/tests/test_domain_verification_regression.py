"""Domain ownership verification and scan authorization regression coverage."""

import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2
import pytest
import requests
from dotenv import dotenv_values


ROOT = "/app"
FRONTEND_ENV = dotenv_values(f"{ROOT}/frontend/.env")
BACKEND_ENV = dotenv_values(f"{ROOT}/backend/.env")

BASE_URL = FRONTEND_ENV.get("REACT_APP_BACKEND_URL", "").rstrip("/")
DATABASE_URL = BACKEND_ENV.get("DATABASE_URL", "")
DEMO_EMAIL = BACKEND_ENV.get("DEMO_EMAIL", "")
DEMO_PASSWORD = BACKEND_ENV.get("DEMO_PASSWORD", "")
CRON_SECRET = BACKEND_ENV.get("WEBHOOK_CRON_SECRET", "")

CREATED_AUTH_USER_IDS: set[str] = set()
CREATED_AUTH_EMAILS: set[str] = set()


def _assert_env():
    missing = [
        name
        for name, value in {
            "REACT_APP_BACKEND_URL": BASE_URL,
            "DATABASE_URL": DATABASE_URL,
            "DEMO_EMAIL": DEMO_EMAIL,
            "DEMO_PASSWORD": DEMO_PASSWORD,
            "WEBHOOK_CRON_SECRET": CRON_SECRET,
        }.items()
        if not value
    ]
    if missing:
        pytest.fail(f"Missing required env values: {missing}")


_assert_env()


@pytest.fixture(scope="session")
def demo_token():
    """Auth fixture: demo user bearer token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        timeout=20,
    )
    assert response.status_code == 200, response.text
    token = response.json().get("token")
    assert isinstance(token, str) and token
    return token


@pytest.fixture()
def demo_client(demo_token):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {demo_token}"})
    return session


@pytest.fixture(scope="session")
def second_user_token():
    """Auth fixture: create/login disposable second user for ownership conflict tests."""
    email = f"qa-v26-owner-{uuid.uuid4().hex[:8]}@example.com"
    password = "QaOwnerPass123!"
    signup = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"name": "QA Owner", "email": email, "password": password},
        timeout=30,
    )
    assert signup.status_code in (200, 201), signup.text
    token = signup.json().get("token")
    assert isinstance(token, str) and token
    user_id = (signup.json().get("user") or {}).get("id")
    if isinstance(user_id, str) and user_id:
        CREATED_AUTH_USER_IDS.add(user_id)
    CREATED_AUTH_EMAILS.add(email)
    return token


@pytest.fixture()
def second_user_client(second_user_token):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {second_user_token}"})
    return session


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_records():
    """Cleanup fixture: remove only this run's QA rows and disposable auth users."""
    yield
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM wevnsec.domains WHERE domain LIKE 'qa-v26-%'")
            cur.execute("DELETE FROM wevnsec.cron_deliveries WHERE run_id LIKE 'qa-cron-%'")
            if CREATED_AUTH_USER_IDS:
                cur.execute("DELETE FROM wevnsec.profiles WHERE id::text = ANY(%s)", (list(CREATED_AUTH_USER_IDS),))
            if CREATED_AUTH_EMAILS:
                cur.execute("DELETE FROM auth.users WHERE email = ANY(%s)", (list(CREATED_AUTH_EMAILS),))
        conn.commit()


def unique_domain(prefix="qa-v26"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}.com"


def add_domain(client, domain_value):
    return client.post(f"{BASE_URL}/api/domains", json={"domain": domain_value}, timeout=20)


def test_domain_add_normalizes_and_instructions_token_stability(demo_client):
    """Domain CRUD basics: add/get/list with stable token and instructions."""
    domain = unique_domain()
    create = add_domain(demo_client, f"https://{domain}/path?x=1")
    assert create.status_code == 201, create.text
    created = create.json()
    assert created["domain"] == domain
    assert isinstance(created["id"], str)
    assert isinstance(created["verification_token"], str) and len(created["verification_token"]) > 20
    assert created["verification_status"] == "pending"
    assert created["instructions"]["dns_txt"]["value"] == f"wevnsec-verify={created['verification_token']}"

    get_one = demo_client.get(f"{BASE_URL}/api/domains/{created['id']}", timeout=20)
    assert get_one.status_code == 200, get_one.text
    fetched = get_one.json()
    assert fetched["verification_token"] == created["verification_token"]
    assert fetched["instructions"]["html_file"]["filename"] == f"wevnsec-{created['verification_token']}.txt"

    listing = demo_client.get(f"{BASE_URL}/api/domains", timeout=20)
    assert listing.status_code == 200, listing.text
    listed = next(item for item in listing.json() if item["id"] == created["id"])
    assert listed["verification_token"] == created["verification_token"]
    assert listed["domain"] == domain


@pytest.mark.parametrize(
    "candidate,reason_hint",
    [
        ("*.example.com", "invalid_domain"),
        ("192.168.1.10", "invalid_domain"),
        ("co.uk", "invalid_domain"),
        ("subdomain.example.com", "Verify the apex domain example.com"),
        ("子.例子.公司.cn", "Verify the apex domain"),
    ],
)
def test_invalid_domain_validation_messages(demo_client, candidate, reason_hint):
    """Validation rules: reject wildcard/IP/public suffix/subdomain with helpful details."""
    response = add_domain(demo_client, candidate)
    assert response.status_code == 400, response.text
    detail = response.json()["detail"]
    assert detail["reason"] == "invalid_domain"
    if reason_hint != "invalid_domain":
        assert reason_hint in detail["message"]


def test_same_user_duplicate_claim_returns_409(demo_client):
    """Ownership uniqueness: same-user duplicate domain claim blocked."""
    domain = unique_domain()
    first = add_domain(demo_client, domain)
    assert first.status_code == 201, first.text
    second = add_domain(demo_client, domain)
    assert second.status_code == 409, second.text
    detail = second.json()["detail"]
    assert detail["reason"] == "domain_already_claimed"


def test_cross_user_duplicate_and_idor_delete_protection(demo_client, second_user_client):
    """Ownership security: one owner globally and IDOR delete blocked."""
    domain = unique_domain()
    created = add_domain(demo_client, domain)
    assert created.status_code == 201, created.text
    domain_id = created.json()["id"]

    conflict = add_domain(second_user_client, domain)
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["detail"]["reason"] == "domain_already_claimed"

    forbidden_delete = second_user_client.delete(f"{BASE_URL}/api/domains/{domain_id}", timeout=20)
    assert forbidden_delete.status_code == 404, forbidden_delete.text

    remove_owner = demo_client.delete(f"{BASE_URL}/api/domains/{domain_id}", timeout=20)
    assert remove_owner.status_code == 200, remove_owner.text
    assert remove_owner.json()["ok"] is True


def test_verify_failure_and_reverify_guard_for_unverified(demo_client):
    """Verification state: initial check failure and reverify precondition."""
    domain = unique_domain()
    created = add_domain(demo_client, domain)
    assert created.status_code == 201, created.text
    domain_id = created.json()["id"]

    verify = demo_client.post(
        f"{BASE_URL}/api/domains/{domain_id}/verify",
        json={"method": "dns_txt"},
        timeout=20,
    )
    assert verify.status_code == 200, verify.text
    payload = verify.json()
    assert payload["success"] is False
    assert payload["verification_status"] == "failed"
    assert payload["reason"] in {"dns_record_not_found", "timeout", "dns_record_mismatch"}

    reverify = demo_client.post(
        f"{BASE_URL}/api/domains/{domain_id}/reverify",
        json={"method": "dns_txt"},
        timeout=20,
    )
    assert reverify.status_code == 409, reverify.text
    assert reverify.json()["detail"]["reason"] == "verification_required"


def test_expired_pending_verification_rejected_with_410(demo_client):
    """Verification expiry: never-verified expired token must reject without success."""
    domain = unique_domain()
    created = add_domain(demo_client, domain)
    assert created.status_code == 201, created.text
    domain_id = created.json()["id"]

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE wevnsec.domains
                SET token_expires_at = %s, verified = FALSE, verification_status = 'pending', verified_at = NULL
                WHERE id = %s
                """,
                (datetime.now(timezone.utc) - timedelta(days=1), domain_id),
            )
        conn.commit()

    verify = demo_client.post(
        f"{BASE_URL}/api/domains/{domain_id}/verify",
        json={"method": "html_file"},
        timeout=20,
    )
    assert verify.status_code == 410, verify.text
    assert verify.json()["detail"]["reason"] == "token_expired"


def test_scan_access_rules_and_monitoring_patch(demo_client):
    """Scan authorization: instant scan open, advanced scan gated, monitoring enable gated."""
    public_scan = requests.post(
        f"{BASE_URL}/api/scan",
        json={"target": "example.com", "advanced": False},
        timeout=40,
    )
    assert public_scan.status_code == 200, public_scan.text
    report = public_scan.json()
    assert report["target"] == "example.com"
    assert isinstance(report["checks"], list) and len(report["checks"]) > 0

    no_owner_advanced = requests.post(
        f"{BASE_URL}/api/scan",
        json={"target": "example.com", "advanced": True},
        timeout=20,
    )
    assert no_owner_advanced.status_code == 403, no_owner_advanced.text
    detail = no_owner_advanced.json()["detail"]
    assert detail["reason"] == "ownership_required"

    # Ownership gate should reject authenticated advanced scans for non-owned domains.
    authed_non_owner_advanced = demo_client.post(
        f"{BASE_URL}/api/scan",
        json={"target": "github.com", "advanced": True},
        timeout=20,
    )
    assert authed_non_owner_advanced.status_code == 403, authed_non_owner_advanced.text
    assert authed_non_owner_advanced.json()["detail"]["reason"] == "ownership_required"

    domain = unique_domain()
    created = add_domain(demo_client, domain)
    assert created.status_code == 201, created.text
    domain_id = created.json()["id"]

    schedule_before_verify = demo_client.patch(
        f"{BASE_URL}/api/domains/{domain_id}",
        json={"monitoring_enabled": True},
        timeout=20,
    )
    assert schedule_before_verify.status_code == 403, schedule_before_verify.text
    assert schedule_before_verify.json()["detail"]["reason"] == "ownership_required"


def test_cron_endpoint_auth_envelope_and_cleanup_idempotency(demo_client):
    """Cron cleanup: auth, envelope validation, async ack, idempotency, retention rules."""
    missing_auth = requests.post(f"{BASE_URL}/api/cron/domain-cleanup", json={}, timeout=20)
    assert missing_auth.status_code == 401, missing_auth.text

    bad_auth = requests.post(
        f"{BASE_URL}/api/cron/domain-cleanup",
        headers={"Authorization": "Bearer wrong-secret"},
        json={"event": "schedule.triggered", "run_id": "qa-cron-bad"},
        timeout=20,
    )
    assert bad_auth.status_code == 401, bad_auth.text

    non_ascii_auth = requests.post(
        f"{BASE_URL}/api/cron/domain-cleanup",
        headers={"Authorization": "Bearer inválid"},
        json={"event": "schedule.triggered", "run_id": "qa-cron-unicode"},
        timeout=20,
    )
    assert non_ascii_auth.status_code == 401, non_ascii_auth.text

    invalid_envelope = requests.post(
        f"{BASE_URL}/api/cron/domain-cleanup",
        headers={"Authorization": f"Bearer {CRON_SECRET}"},
        json={"event": "wrong.event", "run_id": "qa-cron-invalid"},
        timeout=20,
    )
    assert invalid_envelope.status_code == 400, invalid_envelope.text

    pending_domain = unique_domain("qa-v26-pending")
    failed_domain = unique_domain("qa-v26-failed")
    verified_domain = unique_domain("qa-v26-verified")
    needs_domain = unique_domain("qa-v26-needs")

    created_pending = add_domain(demo_client, pending_domain)
    created_failed = add_domain(demo_client, failed_domain)
    created_verified = add_domain(demo_client, verified_domain)
    created_needs = add_domain(demo_client, needs_domain)
    assert all(r.status_code == 201 for r in [created_pending, created_failed, created_verified, created_needs])

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            expiry = datetime.now(timezone.utc) - timedelta(days=2)
            cur.execute(
                """
                UPDATE wevnsec.domains
                SET verification_status='failed', token_expires_at=%s, verified=FALSE, verified_at=NULL
                WHERE domain=%s
                """,
                (expiry, failed_domain),
            )
            cur.execute(
                """
                UPDATE wevnsec.domains
                SET verification_status='pending', token_expires_at=%s, verified=FALSE, verified_at=NULL
                WHERE domain=%s
                """,
                (expiry, pending_domain),
            )
            cur.execute(
                """
                UPDATE wevnsec.domains
                SET verification_status='verified', verified=TRUE, verified_at=%s, token_expires_at=%s
                WHERE domain=%s
                """,
                (datetime.now(timezone.utc) - timedelta(days=1), expiry, verified_domain),
            )
            cur.execute(
                """
                UPDATE wevnsec.domains
                SET verification_status='needs_reverification', verified=TRUE, verified_at=%s, token_expires_at=%s
                WHERE domain=%s
                """,
                (datetime.now(timezone.utc) - timedelta(days=1), expiry, needs_domain),
            )
        conn.commit()

    run_id = f"qa-cron-{uuid.uuid4().hex[:10]}"
    accepted = requests.post(
        f"{BASE_URL}/api/cron/domain-cleanup",
        headers={
            "Authorization": f"Bearer {CRON_SECRET}",
            "x-webhook-id": run_id,
        },
        json={"event": "schedule.triggered", "run_id": run_id},
        timeout=20,
    )
    assert accepted.status_code == 202, accepted.text
    body = accepted.json()
    assert body["accepted"] is True

    completed = False
    for _ in range(20):
        time.sleep(0.5)
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT status, deleted_count FROM wevnsec.cron_deliveries WHERE run_id=%s", (run_id,))
                row = cur.fetchone()
                if row and row[0] == "completed":
                    completed = True
                    assert row[1] >= 2
                    break
    assert completed, "cron delivery did not reach completed status in time"

    duplicate = requests.post(
        f"{BASE_URL}/api/cron/domain-cleanup",
        headers={"Authorization": f"Bearer {CRON_SECRET}", "x-webhook-id": run_id},
        json={"event": "schedule.triggered", "run_id": run_id},
        timeout=20,
    )
    assert duplicate.status_code == 202, duplicate.text
    assert duplicate.json()["duplicate"] is True

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM wevnsec.domains WHERE domain IN (%s,%s)", (pending_domain, failed_domain))
            deleted_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM wevnsec.domains WHERE domain IN (%s,%s)", (verified_domain, needs_domain))
            retained_count = cur.fetchone()[0]
    assert deleted_count == 0
    assert retained_count == 2


def test_domain_inputs_forbid_extra_fields(demo_client):
    """Pydantic guards: client cannot inject extra fields (including verification token)."""
    bad_add = demo_client.post(
        f"{BASE_URL}/api/domains",
        json={"domain": unique_domain(), "verification_token": "attacker-token"},
        timeout=20,
    )
    assert bad_add.status_code == 422, bad_add.text

    created = add_domain(demo_client, unique_domain())
    assert created.status_code == 201, created.text
    domain_id = created.json()["id"]
    bad_verify = demo_client.post(
        f"{BASE_URL}/api/domains/{domain_id}/verify",
        json={"method": "dns_txt", "token": "attacker-token"},
        timeout=20,
    )
    assert bad_verify.status_code == 422, bad_verify.text


def test_crons_yaml_contract_has_no_secret_material():
    """Cron contract: schedule metadata exists and no bearer secret is embedded in YAML."""
    text = Path("/app/.emergent/crons.yml").read_text(encoding="utf-8")
    lower = text.lower()
    assert "name: domain-token-cleanup" in text
    assert "endpoint: \"{{BASE_URL}}/api/cron/domain-cleanup\"" in text
    assert "method: POST" in text
    assert "cron:" in text
    assert "webhook_cron_secret" not in lower
    assert "authorization:" not in lower
