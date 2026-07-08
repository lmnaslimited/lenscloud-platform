# Platform Document Actions Evidence

Date: 2026-07-08  
Incident: `LC-E2E-20260707-009`

## Result

Fixed and retested.

## Changes Verified

- Shared Platform ResourcePage consumes native Frappe DocPerm metadata for document lifecycle actions:
  - `can_submit`;
  - `can_cancel`;
  - `can_amend`;
  - `can_delete`.
- Submittable documents such as Plan can expose Submit, Cancel, and Amend from the main document editor action surface.
- Generic delete is available only when native delete permission allows it, hidden for singleton doctypes, and blocked for submitted documents.
- Singleton doctypes such as Platform Settings open directly as the detail editor, without list view, row count, Refresh, or New actions.

## Validation

- `npm run build` passed.
- `bench --site dev.localhost run-tests --module lenscloud.api.test_policy` passed: 15 tests.
- Schema probe confirmed Plan returns `is_submittable=true` and `can_submit/can_cancel/can_amend/can_delete=true` for the current Platform user.

## Notes

Full Playwright was intentionally skipped for this narrow metadata/admin fix. The frontend compile and backend schema tests cover the changed contract; operator can verify visually by opening Platform Settings and Platform Plans.
