"""Isolated verification transport controls (HTTP fetcher + DoH lookup) without real network."""

import sys

import httpx
import pytest

sys.path.insert(0, "/app/backend")

from domain_validation import VerificationError
from verification_dns import lookup
from verification_http import MAX_BODY, fetch_html, public_address


ORIGINAL_ASYNC_CLIENT = httpx.AsyncClient


def _patch_async_client(monkeypatch, module, handler):
    transport = httpx.MockTransport(handler)

    class PatchedAsyncClient(ORIGINAL_ASYNC_CLIENT):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(module.httpx, "AsyncClient", PatchedAsyncClient)


@pytest.mark.anyio
async def test_fetch_html_valid_200_decodes_text_and_uses_ip_pinning_with_host_sni(monkeypatch):
    """Fetcher: keep Host/SNI for TLS while connecting to vetted pinned IP."""
    async def pinned(_host):
        return "93.184.216.34"

    monkeypatch.setattr("verification_http.public_address", pinned)

    def handler(request: httpx.Request):
        assert request.url.host == "93.184.216.34"
        assert request.headers["Host"] == "qa-v26-unit-example.com"
        assert request.extensions.get("sni_hostname") == "qa-v26-unit-example.com"
        return httpx.Response(200, headers={"Content-Type": "text/plain; charset=utf-8"}, content="token-✓".encode("utf-8"))

    import verification_http

    _patch_async_client(monkeypatch, verification_http, handler)
    body = await fetch_html("qa-v26-unit-example.com", "/.well-known/wevnsec.txt")
    assert body == "token-✓"


@pytest.mark.anyio
async def test_fetch_html_redirects_up_to_three_hops_allowed(monkeypatch):
    """Fetcher: redirects 0..3 are accepted when staying on HTTPS and allowed hostnames."""
    calls = {"public_address": 0, "http": 0}

    async def pinned(_host):
        calls["public_address"] += 1
        return "93.184.216.34"

    monkeypatch.setattr("verification_http.public_address", pinned)

    def handler(request: httpx.Request):
        calls["http"] += 1
        path = request.url.path
        if path == "/start":
            return httpx.Response(302, headers={"location": "/one"})
        if path == "/one":
            return httpx.Response(302, headers={"location": "https://www.qa-v26-unit-example.com/two"})
        if path == "/two":
            return httpx.Response(302, headers={"location": "/ok"})
        return httpx.Response(200, content=b"ok")

    import verification_http

    _patch_async_client(monkeypatch, verification_http, handler)
    body = await fetch_html("qa-v26-unit-example.com", "/start")
    assert body == "ok"
    assert calls["http"] == 4
    assert calls["public_address"] == 4


@pytest.mark.anyio
async def test_fetch_html_fourth_redirect_rejected(monkeypatch):
    """Fetcher: fourth redirect must fail (max 3)."""
    async def pinned(_host):
        return "93.184.216.34"

    monkeypatch.setattr("verification_http.public_address", pinned)

    def handler(_request: httpx.Request):
        return httpx.Response(302, headers={"location": "/next"})

    import verification_http

    _patch_async_client(monkeypatch, verification_http, handler)
    with pytest.raises(VerificationError) as exc:
        await fetch_html("qa-v26-unit-example.com", "/start")
    assert exc.value.reason == "http_file_unreachable"
    assert "limit of three redirects" in exc.value.message


@pytest.mark.anyio
@pytest.mark.parametrize("location", ["http://qa-v26-unit-example.com/plain", "https://evil.example.net/x", "https://127.0.0.1/x"])
async def test_fetch_html_denies_unsafe_redirects_without_validating_target_network(monkeypatch, location):
    """Fetcher: deny scheme/cross-origin/private redirects before any target-network validation."""
    calls = {"public": 0}

    async def pinned(_host):
        calls["public"] += 1
        return "93.184.216.34"

    monkeypatch.setattr("verification_http.public_address", pinned)

    def handler(request: httpx.Request):
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": location})
        return httpx.Response(200, content=b"should-not-happen")

    import verification_http

    _patch_async_client(monkeypatch, verification_http, handler)
    with pytest.raises(VerificationError) as exc:
        await fetch_html("qa-v26-unit-example.com", "/start")
    assert exc.value.reason == "http_file_unreachable"
    assert calls["public"] == 1


@pytest.mark.anyio
async def test_fetch_html_oversize_status_unreachable_timeout_errors(monkeypatch):
    """Fetcher: map 1MB overflow, non-200, HTTP errors and timeout to structured reasons."""
    async def pinned(_host):
        return "93.184.216.34"

    monkeypatch.setattr("verification_http.public_address", pinned)

    # Oversize
    def oversize_handler(_request: httpx.Request):
        return httpx.Response(200, content=b"x" * (MAX_BODY + 1))

    import verification_http

    _patch_async_client(monkeypatch, verification_http, oversize_handler)
    with pytest.raises(VerificationError) as exc_oversize:
        await fetch_html("qa-v26-unit-example.com", "/big")
    assert exc_oversize.value.reason == "http_file_unreachable"
    assert "1 MB" in exc_oversize.value.message

    # HTTP status failure
    def status_handler(_request: httpx.Request):
        return httpx.Response(503, content=b"down")

    _patch_async_client(monkeypatch, verification_http, status_handler)
    with pytest.raises(VerificationError) as exc_status:
        await fetch_html("qa-v26-unit-example.com", "/down")
    assert exc_status.value.reason == "http_file_unreachable"
    assert "HTTP 503" in exc_status.value.message

    # Unreachable
    def unreachable_handler(request: httpx.Request):
        raise httpx.ConnectError("boom", request=request)

    _patch_async_client(monkeypatch, verification_http, unreachable_handler)
    with pytest.raises(VerificationError) as exc_unreachable:
        await fetch_html("qa-v26-unit-example.com", "/oops")
    assert exc_unreachable.value.reason == "http_file_unreachable"

    # Timeout
    def timeout_handler(request: httpx.Request):
        raise httpx.ReadTimeout("slow", request=request)

    _patch_async_client(monkeypatch, verification_http, timeout_handler)
    with pytest.raises(VerificationError) as exc_timeout:
        await fetch_html("qa-v26-unit-example.com", "/slow")
    assert exc_timeout.value.reason == "timeout"


@pytest.mark.anyio
async def test_public_address_blocks_private_mixed_and_private_ipv6(monkeypatch):
    """Address vetting: all resolved addresses must be globally routable."""

    async def all_public(name, record_type, **_kwargs):
        if record_type == "A":
            return ["93.184.216.34"]
        return ["2606:2800:220:1:248:1893:25c8:1946"]

    monkeypatch.setattr("verification_http.lookup", all_public)
    assert await public_address("qa-v26-unit-example.com") == "93.184.216.34"

    async def mixed_private(name, record_type, **_kwargs):
        return ["93.184.216.34", "10.0.0.5"] if record_type == "A" else []

    monkeypatch.setattr("verification_http.lookup", mixed_private)
    with pytest.raises(VerificationError) as exc_mixed:
        await public_address("qa-v26-unit-example.com")
    assert exc_mixed.value.reason == "http_file_unreachable"

    async def private_ipv6(name, record_type, **_kwargs):
        return [] if record_type == "A" else ["fd00::1"]

    monkeypatch.setattr("verification_http.lookup", private_ipv6)
    with pytest.raises(VerificationError) as exc_ipv6:
        await public_address("qa-v26-unit-example.com")
    assert exc_ipv6.value.reason == "http_file_unreachable"


@pytest.mark.anyio
async def test_dns_lookup_request_headers_types_owner_filter_and_malformed_shape(monkeypatch):
    """DoH utility: enforce endpoint params/headers, exact-owner filter, and structured malformed-response error."""
    calls = {"count": 0}

    def handler(request: httpx.Request):
        calls["count"] += 1
        assert str(request.url).startswith("https://cloudflare-dns.com/dns-query")
        assert request.url.params.get("name") == "qa-v26-unit-example.com"
        assert request.url.params.get("type") == "TXT"
        assert request.headers.get("accept") == "application/dns-json"
        assert request.headers.get("user-agent")

        if calls["count"] == 1:
            return httpx.Response(
                200,
                json={
                    "Status": 0,
                    "TC": False,
                    "Answer": [
                        {"name": "qa-v26-unit-example.com.", "type": 16, "data": '"wevnsec-verify=ok"'},
                        {"name": "other.example.com.", "type": 16, "data": '"wevnsec-verify=no"'},
                        {"name": "qa-v26-unit-example.com.", "type": 5, "data": "ignore-cname.example."},
                    ],
                },
            )
        if calls["count"] == 2:
            return httpx.Response(200, json={"Status": 3})
        return httpx.Response(200, json={"Answer": {"not": "a-list"}})

    import verification_dns

    _patch_async_client(monkeypatch, verification_dns, handler)

    exact = await lookup("qa-v26-unit-example.com", "TXT", exact_owner=True)
    assert exact == ['"wevnsec-verify=ok"']

    nxdomain = await lookup("qa-v26-unit-example.com", "TXT", exact_owner=True)
    assert nxdomain == []

    with pytest.raises(VerificationError) as exc_bad_shape:
        await lookup("qa-v26-unit-example.com", "TXT", exact_owner=True)
    assert exc_bad_shape.value.reason == "dns_record_not_found"
