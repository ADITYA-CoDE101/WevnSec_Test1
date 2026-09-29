"""Import supplied server settings without overwriting workspace configuration."""
import secrets
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from dotenv import dotenv_values, set_key

source = dotenv_values(sys.argv[1], interpolate=False)
target = Path('/app/backend/.env')
existing = dotenv_values(target)
preview = dotenv_values('/app/frontend/.env')['REACT_APP_BACKEND_URL']
source['APP_URL'] = preview
source['WEVNSEC_APP_URL'] = preview
# The supplied local development signing key must not protect a public preview.
source['JWT_SECRET'] = secrets.token_urlsafe(48)
source['WEBHOOK_CRON_SECRET'] = secrets.token_urlsafe(48)
source['VERIFICATION_DOH_URL'] = 'https://cloudflare-dns.com/dns-query'
source['VERIFICATION_CNAME_TARGET'] = 'verify.wevnsec.com'
source['VERIFICATION_USER_AGENT'] = 'WevnSec-Verification/1.0'
source['VERIFICATION_TIMEOUT_SECONDS'] = '5'
source['VERIFICATION_MAX_REDIRECTS'] = '3'
url = urlsplit(source['DATABASE_URL'])
if url.port != 6543 or not (url.hostname or '').endswith('.pooler.supabase.com'):
    raise SystemExit('A Supabase transaction pooler connection is required.')
authority = f'{url.username}:{quote(unquote(url.password), safe="")}@{url.hostname}:{url.port}'
source['DATABASE_URL'] = urlunsplit((url.scheme, authority, url.path, url.query, url.fragment))
for key, value in source.items():
    if key not in existing and value is not None:
        set_key(target, key, value, quote_mode='always')
target.chmod(0o600)
print('Imported missing server settings; existing workspace settings preserved.')