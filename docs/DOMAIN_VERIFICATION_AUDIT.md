# Domain verification audit

Source: the user-selected `wevnsec1.zip` (artifact a7omq8so). Existing React, FastAPI, SQLAlchemy, Supabase Auth and PostgreSQL retained.

## Gaps in the supplied project
- Add-domain swallowed all integrity errors and returned only the hostname; it generated no token or instructions.
- Verify expected an integer ID although domains use UUIDs; used synchronous `db.query`/`commit` on AsyncSession and `user.id` on a dictionary.
- Clients could supply their own verification token; TXT checked the wrong hostname with a blocking system resolver and substring matching.
- Meta verification used blocking HTTP and accepted a token anywhere in a page.
- No CNAME/file handlers, detail endpoint, re-verification endpoint, expiry, last-error persistence, or cleanup schedule.
- Model verification columns were missing from Alembic history.
- Supplied migrations constrain `(user_id, domain)`, not global ownership. Inspect live constraints before adding a global unique constraint; never silently delete duplicate claims.
- No public-suffix-aware apex validation, punycode normalization, scan authorization or subdomain inheritance.
- Existing dashboard has no verification instructions, method tabs, status badges, or verification actions.
- Existing domain RLS policy permits clients to write verification fields if table privileges are granted; restrict domain writes to the backend.

## Implementation decisions
- Stable cryptographically random token at add-domain; expires after seven days until first successful proof.
- `verified` means scans remain authorized after a successful proof; a failed manual recheck changes `verification_status` without clearing that authorization.
- Initial `/verify` is idempotent after first success. Only `/reverify` performs another network check.
- Cloudflare DoH for DNS; HTTPS-only, same-domain safe redirects, validated/pinned public IPs, valid TLS, bounded body size, five-second timeout.
- Preserve the requested fixed CNAME target. Unlike token-bearing proofs this record cannot distinguish accounts or prove a fresh challenge. Recommend TXT for stronger proof and document the limitation rather than silently changing the contract.
- Platform nightly cron deletes only expired, never-verified rows. It never polls verification.
- Keep public/basic scans; require ownership before advanced probes and for scheduled advanced scans.

## Deferred by user choice
Admin claim release and failed-recheck email notifications. Successful live tests of all methods await a user-controlled DNS/hosting domain.