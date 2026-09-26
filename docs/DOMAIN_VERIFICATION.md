# Domain ownership verification

## API contract
All routes are under `/api` and use the existing authenticated session/bearer token.

| Route | Behavior |
|---|---|
| `POST /domains` | `{ "domain": "https://Example.com/path" }`; returns 201, canonical apex, stable token, seven-day expiry and four instruction objects |
| `GET /domains` | Current user's domains, proof status, scan entitlement, monitoring information and latest scans |
| `GET /domains/{uuid}` | Current user's domain status and instructions |
| `POST /domains/{uuid}/verify` | `{ "method": "dns_txt" }`; first proof or idempotent response after first success |
| `POST /domains/{uuid}/reverify` | Same request; explicitly performs another check on previously verified domains |
| `DELETE /domains/{uuid}` | Releases the current user's claim, stops its monitoring; scan reports and alerts retained |

Methods: `dns_txt`, `dns_cname`, `html_file`, `html_meta`. Tokens cannot be supplied/changed by the client.

Proof failure is an HTTP 200 attempt result with `success: false`, `reason`, `message`, and updated domain status. Invalid input uses 400; unknown/other-user IDs 404; duplicate claims 409; expired never-verified token 410; invalid method/payload 422. Error details contain `reason` and a human-readable `message`.

`verified` / `advanced_scans_enabled` represents durable authorization. `verification_status` represents the latest manual proof state. A failed manual recheck changes the latter to `needs_reverification` without revoking the former. `verified_at` retains the first success; `last_verification_at` records the latest attempt. No background re-verification takes place.

## Proof formats
- TXT on the apex: exact `wevnsec-verify=<token>` (quoted DNS chunks reconstructed).
- CNAME: `_wevnsec.<apex>` → `verify.wevnsec.com` (DNS-only, no proxy).
- File: `https://<apex>/.well-known/wevnsec-<token>.txt`, body exactly the token (surrounding whitespace permitted).
- Meta: `<meta name="wevnsec-verification" content="<token>">` in the server-rendered root HTML's `<head>`.

HTTP validates certificates, pins connections to public DoH-resolved addresses, accepts up to three HTTPS redirects to the same apex or `www`, limits responses to 1 MB and the full attempt to five seconds. Cross-domain redirects are rejected. Private addresses are never fetched.

**CNAME limitation:** The fixed shared target is the explicitly requested contract, but it is not a user-specific challenge. A stale CNAME left after a claim is deleted can satisfy another account's new claim. Prefer token-bearing TXT/file/meta verification; a future token-specific CNAME target would close this gap but changes the requested contract.

## Three scan/request flows
- Instant Scan remains public (`POST /scan` without `advanced`, or with `advanced: false`) for ordinary non-invasive TLS, transport, headers, cookie and CORS checks.
- Verified Scan (`advanced: true`) requires a previously verified apex owned by the caller. Sensitive-path probes and scheduled advanced scans are gated. All subdomains inherit the verified apex's access, including while a manual recheck needs attention.
- The existing manual pentest contact/request CTA is unchanged. This update does not add a new pentest request backend.

## Storage and migrations
Supabase PostgreSQL / SQLAlchemy / Alembic and the original Supabase Auth + application JWT flow are retained. No MongoDB substitution.

Migration `e0f4a6b8c013` follows `d9e3f5a7b012`. It adds verification fields and a global domain unique constraint, restricts direct browser writes to domain ownership data, and adds the cron-delivery ledger. Legacy unverified rows receive fresh tokens with seven days from migration rather than being immediately purged. Existing reports are not modified.

The later unverified `lenklyst.com` claim dated 2026-09-25 was removed with explicit user approval, retaining the 2026-09-24 claim. All other original claims were retained. The migration refuses to proceed if unresolved duplicates exist.

## Runtime configuration
Keep server secrets in `backend/.env` (never browser variables): existing Supabase keys, transaction-pooler `DATABASE_URL`, and application auth settings. New settings:

- `VERIFICATION_DOH_URL`: Cloudflare DoH endpoint
- `VERIFICATION_CNAME_TARGET`: requested shared verification target
- `VERIFICATION_USER_AGENT`: identifying WevnSec verification bot
- `VERIFICATION_TIMEOUT_SECONDS`: `5`
- `VERIFICATION_MAX_REDIRECTS`: `3`
- `WEBHOOK_CRON_SECRET`: generated high-entropy scheduler credential
- `WEVNSEC_APP_URL`: application's public browser origin
- `WEVNSEC_TRUSTED_ORIGINS`: comma-separated exact proxy/browser origins (an empty value is valid if none are needed)

Use `alembic upgrade head` and `alembic current` after configuring the transaction pooler. Existing environment values for MongoDB and frontend backend URL have not been changed.

## Nightly cleanup
`.emergent/crons.yml` runs at 02:00 UTC. `POST /api/cron/domain-cleanup` authenticates in constant time, validates the envelope, records its idempotency key and acknowledges 202 before background deletion. It removes only expired rows that have never been verified. All previously verified claims—including `needs_reverification`—and all reports are preserved. Delivery outcomes are recorded in `wevnsec.cron_deliveries`.

## QA boundary
Automated API, database, state-machine, UI, DNS and HTTP fixture checks are included. Fixtures are isolated tests, not production behavior. Real successful verification for all four methods requires a user-controlled DNS/hosting domain and remains deferred by user choice.