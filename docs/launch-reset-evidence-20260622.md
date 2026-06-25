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

The current runtime does not expose the full Site Control Profile enforcement contract. Platform stores and validates those policies but does not invent unsupported FrappeSite CR fields. The preferred gap closure is an Infra/operator Bench Command Job/API that safely executes approved `bench --site` style operations such as backup, restore, maintenance mode, developer mode, site config, CORS, Bench Test, and LATP operations with sanitized evidence.

## Metadata Framework Acceptance - 2026-06-23

- Plan Allowed Privacy Profiles rendered as a compact Table MultiSelect with value help, not a regular child grid.
- Customer editing and Subscription creation were verified as LensCloud Platform User.
- Related-document summaries were sourced from DocType Links, limited to the latest five previews, and exposed authoritative counts.
- Clicking a related count opened the target list with the source link-field filter; no catalog relation definitions remain.
- Production build passed; focused metadata Playwright, generic metadata-editor Playwright, and Platform desktop/mobile Playwright passed.
- Backend policy suite passed 9/9, including metadata type, permission, connection-count, and link-integrity assertions.
- Customer browser acceptance remained skipped because the supplied credential file contained Platform credentials only.

## Submitted Policy/Profile Acceptance - 2026-06-25

Implemented BOM-style submitted policy baselines for Site Control Profile and Privacy. Seeded v1 records are submitted, Active, and defaulted. Landscape auto-picks default Site Control Profile records by Environment when omitted, and policy resolution now rejects draft/cancelled policy versions.

Validation:

- `bench --site dev.localhost migrate` passed.
- `bench --site dev.localhost run-tests --module lenscloud.api.test_policy` passed 13/13.
- `npm --prefix apps/lenscloud/frontend run build` passed.
- `lenscloud.api.policy.preview_subscription_topology` resolved the Free Plan against submitted `Public` Privacy and `Prod Controls v1`.

Authenticated Playwright was attempted but did not complete because `/tmp/lenscloud_credential_file.json` currently fails Platform login with `Invalid Login. Try again.` No credentials were exposed.

## Privacy Remodel Acceptance - 2026-06-25

Implemented Privacy as first-class master data and Privacy Profile as the submitted policy document linked to Privacy. Removed Privacy Profile status/version dependence, used deterministic names such as `PP-Public-01`, and kept submitted document detail editors visible read-only in the center editor.

Validation:

- `bench --site dev.localhost migrate` passed.
- Default submitted profiles exist: `PP-Public-01`, `PP-Private Shared-01`, `PP-Private-01`.
- Free Plan resolves to `PP-Public-01` and policy snapshot includes `privacy: Public`.
- `bench --site dev.localhost run-tests --module lenscloud.api.test_policy` passed 13/13.
- `npm --prefix apps/lenscloud/frontend run build` passed.
- Authenticated metadata framework, child-table editor, desktop Platform/Customer, and mobile Platform/Customer Playwright passed using `/tmp/lenscloud_credential_file.json`.

## Bench Command Platform Integration - 2026-06-25

Platform pulled Infra revision `dcd94d8` and consumed INF-010 from `lenscloud-infra/docs/platform-bench-command-handoff.md`.

Implemented Platform-side contract support:

- request ConfigMap and labelled Job creation through the Python Kubernetes API;
- policy, target, namespace, timeout, command, and typed args validation;
- `bench_test.status` as the first positive contract path;
- sanitized termination summary parsing;
- Orchestration Action Log evidence;
- cleanup of temporary command Job and ConfigMap;
- `Unsupported` response for contracted runner-pending commands.

Infra live verification of the INF-010 RBAC/admission contract is complete. Platform first recorded pre-firewall Kubernetes API reachability failure `ORCH-2026-00135`, then after the firewall update completed live `bench_test.status` successfully in `ORCH-2026-00137`. Unsupported-command behavior recorded `ORCH-2026-00136`. Remaining gap: publish a production runner for commands beyond the `bench_test.status` verification stub.
