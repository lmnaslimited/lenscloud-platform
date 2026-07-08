# Platform Metadata Admin Incident Evidence

Date: 2026-07-07

Incidents closed:

- `LC-E2E-20260707-004` Platform Settings metadata editor
- `LC-E2E-20260707-005` Privacy administration missing
- `LC-E2E-20260707-006` Database Server Privacy/Profile field drift
- `LC-E2E-20260707-007` Metadata fetch-from behavior

## Changes Verified

- Platform Settings now routes through the shared `ResourcePage` metadata editor as a singleton resource.
- Platform Privacy now has first-class SPA routes at `/lenscloud/platform/privacy` and `/lenscloud/platform/privacy/:name`.
- Database Server keeps the compatibility fieldname `privacy`, but the DocType and Platform UI label now say `Privacy Profile` because the field links to `Privacy Profile`.
- The metadata schema now includes DocField `fetch_from`, and the ResourcePage editor applies it generically through a permission-checked backend helper.
- Singleton resources no longer issue invalid self-list or related-connection background calls.

## Verification

- `bench --site dev.localhost migrate` passed after the Database Server DocType label update.
- `bench --site dev.localhost run-tests --module lenscloud.api.test_policy` passed 15 tests.
- `npm run build` passed from `frontend/`.
- Backend schema probe confirmed `Database Server.cluster` exposes `fetch_from: region.cluster`.
- Backend fetch helper returned `Region/EU.cluster = lenscloud-eu-dev`.
- Platform Settings schema probe returned the current DocType tabs/sections/columns, including `Central User Access OAuth`.
- Focused authenticated browser smoke passed:
  - Platform Privacy route loads and exposes `New Privacy`.
  - Platform Settings loads the shared center document editor and shows `Central User Access OAuth`.
  - Database Server create dialog shows `Privacy Profile *` and `Cluster`.
  - No unexpected 4xx/5xx responses on those focused surfaces after singleton fix.

## Notes

The broader `frontend/tests/metadata-framework-auth.mjs` was attempted but timed out in an older Customer-to-Site related-record assertion. That path is outside these four incidents and was not used as closure evidence for this fix.

## Follow-Up Correction: LC-E2E-20260707-008

User retest found detail rendering failed because `lenscloud.api.launch.get_document_connections` was no longer whitelisted. The fix restored the whitelist decorator.

The same retest exposed the strategic model mistake in `LC-E2E-20260707-006`: Database Server and Bench runtime records must store the resolved `Privacy` family, not a `Privacy Profile`. Runtime placement logic compares values such as `Public`, `Private Shared`, and `Private`; Plans and Subscriptions continue to use submitted Privacy Profiles for policy snapshots.

Verification:

- `bench --site dev.localhost migrate` passed.
- Existing Database Server and Bench records use `Public`; no data repair was required.
- `bench --site dev.localhost run-tests --module lenscloud.api.test_policy` passed 15 tests.
- `npm run build` passed.
- Database Server schema confirms `privacy.options = Privacy` and `cluster.fetch_from = region.cluster`.
- Bench schema confirms `privacy.options = Privacy`.
- Focused authenticated browser smoke opened Database Server and Bench detail pages with no LensCloud API 4xx/5xx failures; the prior whitelist error is gone.
