# WevnSec — Domain Verification

## Original problem statement

## Domain Verification Feature — WevnSec
Complete the pending domain verification flow so website owners can prove ownership before running advanced security scans.

### Type
Web App (React frontend + FastAPI backend + Supabase DB, existing stack retained)

### Target Users
Website owners who need to unlock advanced security scans on domains they own.

### Verification Methods (all four supported)
1. DNS TXT record — `wevnsec-verify=<token>` on the apex
2. CNAME record — `_wevnsec.<domain>` → `verify.wevnsec.com`
3. HTML file upload — `https://<domain>/.well-known/wevnsec-<token>.txt`
4. Meta tag — `<meta name="wevnsec-verification" content="<token>">` on root HTML

User picks any one method per domain. Token is unique per (user, domain) pair.

### Core Logic
- **One-time verification.** Once verified, domain stays verified; no background polling.
- **Manual re-verify button.** User can trigger re-verification if they changed DNS/hosting. On failure, status flips to `needs_reverification` but scans keep working until user re-runs.
- **Apex-only verification.** Subdomains (`*.example.com`) auto-inherit ownership from verified apex. Reject verification attempts on subdomains with a helpful message.
- **Single-owner enforcement.** Already handled by Supabase unique constraint — surface a clean 409 error on the API and a clear message in UI.
- **Token lifecycle.** Tokens generated on "Add domain", valid for 7 days if unverified. Expired unverified domains auto-purged nightly.

### Backend (FastAPI) — endpoints to finalize
- `POST /domains` — add domain, generate token, return all 4 method instructions
- `GET /domains/{id}` — status + instructions
- `POST /domains/{id}/verify` — attempts verification using selected method; returns success/failure with reason
- `POST /domains/{id}/reverify` — same handler, user-triggered re-check
- `DELETE /domains/{id}` — remove domain

### DNS + HTTP infra
- DNS lookups via **Cloudflare DNS-over-HTTPS** (`https://cloudflare-dns.com/dns-query`) — reliable, no local resolver quirks, avoids ISP caching.
- HTTP checks via `httpx` with 5s timeout, follow redirects max 3, User-Agent identifying WevnSec bot.
- Sanitize domain input (punycode, strip protocol/path, lowercase).

### Failure reasons surfaced to UI
- `dns_record_not_found`
- `dns_record_mismatch`
- `http_file_unreachable`
- `meta_tag_missing`
- `timeout`
- `domain_already_claimed`
- `invalid_domain`

### Frontend (React) — wire-up needed
- Bind existing UI to the four endpoints
- Tab switcher for the 4 methods with copy-to-clipboard for token/record values
- "Verify now" and "Re-verify" buttons with loading + specific error messages
- Status badges: `pending`, `verified`, `needs_reverification`, `failed`
- Toast on 409 (already claimed by another user)

### Implementation Phases
Phase 1: Audit existing backend code, list gaps against the endpoints above
Phase 2: Implement DNS-over-HTTPS resolver util + HTTP fetcher util with timeouts
Phase 3: Complete the 4 verification method handlers + `/verify` + `/reverify` endpoints
Phase 4: Nightly cleanup job for expired unverified domains
Phase 5: Wire React UI to endpoints, error states, copy-to-clipboard, status badges
Phase 6: Manual QA against a real domain (all 4 methods) + edge cases (409, timeout, invalid input)

### Assumptions
- Supabase already has `domains` table with unique constraint on domain — retained
- Existing backend has partial verification logic; will refactor rather than rewrite
- No SSL/custom domain routing needed — verification only unlocks scans

### Open Questions
- Do you want an admin override to release a claimed domain (e.g., for support cases)?
- Should we email the user when their domain flips to `needs_reverification` after a manual recheck fails?

## Confirmed user decisions
- No admin override or failed-recheck emails in this update.
- Implement and test edge cases now; controlled-domain live success QA deferred until a domain is available.
- Retain supplied WevnSec app and Supabase rather than substituting the workspace MongoDB template.
- Authoritative source ZIP: `a7omq8so_wevnsec1.zip`, selected by user as “this is the one”. Credentials imported from its backend `.env`, kept server-side and excluded from version control.
- Supabase inspection found only `(user_id, domain)` uniqueness and two unverified `lenklyst.com` claims. User approved keeping September 24 and deleting only the September 25 duplicate; all reports/alerts retained.
- Three separate flows: Instant Scan for any domain (basic/normal), Verified Scan for owner-only advanced scans, and the original manual pentest request.

## Personas and static requirements
- Website owner: add an apex, configure any one of four proof methods, verify, use advanced scans on apex/subdomains, recheck manually after hosting/DNS changes.
- Visitor: continue public Instant Scan without claiming ownership.
- Pentest customer: retain the existing manual pentest contact/request path, not a new backend workflow.
- Claims must be isolated per authenticated user and globally unique by normalized domain. Failed rechecks must never silently revoke an earlier successful authorization.

## Architecture decisions
- React existing dashboard and Shadcn components retained; Geist/cyan light/dark design preserved, no redesign or replacement landing page.
- FastAPI `/api` prefix, existing Supabase Auth/app JWT dependencies and async SQLAlchemy PostgreSQL sessions retained. No new auth provider or MongoDB app persistence.
- Focused modules: `domain_validation`, `verification_dns`, `verification_http`, `domain_verification`, `domain_routes`, `ownership`, `domain_cleanup`.
- PSL-based apex handling with IDNA normalization; constant token generated using `secrets.token_urlsafe(32)`.
- `verified` is durable scan entitlement; `verification_status` is latest proof result. Original success time and last-attempt time are separate.
- Public Instant Scan retains ordinary TLS/headers/transport/cookie/CORS checks. Advanced sensitive-path checks and existing scheduled advanced scans require an owned, previously verified apex. Deep subdomains inherit this entitlement.
- HTTPS verification validates TLS, pins public DoH-resolved IPs, preserves Host/SNI, limits body to 1 MB and total attempt to 5 seconds. At most three redirects, only same apex or its www host over HTTPS.
- Versioned migration `e0f4a6b8c013`: new verification fields, global domain uniqueness, guarded RLS/table write permissions, expiry index and cron idempotency ledger. Legacy pending claims get a fresh seven-day window.
- Platform nightly cron at 02:00 UTC with constant-time Bearer secret validation, immediate 202 acknowledgement, persistent run-ID deduplication and background deletion of expired never-verified rows only. No verification polling added.
- Exact public/proxy origins configured in env to accommodate preview Origin rewriting without permitting wildcard browser writes.

## Implemented — 2026-09-26
- Retrieved and restored the selected source ZIP; retained existing routes/UI/auth and real Supabase storage.
- Audited incomplete code and captured gaps in `docs/DOMAIN_VERIFICATION_AUDIT.md`.
- Fixed UUID/AsyncSession/user-dictionary errors, removed client-controlled token generation and blocking/substring proof checks.
- Implemented create/list/detail/verify/reverify/delete, all four methods, stable seven-day tokens, useful structured failure reasons, expired-token 410, duplicate-claim 409 and user-scoped access checks.
- Enforced single ownership after explicitly approved duplicate cleanup. Migration applied and Alembic head confirmed.
- Implemented manual proof state lifecycle, durable advanced authorization and inherited subdomain access; basic public scans and manual pentest CTA remain separate.
- Wired dashboard add/verify/reverify, method tabs, copy controls, downloadable text proof, loading/error/expired states and all four badges. Added advanced scan gating to domain actions/monitoring.
- Added nightly cleanup manifest and authenticated endpoint; tested real queue acknowledgement, persisted completed outcomes, idempotency and retention rules.
- Fixed browser origin mismatch found in preview and responsive navbar layout found during testing.
- Added secret-safe test credential references and `.env` ignore rules. Replaced supplied development JWT signing secret with a strong generated value on initial import.
- Final frontend production build passed.
- Added the missing ESLint 9 flat configuration for the supplied project; preserved the cmdk component's supported custom attribute and made the changelog's literal comment-style label explicit JSX text.

## Verification evidence — 2026-09-26
- Testing agent iteration 1: 23/23 backend cases passed; found mobile/tablet navbar layout concern and missing credential-reference notes; both addressed.
- Testing agent iteration 2: 39/39 targeted checks passed and no remaining reported backend/frontend defects. These counts overlap and must not be added together.
- Coverage includes real external authentication/API/database/cron, strict input/409/IDOR/expiry, file/meta/TXT/CNAME logic, HTTP transport IP pinning/SNI/redirect/address/body/timeout guards, ownership inheritance/spoof rejection, one-time verification, failed recheck and recovery, and responsive navigation at 320/390/768/1024 pixels.
- Browser screenshot checks: sign-in, add domain, all four proof tabs; testing agent also checked copy/download/error status and retained pentest CTA. Disposable test rows/users cleaned up.
- Production integrations are real. Deterministic success/error network fixtures are used only in isolated automated tests. No production bypass or fake verified seed data.
- Reports: `test_reports/iteration_1.json`, `test_reports/iteration_2.json`; pytest results in `test_reports/pytest/`.

## Remaining / prioritized backlog
### P0
- No known blocking defect in the tested verification flow.
- Operational credential hygiene: user should rotate database/service-role credentials and supplied account passwords exposed in chat/archive. Secrets are not reproduced in this document.

### P1
- Complete successful live DNS TXT, CNAME, file and meta checks using a domain whose DNS/hosting the user controls. Deferred by user choice, not claimed as completed.
- Consider a token-specific CNAME target: the requested shared `verify.wevnsec.com` target cannot prove a fresh per-user challenge. A stale record after claim deletion can satisfy a different user's new claim. Current contract is implemented and limitation documented.

### P2 (requires user direction)
- Admin release/transfer workflow with audit trail.
- Notifications after manual recheck failure.
- Optional verified-subdomain scan picker in the dashboard.
- Review original scan engine and existing monitoring/email system independently if requested; not a security audit or email integration replacement in this task.

## Next tasks
1. Owner supplies a controlled domain and publishes proof records/files for live end-to-end acceptance.
2. Decide whether to strengthen the CNAME contract to use a token-bound target.
3. Revisit optional support/email enhancements only after user feedback.

Implementation/API/runbook: `docs/DOMAIN_VERIFICATION.md`.

---

## Follow-up: stable live scan panel, honest counters, editable documentation

### Original follow-up request (visual edits)
**Terminal, div line 69:** "this just a , plan showcase and its shorting and streching making the rest of the content up and down, add something meaningful here, something good visually"

**TrustBar, div line 72:** "these numerical values are misleading , we are just getting started so , just put the real numbers , and make it dinamisclly change as user do scan , this will give lots of number in runtime , add number of vulnravilties we are  addressing,  we wiil also add the documentation page which wiill contain all the explanation of almost  all the weakness and vulnerability and there mitigation for users to have references on vulnerability found on the scans and this documentaion numbers will be significant , you can add the doc page too. if there anythiing you want to add more you can do it ."

### Confirmed follow-up choices
- Fixed-size scan preview, explicitly labeled example while idle; actual activity/findings during a real scan without surrounding layout movement.
- Real completed scan totals and recorded findings, with repeated observations accurately labeled.
- Documentation for current scanner checks AND broader vulnerability education, clearly distinguished from automated detection.
- Additional requirement: "make it so that an admin can add/edit/remove any documentation or explanation on the docs".

### Architecture additions
- Keep existing React design, FastAPI, Supabase/PostgreSQL and authentication.
- Request-scoped `POST /api/scan/stream` NDJSON stream: actual start and check-return events, complete event only after the real report is persisted. Existing nonstreaming scan API retained. Advanced stream uses existing ownership gate; disconnected requests cancel their task. No fabricated progress percentages.
- Console dimensions are stable per breakpoint (520px desktop, 540px mobile); only the inner results scroll. Removed auto-cycling typing/tilt/showcase behavior.
- `/api/stats` uses one database snapshot: saved assessments, fail+warn observations (repeat findings included), separate fail/warn aliases, published articles, and check-type count from the implemented catalog. No invented baselines, random increments, fictitious researchers or trust-logo claims.
- Frontend revalidates stats after scan completion, on focus, and every 15 seconds while visible; failures display unavailable/stale states rather than invented values.
- Implemented check catalog contains 14 diagnostic output IDs. This does not imply that every scan executes all 14 or that these are 14 confirmed vulnerabilities.
- `wevnsec.documentation` stores structured plain-text articles, slug, category, reference severity, automated/educational coverage, supported check IDs, publication state, timestamps and optimistic version.
- Migration `f1a5b7c9d014` creates/seeds docs once, with RLS and direct browser-write restrictions. Profile-role writes are restricted so users cannot self-promote through Supabase table access.
- Public `GET /api/docs`, `/api/docs/catalog`, `/api/docs/{slug}` expose only published content. Admin GET/POST/PUT/DELETE under `/api/admin/docs`, authorized by server-loaded profile role. Duplicate slug and stale-version conflicts use 409; reserved slugs and inconsistent coverage are rejected.
- Documentation routes: `/docs`, `/docs/:slug`, `/docs/manage`, `/docs/manage/new`, `/docs/manage/:id`. Each significant view has its own route. Report checks link to their currently published guidance.

### Implemented — 2026-09-26 follow-up
- Replaced changing-height terminal with fixed-size scan activity view, truthful idle example, live returned checks, filter tabs, actual duration and full-report link; real scan stays on the landing page until the user opens its report.
- Replaced fabricated TrustBar values and randomized increases with live database aggregates, explicit repeat-counting definitions, retry control and update timestamp.
- Removed invented trust-logo strip, unused fake initial stats, and unsupported automated capability claims in the affected hero/marquee/check-summary content.
- Added 22 substantive published reference articles: 14 covering implemented scanner diagnostics and 8 educational-only topics. Explanations, impact, remediation, validation and known detector limitations are included. Educational topics explicitly say they are not automatically detected.
- Added searchable/filterable responsive documentation library, individual reference pages, related report links, actual Docs navigation/footer/preview links, and an admin entry point.
- Added admin draft/create/edit/publish/unpublish/delete UI; supported-check picker; all article fields editable; validation/errors, duplicate slug conflict, optimistic version protection, save/loading and delete confirmation states.
- Existing Instant/Verified scan separation, domain verification, monitoring, and manual pentest request preserved.
- Migration applied; frontend lint passed with one pre-existing unused constant warning; production build passed.

### Follow-up verification evidence
- Main screenshot verified a real Instant Scan and the console retaining exactly 520px height across idle/filter/complete states; docs search/filter/detail loaded.
- Testing agent iteration 3: 14/14 backend regression tests passed for actual streamed reports, stats parity/increments, admin CRUD/validation and permissions. Public UI and reported layout bug verified at desktop/tablet and 320/390px mobile with stable heights/no overflow. Full report links and related docs passed.
- Testing agent iteration 4: full ADMIN BROWSER CRUD passed using a legitimate disposable Supabase account, provisioned admin only for that exact test UUID. Normal UI sign-in and `/auth/me` role confirmed. Draft privacy/counts, publishing, coverage picker, edits/version persistence, unpublish/republish, duplicate URL error, delete cancel/confirm and final public 404/count restoration verified. Disposable data/account cleaned up.
- Production APIs/integrations are real. Idle example records are clearly illustrative and never contribute to statistics. No customer accounts or original article rows were modified by admin tests.
- Evidence: `/app/test_reports/iteration_3.json`, `/app/test_reports/iteration_4.json`, `/app/test_reports/pytest/pytest_results_iteration_3.xml`; regression suite `backend/tests/test_docs_stats_stream_regression.py`.

### Follow-up remaining work and next actions
- No known outstanding application defects in the tested new flows.
- **Access note:** the supplied `.env` admin password does not match the pre-existing Supabase admin account. The existing account/password was deliberately NOT reset. Use the account's current password; an authorized password reset/sync requires user approval. This is separate from the successfully tested admin functionality.
- P1 optional: article revision history/restore to supplement optimistic version conflict checks.
- P2 optional: editorial review workflow, article tags, and richer formatting if requested.
- Original controlled-domain live verification QA and token-bound CNAME enhancement remain deferred as documented above.