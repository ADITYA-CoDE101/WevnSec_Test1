"""Cloudflare DNS-over-HTTPS; never use a local recursive resolver for proof."""
import os
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import httpx

from domain_validation import VerificationError

RECORD_TYPES = {'A': 1, 'CNAME': 5, 'TXT': 16, 'AAAA': 28}


async def lookup(name: str, record_type: str, *, exact_owner=True) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=float(os.environ['VERIFICATION_TIMEOUT_SECONDS']), trust_env=False) as client:
            response = await client.get(os.environ['VERIFICATION_DOH_URL'],
                params={'name': name, 'type': record_type},
                headers={'Accept': 'application/dns-json', 'User-Agent': os.environ['VERIFICATION_USER_AGENT']})
            response.raise_for_status()
            body = response.json()
        if not isinstance(body, dict) or not isinstance(body.get('Answer', []), list):
            raise ValueError('Invalid DNS response')
        if body.get('Status') == 3:
            return []
        if body.get('Status') != 0 or body.get('TC'):
            raise VerificationError('dns_record_not_found', 'DNS could not be resolved reliably. Check the records and try again.')
        return [r['data'] for r in body.get('Answer', [])
                if isinstance(r, dict) and r.get('type') == RECORD_TYPES[record_type] and isinstance(r.get('data'), str)
                and (not exact_owner or r.get('name', '').rstrip('.').lower() == name.rstrip('.').lower())]
    except httpx.TimeoutException:
        raise VerificationError('timeout', 'The DNS lookup timed out. Please try again.')
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        raise VerificationError('dns_record_not_found', 'DNS is temporarily unavailable. Please try again.')


def txt_value(value: str) -> str:
    """TXT RDATA can contain multiple quoted chunks; compare the complete value."""
    try:
        record = dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, value)
        return b''.join(record.strings).decode('utf-8')
    except Exception:
        return ''


async def verify_dns(host, token, method):
    name = host if method == 'dns_txt' else f'_wevnsec.{host}'
    records = await lookup(name, 'TXT' if method == 'dns_txt' else 'CNAME')
    if not records:
        raise VerificationError('dns_record_not_found', f'No {"TXT" if method == "dns_txt" else "CNAME"} record was found at {name}. DNS changes may need time to propagate.')
    expected = f'wevnsec-verify={token}' if method == 'dns_txt' else os.environ['VERIFICATION_CNAME_TARGET'].lower().rstrip('.')
    values = [txt_value(r) if method == 'dns_txt' else r.lower().rstrip('.') for r in records]
    if expected not in values:
        raise VerificationError('dns_record_mismatch', 'A DNS record exists, but its value does not match. Copy the exact value below.')