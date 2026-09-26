"""Fixed, first-party transactional templates; no caller-supplied recipient or HTML."""
import os
import re
import ipaddress
import httpx
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ["EMERGENT_EMAIL_KEY"]
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")
APP_URL = os.environ["APP_URL"].rstrip('/')

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv",
             "send us your password", "enter your password below", "confirm your card number",
             "your full card number", "seed phrase", "recovery phrase", "verify your card",
             "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    """Reject empty, punycode, IP-literal, and shortener hosts."""
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan(); scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} != real link host {real!r} (G3)")


def grade_drop_template(alert):
    subject = f"{EMAIL_FROM_NAME}: grade dropped for {alert.domain}"
    link = f"{APP_URL}/report/{alert.scan_share_id}"
    html = f'''<table role="presentation" width="100%" style="background:#f4f6f8;padding:32px"><tr><td>
    <table role="presentation" width="100%" style="max-width:600px;margin:auto;background:#fff;padding:32px;font-family:Arial,sans-serif;color:#16202a"><tr><td>
    <p style="font-size:22px;font-weight:bold">{escape(EMAIL_FROM_NAME)}</p>
    <p style="color:#b42318;font-size:12px">SECURITY GRADE DROP</p>
    <h1 style="font-size:24px">{escape(alert.domain)}</h1>
    <p>Your watched domain changed from <strong>{escape(alert.previous_grade)}</strong> ({alert.previous_score}/100)
    to <strong>{escape(alert.current_grade)}</strong> ({alert.current_score}/100).</p>
    <p>A new automated scan found a lower security grade. Review the findings and recommended fixes.</p>
    <p><a href="{escape(link, quote=True)}" style="color:#0284c7">View scan report</a></p>
    <p style="font-size:12px;color:#596675">Sent by {escape(EMAIL_FROM_NAME)} for a domain you watch.
    Email preferences are available in your <a href="{escape(APP_URL, quote=True)}/dashboard/domains">watched domains</a>.
    We never ask for your password or payment details by email.</p>
    </td></tr></table></td></tr></table>'''
    return subject, html


async def send_email(*, to: str, subject: str, html: str) -> str:
    _assert_safe_email(subject, html)
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if EMAIL_REPLY_TO:
        payload["contact_email"] = EMAIL_REPLY_TO
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{EMAIL_BASE_URL}/api/v1/email/send", headers={"X-Email-Key": EMAIL_KEY}, json=payload)
    response.raise_for_status()
    provider_id = response.json().get('id')
    if not provider_id:
        raise ValueError('Email provider returned no message ID')
    return provider_id