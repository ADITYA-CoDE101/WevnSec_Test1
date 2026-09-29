"""Bounded HTTPS proof fetches, with DoH-resolved IP pinning to prevent SSRF."""
import asyncio
import os
from ipaddress import ip_address
from urllib.parse import urljoin

import httpx

from domain_validation import VerificationError
from verification_dns import lookup

MAX_BODY = 1024 * 1024


async def public_address(host):
    results = await asyncio.gather(lookup(host, 'A', exact_owner=False), lookup(host, 'AAAA', exact_owner=False))
    addresses = [ip_address(value) for group in results for value in group]
    if not addresses or any(not ip.is_global or ip.is_multicast or ip.is_unspecified or getattr(ip, 'ipv4_mapped', None) for ip in addresses):
        raise VerificationError('http_file_unreachable', 'The domain must resolve only to public internet addresses.')
    # Prefer IPv4 for containers without IPv6 routing. Connection is pinned below.
    return str(sorted(addresses, key=lambda ip: ip.version)[0])


async def fetch_html(host: str, path: str) -> str:
    timeout = float(os.environ['VERIFICATION_TIMEOUT_SECONDS'])
    max_redirects = int(os.environ['VERIFICATION_MAX_REDIRECTS'])
    url = httpx.URL(f'https://{host}{path}')
    try:
        async with asyncio.timeout(timeout):
            for hop in range(max_redirects + 1):
                if url.scheme != 'https' or url.port not in (443, None) or url.userinfo or url.host not in (host, f'www.{host}'):
                    raise VerificationError('http_file_unreachable', 'Redirects must stay on HTTPS on this domain or its www hostname.')
                address = await public_address(url.host)
                # Preserve Host and TLS SNI while connecting to the exact vetted IP.
                pinned = url.copy_with(host=address)
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, max_redirects=max_redirects, verify=True, trust_env=False) as client:
                    async with client.stream('GET', pinned,
                        headers={'Host': url.host, 'User-Agent': os.environ['VERIFICATION_USER_AGENT'], 'Accept': 'text/html,text/plain'},
                        extensions={'sni_hostname': url.host}) as response:
                        if response.status_code in (301, 302, 303, 307, 308):
                            if hop == max_redirects or not response.headers.get('location'):
                                raise VerificationError('http_file_unreachable', 'The page exceeded the limit of three redirects.')
                            url = httpx.URL(urljoin(str(url), response.headers['location']))
                            continue
                        if response.status_code != 200:
                            raise VerificationError('http_file_unreachable', f'The verification URL returned HTTP {response.status_code}. It must be publicly accessible without signing in.')
                        content = bytearray()
                        async for chunk in response.aiter_bytes():
                            content.extend(chunk)
                            if len(content) > MAX_BODY:
                                raise VerificationError('http_file_unreachable', 'The verification response exceeds the 1 MB limit.')
                        return content.decode(response.encoding or 'utf-8', errors='replace')
    except (TimeoutError, httpx.TimeoutException):
        raise VerificationError('timeout', 'The website did not respond within five seconds. Please try again.')
    except VerificationError as exc:
        if exc.reason.startswith('dns_'):
            raise VerificationError('http_file_unreachable', 'The verification URL could not be resolved. Check your domain’s DNS records.')
        raise
    except (httpx.HTTPError, ValueError, UnicodeError):
        raise VerificationError('http_file_unreachable', 'The HTTPS verification URL could not be reached. Check hosting and the TLS certificate.')
    raise VerificationError('http_file_unreachable', 'The verification URL could not be reached.')