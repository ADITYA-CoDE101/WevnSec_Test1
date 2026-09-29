"""Proof instructions and method dispatch; never accepts client-provided tokens."""
import asyncio
import os
from typing import Literal

from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field

from domain_validation import VerificationError, normalize_domain
from verification_dns import verify_dns
from verification_http import fetch_html

VerificationMethod = Literal['dns_txt', 'dns_cname', 'html_file', 'html_meta']


class DomainIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    domain: str = Field(min_length=1, max_length=2048)


class VerifyIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    method: VerificationMethod


def instructions(domain):
    host, token = domain.domain, domain.verification_token
    filename = f'wevnsec-{token}.txt'
    return {
        'dns_txt': {'type': 'TXT', 'name': '@', 'hostname': host, 'value': f'wevnsec-verify={token}'},
        'dns_cname': {'type': 'CNAME', 'name': '_wevnsec', 'hostname': f'_wevnsec.{host}', 'value': os.environ['VERIFICATION_CNAME_TARGET']},
        'html_file': {'filename': filename, 'path': f'/.well-known/{filename}', 'url': f'https://{host}/.well-known/{filename}', 'content': token},
        'html_meta': {'url': f'https://{host}/', 'tag': f'<meta name="wevnsec-verification" content="{token}">', 'content': token},
    }


def domain_view(d):
    iso = lambda value: value.isoformat() if value else None
    return {
        'id': d.id, 'domain': d.domain, 'verified': d.verified, 'status': d.verification_status,
        'verification_status': d.verification_status, 'verification_method': d.verification_method,
        'verification_token': d.verification_token, 'token_expires_at': iso(d.token_expires_at),
        'verified_at': iso(d.verified_at), 'last_verification_at': iso(d.last_verification_at),
        'last_verification_error': d.last_verification_error, 'advanced_scans_enabled': d.verified,
        'created_at': iso(d.created_at), 'instructions': instructions(d),
    }


async def check_proof(domain, method):
    normalize_domain(domain.domain, apex_only=True)
    try:
        async with asyncio.timeout(float(os.environ['VERIFICATION_TIMEOUT_SECONDS'])):
            if method in ('dns_txt', 'dns_cname'):
                await verify_dns(domain.domain, domain.verification_token, method)
            elif method == 'html_file':
                content = await fetch_html(domain.domain, instructions(domain)['html_file']['path'])
                if content.strip() != domain.verification_token:
                    raise VerificationError('http_file_unreachable', 'The file is reachable, but its contents must be exactly the verification token.')
            elif method == 'html_meta':
                content = await fetch_html(domain.domain, '/')
                soup = BeautifulSoup(content, 'html.parser')
                if not soup.head or not any(tag.get('name') == 'wevnsec-verification' and tag.get('content') == domain.verification_token for tag in soup.head.find_all('meta')):
                    raise VerificationError('meta_tag_missing', 'The exact verification meta tag was not found in the root page’s <head>.')
            else:
                raise VerificationError('invalid_method', 'Choose one of the four verification methods.')
    except TimeoutError:
        raise VerificationError('timeout', 'Verification timed out after five seconds. Please try again.')