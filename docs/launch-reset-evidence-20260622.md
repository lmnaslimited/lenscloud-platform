# Launch Reset Evidence - 2026-06-22

## Scope

Implementation baseline for configurable topology, launch dashboard, grouped navigation, customer Free onboarding, and the controlled tenant/runtime reset.

## Completed Evidence

- Platform base revision: `0b14078` plus the current uncommitted implementation.
- Migration: passed on `dev.localhost`.
- Backend suite: 32 tests passed.
- Frontend production build: passed.
- Seeded Environment, Site Control Profile, Single through Four Tier Landscape, Public/Private Shared/Private profile, Free Plan mapping, and LensCloud Platform Workspace Sidebar records.
- Added authoritative dashboard aggregates and launch gates.
- Added immutable Subscription policy snapshots, independent Bench/Database placement keys, beta approval, and test-gate records.
- Added guided Free Site and beta enrollment UI behavior.
- Authenticated metadata-editor Playwright passed for DocType sections, compact fixed child columns, horizontal scrolling, child persistence, and Release Group Included Apps Table MultiSelect value help/discard.
- No credential or Secret value is recorded here.

- Authenticated Platform Customer and Site lists render nonzero records; the missing icon import and Platform role permissions were corrected.

## Pending Live Evidence

- Exact pre-cleanup Platform and runtime inventory.
- Normal Site, Bench, and managed Database Server lifecycle cleanup.
- Matched Infra handoff for any orphaned or unlabelled resource.
- Post-reset direct counts.
- Exactly one Ready Free Bench per launch Plan/Region.
- Fresh customer signup, HTTPS, and static-asset proof.
- Sequential Single, Two, Three, and Four Tier live acceptance.
- Authenticated customer and Platform desktop/mobile Playwright.
- Final apply-disabled and protected-resource proof.

No cleanup is claimed by this document until these items are appended with action-log references and exact resource outcomes.

## Known Gap

The current Frappe Operator CRD does not expose the full Site Control Profile contract. Platform stores and validates those policies but does not invent unsupported runtime fields. Operator-side typed configuration support remains required before these controls can be enforced on live Sites.

## Metadata Framework Acceptance - 2026-06-23

- Plan Allowed Privacy Profiles rendered as a compact Table MultiSelect with value help, not a regular child grid.
- Customer editing and Subscription creation were verified as LensCloud Platform User.
- Related-document summaries were sourced from DocType Links, limited to the latest five previews, and exposed authoritative counts.
- Clicking a related count opened the target list with the source link-field filter; no catalog relation definitions remain.
- Production build passed; focused metadata Playwright, generic metadata-editor Playwright, and Platform desktop/mobile Playwright passed.
- Backend policy suite passed 9/9, including metadata type, permission, connection-count, and link-integrity assertions.
- Customer browser acceptance remained skipped because the supplied credential file contained Platform credentials only.
