"""Public-suffix-aware domain handling shared by verification and scan access."""
from urllib.parse import urlsplit

import idna
import tldextract

# A bundled PSL avoids a runtime download and handles co.uk and private suffixes.
PSL = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=True)


class VerificationError(Exception):
    def __init__(self, reason, message):
        self.reason, self.message = reason, message
        super().__init__(message)


def normalize_domain(value: str, *, apex_only=False) -> str:
    try:
        value = value.strip()
        if not value or any(c.isspace() for c in value) or '*' in value:
            raise ValueError()
        url = urlsplit(value if '://' in value else 'https://' + value)
        if url.scheme.lower() not in ('https', 'http') or url.username or url.password:
            raise ValueError()
        if url.port not in (None, 80, 443) or not url.hostname:
            raise ValueError()
        host = idna.encode(url.hostname.rstrip('.'), uts46=True, std3_rules=True).decode().lower()
        parts = PSL(host)
        if len(host) > 253 or not parts.domain or not parts.suffix:
            raise ValueError()
    except (ValueError, idna.IDNAError, UnicodeError):
        raise VerificationError('invalid_domain', 'Enter a valid public domain, such as example.com.')
    if apex_only and parts.subdomain:
        raise VerificationError('invalid_domain', f'Verify the apex domain {parts.top_domain_under_public_suffix} instead. Its subdomains automatically inherit ownership.')
    return host


def apex_domain(host: str) -> str:
    return PSL(normalize_domain(host)).top_domain_under_public_suffix