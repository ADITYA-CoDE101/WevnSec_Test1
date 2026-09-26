# Legacy public-table retirement assessment — 2026-09-24

## Decision: do not remove
The public schema is not unused. Removing or renaming these tables now would break Supabase authentication triggers and existing RPCs. No destructive migration has been created or applied.

## Verified dependencies
- `auth.users` AFTER INSERT invokes `private.handle_new_user()`, which inserts/updates `public.users` and allocates usernames using it.
- `auth.users` AFTER UPDATE invokes `private.sync_auth_user()`, which updates `public.users`.
- `public.request_scan`, domain-verification RPCs, username RPC, and soft-delete RPC reference the legacy tables.
- `public.scans` triggers `private.sync_scan_history()`, referencing public domains, findings and scan_history.
- Active cron job 1 (`15 * * * *`) invokes `private.purge_expired_scan_reports()` against public scans/scan_history.
- Foreign keys link findings→scans/engagements, engagements→domains, domains→users, scans→domains, history→users/domains, audit_log→users.
- Existing rows: 7 users, 11 domains, 7 scans, 41 findings, 12 history; engagements/audit_log/contact_messages are empty but not demonstrated unused.
- New schema has no matching domain/scan IDs with public records; data migration equivalence is NOT established.

## Safe next steps requiring explicit approval
1. Identify/retire external callers, Edge Functions and old frontend/RPC clients; database inspection cannot prove their inactivity.
2. Approve retention policy and export a verified database backup (including triggers, policies, functions and data).
3. Map legacy users/domains/scans/findings/history to the current models. Verification status and historical report semantics need explicit mapping, not blind ID copying.
4. In a reviewed migration, replace auth trigger functions to remove legacy references, retire RPCs and disable the legacy cron job, then validate signup/login and retained historical data.
5. Archive approved tables in a separate non-exposed schema with restoration instructions. Verify for an agreed retention interval.
6. Only then apply a separately approved DROP migration, explicitly listing objects; never blind CASCADE.

Reproduce the read-only inventory with `python backend/scripts/legacy_inventory.py`; evidence is in `legacy_inventory.json`. Existing public data was preserved while the additive `wevnsec` monitoring migration advanced to `c8d2e4f6a901`.