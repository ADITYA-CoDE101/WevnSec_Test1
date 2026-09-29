import json
import os
import uuid
from dataclasses import dataclass, field

import psycopg2
import pytest
import requests
from dotenv import dotenv_values


def _env(name: str, fallback_env_file: str | None = None) -> str:
    value = os.environ.get(name)
    if value:
        return value
    if fallback_env_file:
        loaded = dotenv_values(fallback_env_file).get(name)
        if loaded:
            return loaded
    pytest.skip(f"Missing required environment variable: {name}")


BASE_URL = _env("REACT_APP_BACKEND_URL", "/app/frontend/.env").rstrip("/")
DATABASE_URL = _env("DATABASE_URL", "/app/backend/.env")
ADMIN_EMAIL = _env("ADMIN_EMAIL", "/app/backend/.env")
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "/app/backend/.env")
DEMO_EMAIL = _env("DEMO_EMAIL", "/app/backend/.env")
DEMO_PASSWORD = _env("DEMO_PASSWORD", "/app/backend/.env")


@dataclass
class Tracker:
    created_doc_ids: list[str] = field(default_factory=list)
    created_scan_share_ids: list[str] = field(default_factory=list)
    created_user_ids: list[str] = field(default_factory=list)
    created_user_emails: list[str] = field(default_factory=list)
    observed_admin_login_status: int | None = None


@pytest.fixture(scope="module")
def http() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def tracker() -> Tracker:
    t = Tracker()
    yield t
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor() as cur:
                if t.created_doc_ids:
                    cur.execute("DELETE FROM wevnsec.documentation WHERE id = ANY(%s::uuid[])", (t.created_doc_ids,))
                if t.created_scan_share_ids:
                    cur.execute("DELETE FROM wevnsec.scans WHERE share_id = ANY(%s)", (t.created_scan_share_ids,))
                if t.created_user_ids:
                    cur.execute("DELETE FROM wevnsec.profiles WHERE id = ANY(%s::uuid[])", (t.created_user_ids,))
                    cur.execute("DELETE FROM auth.users WHERE id = ANY(%s::uuid[])", (t.created_user_ids,))
    finally:
        conn.close()


def api(path: str) -> str:
    return f"{BASE_URL}/api{path}"


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def login(http: requests.Session, email: str, password: str) -> requests.Response:
    return http.post(api("/auth/login"), json={"email": email, "password": password})


def register_disposable_user(http: requests.Session, tracker: Tracker, role_hint: str | None = None):
    local = f"qa-docs-{uuid.uuid4().hex[:10]}"
    email = f"{local}@example.com"
    payload = {"name": f"QA {local}", "email": email, "password": f"QaPwd!{uuid.uuid4().hex[:10]}"}
    if role_hint is not None:
        payload["role"] = role_hint
    response = http.post(api("/auth/register"), json=payload)
    assert response.status_code == 200
    data = response.json()
    tracker.created_user_ids.append(data["user"]["id"])
    tracker.created_user_emails.append(email)
    return payload, data


def promote_admin(user_id: str):
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE wevnsec.profiles SET role='admin' WHERE id=%s", (user_id,))
    finally:
        conn.close()


def stream_scan(http: requests.Session, payload: dict, headers: dict | None = None):
    response = http.post(api("/scan/stream"), json=payload, headers=headers or {}, stream=True, timeout=90)
    return response


def stats(http: requests.Session) -> dict:
    response = http.get(api("/stats"), timeout=30)
    assert response.status_code == 200
    data = response.json()
    for key in ("scans", "findings", "vulns", "warnings", "docs_count", "checks_supported"):
        assert key in data
    return data


# auth + authorization checks around docs management and role integrity
def test_guest_admin_docs_requires_auth(http):
    response = http.get(api("/admin/docs"), timeout=30)
    assert response.status_code == 401
    assert "detail" in response.json()


def test_admin_env_login_observation(http, tracker):
    response = login(http, ADMIN_EMAIL, ADMIN_PASSWORD)
    tracker.observed_admin_login_status = response.status_code
    assert response.status_code in (200, 401)


def test_registration_cannot_self_grant_admin_role(http, tracker):
    payload, data = register_disposable_user(http, tracker, role_hint="admin")
    token = data["token"]
    assert data["user"]["email"] == payload["email"].lower()
    assert data["user"]["role"] == "user"

    me = http.get(api("/auth/me"), headers=auth_header(token), timeout=30)
    assert me.status_code == 200
    assert me.json()["role"] == "user"

    forbidden = http.get(api("/admin/docs"), headers=auth_header(token), timeout=30)
    assert forbidden.status_code == 403


@pytest.fixture(scope="module")
def demo_token(http):
    response = login(http, DEMO_EMAIL, DEMO_PASSWORD)
    if response.status_code != 200:
        pytest.skip("Demo login failed; skipping non-admin gate checks")
    return response.json()["token"]


@pytest.fixture(scope="module")
def disposable_admin(http, tracker):
    creds, data = register_disposable_user(http, tracker)
    promote_admin(data["user"]["id"])
    response = login(http, creds["email"], creds["password"])
    assert response.status_code == 200
    login_data = response.json()
    assert login_data["user"]["role"] == "admin"
    return {"token": login_data["token"], "id": login_data["user"]["id"], "email": creds["email"], "password": creds["password"]}


def _doc_payload(slug: str, coverage: str = "educational", published: bool = False, version: int | None = None):
    payload = {
        "slug": slug,
        "title": f"QA Doc {slug}",
        "summary": "QA validation article summary with enough length.",
        "category": "Access control",
        "severity": "medium",
        "coverage": coverage,
        "check_ids": [] if coverage == "educational" else ["TLS-01"],
        "explanation": "This is a QA explanation body with enough words for validation.",
        "impact": "This is QA impact text.",
        "mitigation": "This is QA mitigation text that is long enough.",
        "validation": "Run QA validation checks.",
        "limitations": "This is a QA limitations statement.",
        "reference_url": "https://owasp.org",
        "published": published,
    }
    if version is not None:
        payload["version"] = version
    return payload


# docs public/admin CRUD and validation contracts
def test_demo_user_cannot_access_admin_docs(http, demo_token):
    response = http.get(api("/admin/docs"), headers=auth_header(demo_token), timeout=30)
    assert response.status_code == 403


def test_public_docs_and_catalog_shape(http):
    docs = http.get(api("/docs"), timeout=30)
    assert docs.status_code == 200
    doc_rows = docs.json()
    assert len(doc_rows) >= 22
    assert all(row["published"] is True for row in doc_rows)
    assert {row["coverage"] for row in doc_rows}.issuperset({"automated", "educational"})

    automated = http.get(api("/docs?coverage=automated"), timeout=30)
    educational = http.get(api("/docs?coverage=educational"), timeout=30)
    assert automated.status_code == 200
    assert educational.status_code == 200
    assert all(row["coverage"] == "automated" for row in automated.json())
    assert all(row["coverage"] == "educational" for row in educational.json())

    catalog = http.get(api("/docs/catalog"), timeout=30)
    assert catalog.status_code == 200
    rows = catalog.json()
    assert len(rows) == 14
    assert any(c["id"] == "LEAK-01" for c in rows)


def test_draft_create_stays_private_and_does_not_increment_docs_stats(http, disposable_admin, tracker):
    before = stats(http)
    slug = f"qa-docs-draft-{uuid.uuid4().hex[:8]}"
    response = http.post(api("/admin/docs"), headers=auth_header(disposable_admin["token"]), json=_doc_payload(slug, coverage="educational", published=False), timeout=30)
    assert response.status_code == 201
    created = response.json()
    tracker.created_doc_ids.append(created["id"])
    assert created["published"] is False
    assert created["version"] == 1

    public = http.get(api(f"/docs/{slug}"), timeout=30)
    assert public.status_code == 404

    after = stats(http)
    assert int(after["docs_count"]) == int(before["docs_count"])


def test_published_create_is_visible_and_increments_docs_stats(http, disposable_admin, tracker):
    before = stats(http)
    slug = f"qa-docs-published-{uuid.uuid4().hex[:8]}"
    response = http.post(api("/admin/docs"), headers=auth_header(disposable_admin["token"]), json=_doc_payload(slug, coverage="automated", published=True), timeout=30)
    assert response.status_code == 201
    created = response.json()
    tracker.created_doc_ids.append(created["id"])
    assert created["published"] is True
    assert created["check_ids"] == ["TLS-01"]

    public = http.get(api(f"/docs/{slug}"), timeout=30)
    assert public.status_code == 200
    public_doc = public.json()
    assert public_doc["slug"] == slug
    assert public_doc["coverage"] == "automated"

    after = stats(http)
    assert int(after["docs_count"]) == int(before["docs_count"]) + 1


def test_admin_edit_versioning_and_conflict_rules(http, disposable_admin, tracker):
    token = disposable_admin["token"]
    slug_a = f"qa-docs-edit-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"qa-docs-edit-b-{uuid.uuid4().hex[:8]}"

    a = http.post(api("/admin/docs"), headers=auth_header(token), json=_doc_payload(slug_a, coverage="automated", published=True), timeout=30)
    b = http.post(api("/admin/docs"), headers=auth_header(token), json=_doc_payload(slug_b, coverage="educational", published=False), timeout=30)
    assert a.status_code == 201
    assert b.status_code == 201
    doc_a = a.json()
    doc_b = b.json()
    tracker.created_doc_ids.extend([doc_a["id"], doc_b["id"]])

    update_payload = _doc_payload(slug_a, coverage="educational", published=True, version=doc_a["version"])
    update_payload.update({
        "title": f"Edited {slug_a}",
        "summary": "Edited summary with sufficient content for QA verification.",
        "category": "Session security",
        "severity": "high",
        "check_ids": [],
        "explanation": "Edited explanation body for QA checks in editor save flow.",
        "impact": "Edited impact body for QA tests.",
        "mitigation": "Edited mitigation text meeting validation constraints.",
        "validation": "Edited validation guidance.",
        "limitations": "Edited limitations content for QA.",
        "reference_url": "https://developer.mozilla.org",
    })
    updated = http.put(api(f"/admin/docs/{doc_a['id']}"), headers=auth_header(token), json=update_payload, timeout=30)
    assert updated.status_code == 200
    updated_doc = updated.json()
    assert updated_doc["version"] == doc_a["version"] + 1
    assert updated_doc["title"] == f"Edited {slug_a}"
    assert updated_doc["coverage"] == "educational"

    stale = http.put(api(f"/admin/docs/{doc_a['id']}"), headers=auth_header(token), json=update_payload, timeout=30)
    assert stale.status_code == 409

    slug_conflict = dict(update_payload)
    slug_conflict["version"] = updated_doc["version"]
    slug_conflict["slug"] = doc_b["slug"]
    conflict = http.put(api(f"/admin/docs/{doc_a['id']}"), headers=auth_header(token), json=slug_conflict, timeout=30)
    assert conflict.status_code == 409


def test_admin_validation_rules_for_docs_payloads(http, disposable_admin):
    token = disposable_admin["token"]

    reserved = http.post(api("/admin/docs"), headers=auth_header(token), json=_doc_payload("manage", coverage="educational", published=False), timeout=30)
    assert reserved.status_code == 422

    bad_ref = _doc_payload(f"qa-docs-http-{uuid.uuid4().hex[:8]}", coverage="educational", published=False)
    bad_ref["reference_url"] = "http://example.com"
    ref_response = http.post(api("/admin/docs"), headers=auth_header(token), json=bad_ref, timeout=30)
    assert ref_response.status_code == 422

    edu_with_check = _doc_payload(f"qa-docs-edu-{uuid.uuid4().hex[:8]}", coverage="educational", published=False)
    edu_with_check["check_ids"] = ["TLS-01"]
    edu_response = http.post(api("/admin/docs"), headers=auth_header(token), json=edu_with_check, timeout=30)
    assert edu_response.status_code == 422

    auto_no_check = _doc_payload(f"qa-docs-auto-{uuid.uuid4().hex[:8]}", coverage="automated", published=False)
    auto_no_check["check_ids"] = []
    auto_response = http.post(api("/admin/docs"), headers=auth_header(token), json=auto_no_check, timeout=30)
    assert auto_response.status_code == 422


# stream scan, persistence, stats deltas, and compatibility endpoint behavior
def test_scan_stream_invalid_domain_400(http):
    guest = requests.Session()
    guest.headers.update({"Content-Type": "application/json"})
    response = stream_scan(guest, {"target": "localhost", "advanced": False})
    assert response.status_code == 400
    body = response.json()
    assert "detail" in body


def test_scan_stream_advanced_requires_ownership(http, demo_token):
    response = stream_scan(http, {"target": "example.com", "advanced": True}, headers=auth_header(demo_token))
    assert response.status_code == 403
    body = response.json()
    assert "detail" in body


def test_scan_stream_complete_matches_saved_report_and_stats_once(http, disposable_admin, tracker):
    before = stats(http)
    response = stream_scan(http, {"target": "example.com", "advanced": False}, headers=auth_header(disposable_admin["token"]))
    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers.get("content-type", "")

    events = [json.loads(line.decode("utf-8")) for line in response.iter_lines() if line]
    assert events
    assert events[0]["type"] == "started"
    assert any(event["type"] == "check" for event in events)
    assert events[-1]["type"] == "complete"

    report = events[-1]["report"]
    tracker.created_scan_share_ids.append(report["share_id"])
    checks = [event["check"] for event in events if event["type"] == "check"]
    assert len(checks) == len(report["checks"])
    assert {c["id"] for c in checks} == {c["id"] for c in report["checks"]}

    saved = http.get(api(f"/scan/{report['share_id']}"), timeout=30)
    assert saved.status_code == 200
    saved_report = saved.json()
    assert saved_report["share_id"] == report["share_id"]
    assert len(saved_report["checks"]) == len(report["checks"])

    expected_findings = sum(1 for c in report["checks"] if c["status"] in ("fail", "warn"))
    expected_vulns = sum(1 for c in report["checks"] if c["status"] == "fail")
    expected_warnings = sum(1 for c in report["checks"] if c["status"] == "warn")

    after = stats(http)
    assert int(after["scans"]) == int(before["scans"]) + 1
    assert int(after["findings"]) == int(before["findings"]) + expected_findings
    assert int(after["vulns"]) == int(before["vulns"]) + expected_vulns
    assert int(after["warnings"]) == int(before["warnings"]) + expected_warnings
    assert int(after["checks_supported"]) == 14


def test_scan_stream_client_cancel_has_no_fake_complete_event(http, disposable_admin):
    response = stream_scan(http, {"target": "example.com", "advanced": False}, headers=auth_header(disposable_admin["token"]))
    assert response.status_code == 200

    seen_types = []
    for line in response.iter_lines():
        if not line:
            continue
        event = json.loads(line.decode("utf-8"))
        seen_types.append(event["type"])
        if event["type"] == "check":
            break

    response.close()
    assert "started" in seen_types
    assert "check" in seen_types
    assert "complete" not in seen_types


def test_post_scan_endpoint_still_works(http, disposable_admin, tracker):
    response = http.post(api("/scan"), headers=auth_header(disposable_admin["token"]), json={"target": "example.com", "advanced": False}, timeout=90)
    assert response.status_code == 200
    data = response.json()
    tracker.created_scan_share_ids.append(data["share_id"])
    assert data["target"] == "example.com"
    assert isinstance(data["checks"], list)
    assert len(data["checks"]) > 0