"""Isolated verification logic tests (DNS/HTTP proof checks and state machine)."""

import os
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

sys.path.insert(0, "/app/backend")

import domain_routes
from domain_routes import attempt
from domain_validation import VerificationError
from domain_verification import check_proof
from ownership import require_ownership
from verification_dns import txt_value, verify_dns


def _make_domain(**overrides):
    now = datetime.now(timezone.utc)
    base = {
        "id": "11111111-1111-1111-1111-111111111111",
        "domain": "qa-v26-unit-example.com",
        "verification_token": "tok_unit_123",
        "verified": False,
        "verification_status": "pending",
        "verification_method": None,
        "token_expires_at": now + timedelta(days=7),
        "verified_at": None,
        "last_verification_at": None,
        "last_verification_error": None,
        "monitoring_enabled": False,
        "next_scan_at": None,
        "email_alerts_enabled": False,
        "scan_lock_until": None,
        "last_scan_error": None,
        "created_at": now,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class FakeDB:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeOwnershipDB:
    def __init__(self, value):
        self.value = value

    async def execute(self, _query):
        return FakeResult(self.value)


def test_txt_value_concatenates_chunks():
    """DNS TXT parsing: quoted TXT chunks must be concatenated before comparison."""
    assert txt_value('"wevnsec-" "verify=abc"') == "wevnsec-verify=abc"


@pytest.mark.anyio
async def test_verify_dns_txt_exact_match_only(monkeypatch):
    """DNS TXT validation: exact token string required, not substring match."""

    async def fake_lookup(name, record_type, **kwargs):
        assert name == "qa-v26-unit-example.com"
        assert record_type == "TXT"
        return ['"xwevnsec-verify=tok_unit_123y"']

    monkeypatch.setattr("verification_dns.lookup", fake_lookup)
    with pytest.raises(VerificationError) as exc:
        await verify_dns("qa-v26-unit-example.com", "tok_unit_123", "dns_txt")
    assert exc.value.reason == "dns_record_mismatch"


@pytest.mark.anyio
async def test_verify_dns_txt_chunked_exact_success(monkeypatch):
    """DNS TXT validation: chunked TXT record is accepted when exact value reconstructs."""

    async def fake_lookup(name, record_type, **kwargs):
        return ['"wevnsec-" "verify=tok_unit_123"']

    monkeypatch.setattr("verification_dns.lookup", fake_lookup)
    await verify_dns("qa-v26-unit-example.com", "tok_unit_123", "dns_txt")


@pytest.mark.anyio
async def test_verify_dns_cname_normalizes_case_and_trailing_dot(monkeypatch):
    """CNAME validation: target comparison should be case-insensitive and dot-normalized."""

    async def fake_lookup(name, record_type, **kwargs):
        assert name == "_wevnsec.qa-v26-unit-example.com"
        return ["VERIFY.WEVNSEC.COM."]

    monkeypatch.setattr("verification_dns.lookup", fake_lookup)
    monkeypatch.setenv("VERIFICATION_CNAME_TARGET", "verify.wevnsec.com")
    await verify_dns("qa-v26-unit-example.com", "tok_unit_123", "dns_cname")


@pytest.mark.anyio
async def test_check_proof_html_file_requires_exact_content(monkeypatch):
    """HTML file method: file body must exactly equal token."""

    async def fake_fetch_html(host, path):
        return "tok_unit_123 extra"

    monkeypatch.setattr("domain_verification.fetch_html", fake_fetch_html)
    with pytest.raises(VerificationError) as exc:
        await check_proof(_make_domain(), "html_file")
    assert exc.value.reason == "http_file_unreachable"


@pytest.mark.anyio
async def test_check_proof_html_file_success_uses_required_path(monkeypatch):
    """HTML file method: success requires token at exact /.well-known/wevnsec-<token>.txt path."""

    async def exact_file(host, path):
        assert host == "qa-v26-unit-example.com"
        assert path == "/.well-known/wevnsec-tok_unit_123.txt"
        return "tok_unit_123"

    monkeypatch.setattr("domain_verification.fetch_html", exact_file)
    await check_proof(_make_domain(), "html_file")


@pytest.mark.anyio
async def test_check_proof_meta_must_exist_in_head(monkeypatch):
    """Meta method: token in body/wrong place must not pass."""

    async def body_only_meta(host, path):
        return '<html><body><meta name="wevnsec-verification" content="tok_unit_123"></body></html>'

    monkeypatch.setattr("domain_verification.fetch_html", body_only_meta)
    with pytest.raises(VerificationError) as exc:
        await check_proof(_make_domain(), "html_meta")
    assert exc.value.reason == "meta_tag_missing"


@pytest.mark.anyio
async def test_check_proof_meta_head_exact_success(monkeypatch):
    """Meta method: exact verification tag in <head> should pass."""

    async def good_meta(host, path):
        return '<html><head><meta name="wevnsec-verification" content="tok_unit_123"></head><body></body></html>'

    monkeypatch.setattr("domain_verification.fetch_html", good_meta)
    await check_proof(_make_domain(), "html_meta")


@pytest.mark.anyio
async def test_attempt_idempotent_after_verified_without_network(monkeypatch):
    """State machine: /verify on already verified domain should be idempotent."""
    domain = _make_domain(verified=True, verification_status="verified", verified_at=datetime.now(timezone.utc))
    db = FakeDB()
    called = {"value": False}

    async def never_call(*args, **kwargs):
        called["value"] = True

    monkeypatch.setattr(domain_routes, "check_proof", never_call)
    result = await attempt(db, domain, "dns_txt", reverify=False)
    assert result["success"] is True
    assert result["reason"] is None
    assert called["value"] is False
    assert db.commits == 0


@pytest.mark.anyio
async def test_attempt_reverify_failure_sets_needs_reverification(monkeypatch):
    """State machine: failed reverify keeps verified=true and verified_at timestamp."""
    verified_at = datetime.now(timezone.utc) - timedelta(days=1)
    domain = _make_domain(verified=True, verification_status="verified", verified_at=verified_at)
    db = FakeDB()

    async def fail_proof(*args, **kwargs):
        raise VerificationError("dns_record_not_found", "missing")

    monkeypatch.setattr(domain_routes, "check_proof", fail_proof)
    result = await attempt(db, domain, "dns_txt", reverify=True)
    assert result["success"] is False
    assert result["verification_status"] == "needs_reverification"
    assert domain.verified is True
    assert domain.verified_at == verified_at
    assert db.commits == 1


@pytest.mark.anyio
async def test_attempt_initial_failure_sets_failed(monkeypatch):
    """State machine: initial failed verification marks failed status."""
    domain = _make_domain(verified=False, verification_status="pending")
    db = FakeDB()

    async def fail_proof(*args, **kwargs):
        raise VerificationError("timeout", "timed out")

    monkeypatch.setattr(domain_routes, "check_proof", fail_proof)
    result = await attempt(db, domain, "html_file", reverify=False)
    assert result["success"] is False
    assert result["verification_status"] == "failed"
    assert domain.verified is False
    assert db.commits == 1


@pytest.mark.anyio
async def test_attempt_expired_never_verified_rejects_410(monkeypatch):
    """State machine: expired unverified token should reject before proof network checks."""
    domain = _make_domain(token_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1), verified=False)
    db = FakeDB()
    called = {"value": False}

    async def never_call(*args, **kwargs):
        called["value"] = True

    monkeypatch.setattr(domain_routes, "check_proof", never_call)
    with pytest.raises(HTTPException) as exc:
        await attempt(db, domain, "dns_txt", reverify=False)
    assert exc.value.status_code == 410
    assert called["value"] is False


@pytest.mark.anyio
async def test_attempt_success_failure_recovery_stabilizes_verified_at_and_token(monkeypatch):
    """State machine: first verify success -> failed reverify -> successful reverify recovery."""
    now = datetime.now(timezone.utc)
    domain = _make_domain(verified=False, verification_status="pending", token_expires_at=now + timedelta(days=7))
    original_token = domain.verification_token
    db = FakeDB()
    calls = {"count": 0}

    async def proof_sequence(_domain, _method):
        calls["count"] += 1
        if calls["count"] == 2:
            raise VerificationError("dns_record_not_found", "missing")

    monkeypatch.setattr(domain_routes, "check_proof", proof_sequence)

    first = await attempt(db, domain, "html_file", reverify=False)
    assert first["success"] is True
    assert domain.verified is True
    assert domain.verification_status == "verified"
    first_verified_at = domain.verified_at
    assert first_verified_at is not None
    assert domain.verification_token == original_token

    domain.token_expires_at = now - timedelta(minutes=1)
    second = await attempt(db, domain, "html_file", reverify=True)
    assert second["success"] is False
    assert domain.verification_status == "needs_reverification"
    assert domain.verified is True
    assert domain.verified_at == first_verified_at
    assert domain.verification_token == original_token

    third = await attempt(db, domain, "html_file", reverify=True)
    assert third["success"] is True
    assert domain.verification_status == "verified"
    assert domain.verified is True
    assert domain.verified_at == first_verified_at
    assert domain.verification_token == original_token

    already_verified = await attempt(db, domain, "html_file", reverify=False)
    assert already_verified["success"] is True
    assert calls["count"] == 3


@pytest.mark.anyio
async def test_require_ownership_allows_apex_and_deep_subdomain_with_needs_reverification():
    """Ownership gate: previously verified apex authorizes deep subdomains even when reverify is needed."""
    domain = SimpleNamespace(domain="example.com", verified=True, verification_status="needs_reverification")
    db = FakeOwnershipDB(domain)
    assert await require_ownership(db, "user-1", "api.deep.example.com") is domain


@pytest.mark.anyio
async def test_require_ownership_rejects_suffix_spoof():
    """Ownership gate: example.com ownership must not authorize example.com.evil.com."""
    db = FakeOwnershipDB(None)
    with pytest.raises(HTTPException) as exc:
        await require_ownership(db, "user-1", "example.com.evil.com")
    assert exc.value.status_code == 403
    assert exc.value.detail["reason"] == "ownership_required"
    assert "evil.com" in exc.value.detail["message"]


@pytest.mark.anyio
async def test_require_ownership_rejects_wrong_account_or_missing_user():
    """Ownership gate: wrong/missing account must not pass verified-domain requirement."""
    db = FakeOwnershipDB(None)
    with pytest.raises(HTTPException) as exc:
        await require_ownership(db, None, "example.com")
    assert exc.value.status_code == 403
    assert exc.value.detail["reason"] == "ownership_required"
