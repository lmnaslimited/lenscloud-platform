# Platform Metadata Admin Incidents Follow-Up

Date: 2026-07-07

This prompt resumes the Platform-side fixes for metadata-driven administration incidents.

## Incidents

- `LC-E2E-20260707-004`: Platform Settings must use the shared metadata-driven detail/editor path for singleton doctypes instead of a hard-coded field layout.
- `LC-E2E-20260707-005`: Platform Privacy must be routable and maintainable like other ResourcePage-backed doctypes.
- `LC-E2E-20260707-006`: Database Server privacy/Profile naming must be aligned. The stored policy link is a `Privacy Profile`; if the compatibility fieldname remains `privacy`, the label/help text must say `Privacy Profile`.
- `LC-E2E-20260707-007`: DocType `fetch_from` must be honored generically in the SPA/backend metadata layer. Database Server `cluster` should populate from selected `region.cluster` without a hard-coded Database Server rule.

## Required Reading

Start with:

1. `AGENTS.md`
2. `README.md`
3. `requirements.md`
4. `docs/handoffs/platform/agent-handoff.md`
5. `docs/platform-workitems.md`
6. `docs/incidents/e2e-incident-tracker.md`
7. `docs/operator-sop/platform-customer-e2e-acceptance.md`

For implementation context, inspect:

- `frontend/src/pages/ResourcePage.vue`
- `frontend/src/pages/PlatformSettingsPage.vue`
- `frontend/src/lib/catalog.js`
- `frontend/src/router.js`
- `lenscloud/api/launch.py`
- `lenscloud/lenscloud/doctype/platform_settings/platform_settings.json`
- `lenscloud/lenscloud/doctype/database_server/database_server.json`
- `lenscloud/lenscloud/doctype/privacy/privacy.json`
- `lenscloud/lenscloud/doctype/privacy_profile/privacy_profile.json`

## Implementation Rules

- Do not introduce one-off Database Server behavior for `fetch_from`; implement metadata behavior that works for any DocField with `fetch_from`.
- Do not delete the compatibility Database Server field unless a migration and all references are intentionally updated.
- Respect Frappe permissions and DocType metadata.
- Do not expose secrets or credentials.
- Keep Platform Settings as a singleton; only its presentation/editor path should become metadata-driven.

## Verification

Run focused checks before closing incidents:

1. Platform Settings opens through the Platform console and renders DocType tabs/sections/columns from metadata.
2. Platform Settings saves through standard document APIs.
3. Privacy appears in the Platform sidebar/router and supports list/create/edit for authorized Platform users.
4. Database Server create/edit shows `Privacy Profile` copy for the policy selector.
5. Selecting Region in Database Server creation auto-populates the read-only Cluster from `region.cluster`.
6. Existing ResourcePage metadata tests pass.
7. Frontend build passes.

Only after successful verification, move `LC-E2E-20260707-004` through `LC-E2E-20260707-007` from Active to Closed in `docs/incidents/e2e-incident-tracker.md` with evidence.

## Follow-Up Drift Found During User Retest

`LC-E2E-20260707-008` corrected two issues after the initial metadata pass:

- `get_document_connections` must remain whitelisted because ResourcePage detail rendering calls it for related-document summaries.
- Bench and Database Server runtime `privacy` fields must link to first-class `Privacy`, not `Privacy Profile`. Privacy Profiles belong to Plan/Subscription policy resolution and snapshots; runtime placement compares family values (`Public`, `Private Shared`, `Private`).
