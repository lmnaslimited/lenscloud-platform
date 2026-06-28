# LensCloud Platform Agent Handoff

## Purpose

This is the canonical handoff for active LensCloud Platform implementation.
Keep it short. Product rules belong in the linked domain documents; completed
evidence belongs in dated evidence records.

## Current Objective

Complete first-class Platform runtime lifecycle management, then finish live EU orchestration for three database privacy policies:

1. Public
2. Private Shared
3. Private

Platform operators must inspect and delete Platform-owned runtime resources without manager access. Both platform operators and customers using the Free Plan must create real Sites through the same server-side orchestration service.

## Runtime Truth

- cluster: `lenscloud-eu-dev`
- region: EU
- runtime namespace: `lenscloud-runtime-eu`
- shared Public MariaDB: `MariaDB/default/frappe-mariadb`
- Frappe Operator: `ghcr.io/vyogotech/frappe-operator:4.0.0`
- operator API: `vyogo.tech/v1`
- ingress class: `traefik`
- root domain: `cloud.lmnaslens.com`
- Headlamp: `https://headlamp.cloud.lmnaslens.com`
- restricted kubeconfig:
  `file:/run/secrets/lenscloud-eu.kubeconfig`
- wildcard DNS, TLS, routing, operators, nodes, storage, and restricted RBAC:
  Ready

Authoritative runtime details are in the adjacent `lenscloud-infra` repo:

- `docs/platform-handoff-contract.md`
- `docs/platform-live-orchestration-readiness.md`
- `docs/platform-restricted-access-contract.md`
- `docs/database-server-runtime-contract.md`
- `docs/wildcard-edge-contract.md`

## Approved Release

Create or update this platform data:

- Release Group: `lens-pure`
- registry/repository:
  `ghcr.io/lmnaslimited/lensdocker/lens-pure`
- Release tag: `v16.14.1`
- digest:
  `sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2`
- Frappe: `16.14.0`
- ERPNext: `16.13.1`
- included app: ERPNext
- build/release status: deployable after platform-side validation

This image passed live Frappe Operator acceptance:

- operator asset cache and PVC synchronization passed;
- Bench and Site reached Ready;
- login and generated CSS returned HTTPS 200;
- Administrator authentication passed.

Do not deploy `lenscx:v15.91.2`; it lacks the operator asset cache.

## Existing Implementation

The current code already includes:

- Database Server model and UI;
- Bench-to-Database Server attachment;
- Public, Private Shared, and Private policy validation;
- MariaDB, FrappeBench, and FrappeSite manifest generation;
- gated, idempotent Kubernetes apply;
- status synchronization and orchestration action logging;
- wildcard hostname and inherited TLS handling;
- platform and customer Site workflows;
- focused backend tests and frontend build coverage.

Inspect and reuse this implementation. Do not rebuild it from scratch.

## Runtime Lifecycle Authority

The canonical Platform contract is `docs/platform-runtime-lifecycle.md`. After Infra provisions and registers a Cluster, Platform owns routine inspection, reconciliation, suspension, retirement, and deletion of Platform-created Database Servers, Benches, Sites, and explicitly owned dependents. Manager cleanup is an interim blocker, not the intended operating model.

Old LensCloud Bench and Site records may be retired with their exactly matched runtime resources only after ownership and dependency validation.

Preserve:

- `MariaDB/default/frappe-mariadb`;
- Database Server and Cluster records needed for EU placement;
- operators, namespaces, RBAC, Traefik, wildcard TLS, Certbot, and Headlamp;
- resources not demonstrably owned by a retired LensCloud Bench or Site.

Never delete a namespace or use a broad label/name pattern without first
showing the exact matched resources.

## Lifecycle Milestone Gate

Before resuming Private Shared and Private live acceptance:

- Infra must publish namespace-scoped delete/read RBAC with positive and negative evidence;
- Platform manifests must carry stable ownership labels;
- Platform must implement secret-safe runtime inventory;
- Site, Bench, and platform-managed Database Server deletion must be asynchronous, audited, dependency-aware, protected-resource-safe, and retryable;
- platform UI must expose inspect/delete/progress/retry actions;
- create/inspect/delete acceptance must complete without manager intervention.

## Acceptance Scenarios

Run sequentially with unique `run-*` resource names.

### Public

- Register or reuse `default/frappe-mariadb`.
- Create Benches for two unrelated customers.
- Create one Site for each customer.
- Prove both Benches reference the same MariaDB CR.
- Prove distinct logical databases and credential Secret references.
- Verify both Sites over HTTPS.

### Private Shared

- Create one customer-owned MariaDB CR.
- Attach Quality and Production Benches for the same customer.
- Create one Site under each Bench.
- Reject attachment by another customer before Kubernetes apply.
- Verify both Sites over HTTPS.

### Private

- Create one MariaDB CR exclusive to one Bench.
- Create one Site and verify it over HTTPS.
- Reject every second Bench, including one for the same customer.

## Completion Contract

The milestone is complete only when:

- Release Group `lens-pure` and Release `v16.14.1` drive the Bench image;
- all three privacy scenarios pass;
- platform and customer Free Plan creation use the same backend;
- route health requires real HTTPS success, not only operator Ready;
- no standard Site creates DNS or Certificate resources;
- repeated reconcile is idempotent;
- all actions and failures are audited without secrets;
- authenticated Playwright covers platform and customer flows;
- temporary Private Shared and Private resources are cleaned safely;
- workitems and dated evidence are updated.

## Reading Order

1. `AGENTS.md`
2. `requirements.md`
3. this file
4. `docs/platform-workitems.md`
5. `docs/release-model.md`
6. `docs/database-server-model.md`
7. `docs/wildcard-domain-model.md`
8. `docs/state-model.md`
9. `docs/workflows.md`
10. `.agents/skills/frappe-ui-product/SKILL.md`
11. `docs/platform-runtime-lifecycle.md`
12. the Infra contracts listed under Runtime Truth

Use `docs/platform-agent-live-orchestration-prompt.md` as the executable agent
prompt.


## June 7 Live Run Handoff

Canonical evidence: `docs/live-orchestration-evidence-20260607.md`.

Completed:

- exact revisions verified: Platform `d422323`, Infra `60158e5`;
- migrations, 7/7 backend tests, production build, positive/negative RBAC;
- submitted `lens-pure` / `v16.14.1` Release with approved digest;
- stale prior run records retired only after exact CR 404 matches;
- Public live acceptance with two unrelated customers sharing `default/frappe-mariadb`;
- three live HTTPS Sites, including authenticated customer Free Plan creation;
- page and generated CSS HTTP 200 for every live Site;
- desktop and mobile authenticated Playwright;
- idempotent reapply and action-log evidence;
- Private Shared and Private dry-run manifests and explicit rejection evidence.

Apply is disabled.

Current live resources requiring manager cleanup before the sequential Private Shared run:

- FrappeBench `run-20260607-0623-pub-a`
- FrappeBench `run-20260607-0623-pub-b`
- FrappeSite `run-20260607-0623-platform`
- FrappeSite `run-20260607-0623-customer`
- FrappeSite `run-20260607-0623-free`
- their exact-prefix Jobs, Secrets, and PVCs in `lenscloud-runtime-eu`

The restricted Platform identity currently has no delete permission. Infra may perform the one-time exact-prefix cleanup to restore capacity, but routine manager cleanup must not become the operating model. The next milestone is the RBAC plus Platform lifecycle implementation defined above. Private Shared and Private live acceptance resume only after Platform can create, inspect, and delete its owned resources directly.


## June 11 Runtime Lifecycle Handoff

Canonical evidence: `docs/live-orchestration-evidence-20260611.md`. This section supersedes the June 7 statement that the restricted Platform identity has no delete permission; Infra has supplied the lifecycle RBAC contract and host-side evidence.

Completed in the current Platform worktree from base `818c262`:

- Python Kubernetes API-only permission preflight, apply, inspect, status, and delete paths; no `kubectl` runtime dependency;
- stable ownership labels on MariaDB, FrappeBench, FrappeSite, and Platform-created credential Secrets;
- secret-safe owner/dependent inventory and finalizer visibility;
- guarded asynchronous Site, Bench, and operator-managed Database Server deletion, retry, dependency checks, protected-resource checks, exact confirmation, and action logs;
- explicit MariaDB PVC `Retain`/`Delete` policy;
- Platform inspect/delete/progress/retry UI while customer runtime internals remain hidden;
- migrations, 15/15 backend tests, production build, and authenticated desktop/mobile Playwright.

Apply remains disabled. The current external blocker is Kubernetes API reachability from the devcontainer: Python API preflight timed out connecting to the cluster API on port 6443. No live acceptance resources were created or deleted in this pass.

Before resuming live acceptance, keep the host authorization watcher running:

```sh
cd /Users/arunkumar.ganesan/lensk8s/lenscloud-infra
./scripts/52-authorize-platform-api.sh --watch
```

Then rerun Python preflight and proceed sequentially with lifecycle create/inspect/delete, Private Shared, cleanup, Private, and cleanup. Never use manager cleanup as the normal path, and never mutate `MariaDB/default/frappe-mariadb`.

## June 22 Launch Topology Handoff

The current worktree adds versioned Environments, Site Control Profiles, Single through Four Tier Landscapes, independent Bench/Database Privacy rules, immutable Subscriptions, beta approval, policy-bound test gates, Free capacity rules, authoritative dashboard aggregates, native grouped Workspace Sidebar navigation, and a simplified customer launch journey.

Read next:

- `docs/product-topology-model.md`
- `docs/operator-sop/launch-reset-and-acceptance.md`
- `docs/launch-reset-evidence-20260622.md`
- `docs/design/stitch-customer-portal-prompt.md`

Migration, 32 backend tests, and the production frontend build passed before this handoff update. Live reset, fresh Free acceptance, sequential topology acceptance, and final authenticated browser evidence remain pending and must not be inferred from dry-run or unit-test results. Apply must remain disabled outside the controlled window. Site Control Profile runtime enforcement is now expected to use an Infra/operator-provided Bench Command Job/API, not invented FrappeSite CR fields.

Metadata-driven center editor: Platform forms now load LensCloud DocType field order and render Tab Break, Section Break, Column Break, Table, and Table MultiSelect fields. Release Group Included Apps is visible as a compact value-help chip control. Wide child grids keep row identity/primary/actions fixed and scroll remaining columns horizontally.

Customer/Site Platform visibility: restored the missing `Users` icon import that caused both ResourcePage routes to crash before rendering. Customer and Site now grant `LensCloud Platform User` read/create/write but not raw delete; Site deletion remains guarded by lifecycle APIs. Authenticated list regression coverage requires nonzero Customer and Site totals.

Metadata-driven permissions and connections: Resource creation/editing now follows Frappe DocType permissions rather than catalog flags. Related records come only from canonical DocType Links, return permission-filtered counts plus the latest five records, and count navigation opens the target list with the correct link-field filter. Customer editing and Subscription creation are available to LensCloud Platform User; Plan Table MultiSelect metadata remains authoritative over legacy catalog hints. Focused authenticated Playwright, generic metadata-editor Playwright, desktop/mobile Platform Playwright, production build, and 9 backend policy tests passed.

Policy/versioning decision: Subscription remains a regular DocType for the launch path, but native Frappe Workflow approval is now tracked as pending work for Free self-approval and paid/beta multi-level approval/rejection. Site Control Profile and Privacy should move to submitted, BOM-like immutable policy versions with amend/create-version flows, active/default selection, and Subscription snapshot stability. The design anchor is documented in `docs/product-topology-model.md`; canonical rows are in `docs/platform-workitems.md`.

Submitted policy/profile implementation: Site Control Profile and Privacy are now submittable policy documents. Site Control Profile has Environment, Profile Code, Default, and Amended From fields; Privacy has Privacy Family/Profile Code, Default, and Amended From fields. Seeded v1 controls/privacy profiles are submitted, Active, and defaulted. Landscape rows auto-pick an Environment default Site Control Profile when omitted. Plan and Subscription policy resolution reject non-submitted or non-Active policy versions. Backend policy tests pass 13/13 and production frontend build passes. Authenticated Playwright was attempted but blocked because `/tmp/lenscloud_credential_file.json` currently returns invalid Platform login credentials.

Privacy remodel implementation: submitted document detail editors now remain visible read-only, with Save disabled and Amend available from lifecycle controls. Privacy is first-class master data, Privacy Profile is the submitted policy document linked to Privacy, and seeded defaults are `PP-Public-01`, `PP-Private Shared-01`, and `PP-Private-01`. Plan Free now points to `PP-Public-01`; policy snapshots store both `privacy_profile` and `privacy`. Backend tests, frontend build, authenticated metadata/editor tests, and desktop/mobile authenticated Playwright passed.

## June 25 Bench Command Platform Handoff

Infra revision `dcd94d8` was pulled in `/workspace/lenscloud-infra`. Platform consumed INF-010 from:

- `/workspace/lenscloud-infra/docs/infra-workitems.md`
- `/workspace/lenscloud-infra/docs/platform-bench-command-handoff.md`
- `/workspace/lenscloud-infra/docs/bench-command-job-evidence-20260625.md`

Platform-side implementation now exists for the Bench Command Job/API contract:

- `lenscloud.api.bench_command.run_site_control_command`
- Python Kubernetes API-only request ConfigMap and labelled Job creation;
- Site/Bench/Subscription/Environment/Runtime Namespace validation;
- typed args and bounded timeout validation;
- `bench_test.status` positive contract path;
- structured `Unsupported` result for contracted but runner-pending commands;
- sanitized termination summary parsing;
- action-log evidence;
- best-effort cleanup of command Job and request ConfigMap after terminal state or failure;
- Site action surfaced as `Run Site Control command`.

This does not invent FrappeSite CR fields and does not use `kubectl`. Infra live verification/apply for INF-010 is complete at `dcd94d8`; after the firewall refresh, Platform live smoke completed `bench_test.status` successfully. Action logs: `ORCH-2026-00135` for the pre-firewall reachability failure, `ORCH-2026-00136` for unsupported-command behavior, and `ORCH-2026-00137` for the successful live `bench_test.status` run. Temporary smoke Site, Bench, and Customer records are absent. The temporary Job and ConfigMap were deleted and verified absent through the Python Kubernetes API. Current Platform evidence is `docs/bench-command-platform-evidence-20260625.md`.

Next action: production runner support for backup, restore, Bench Test trigger, and LATP remains pending. Infra `f3d8057` completed INF-011 and Platform now integrates runner-backed maintenance mode, developer mode, approved site_config, and CORS commands behind Site Control policy. Current Platform evidence is `docs/bench-command-runner-platform-evidence-20260628.md`.
## June 28 Bench Command Runner Integration

Infra revision `f3d8057` was pulled in `/workspace/lenscloud-infra`. Platform consumed the updated `docs/platform-bench-command-handoff.md` and `docs/bench-command-production-runner-evidence-20260627.md`.

Platform now keeps `bench_test.status` as the verification smoke path and enables the pinned production runner for `maintenance_mode.*`, `developer_mode.*`, approved `site_config.*`, and `cors.allowlist.*` commands. Backup, restore, `bench_test.trigger`, and LATP commands remain `Unsupported / COMMAND_UNSUPPORTED` until Infra publishes those runner contracts.

The backend validates typed args, Site/Bench/Runtime Namespace target, Subscription/Environment Site Control policy, and uses the Python Kubernetes API only. Runner Jobs use the pinned image digest from Infra and mount the expected Bench sites PVC. Current evidence is `docs/bench-command-runner-platform-evidence-20260628.md`.
