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

## 2026-07-02 Free Plan E2E Status

Infra `1bfc57c` resolved the old PVC/PV blocker for `run-20260629-free-prod-bench`; Platform verified old runtime absence with `ORCH-2026-00188`. A fresh Free Plan launch then passed: `SUB-00001`, `run-20260702-free-prod-bench`, `run-20260702-free-site.cloud.lmnaslens.com`, Site Ready/HTTPS/static asset proof `ORCH-2026-00199`, inventory `ORCH-2026-00200`. Apply was disabled after the live window.

`LC-E2E-20260702-003` is closed. Infra `e2a5483` added narrow terminal Bench Command pod cleanup RBAC/admission, and Platform retested successfully with `ORCH-2026-00206`. Final inventory showed no Platform-labelled Bench Command Pods, Jobs, or ConfigMaps in `lenscloud-runtime-eu`; Bench sites PVCs were Bound with no deletion timestamp. No remaining launch blocker is known from this pass.

## 2026-07-02 E2E Recovery And SOP Resume

E2E incident recovery is now documented. Every new incident must link an executable follow-up prompt under `docs/handoffs/platform/` or `docs/handoffs/infra/`, then close with retest evidence and resume from the next unpassed scenario. References: `docs/architecture/e2e-incident-management.md`, `docs/operator-sop/platform-customer-e2e-acceptance.md`, `docs/handoffs/platform/e2e-incident-followup-template.md`.

Resumed Free-first E2E validation passed: migration, frontend build, backend plan/policy/bench-command tests, authenticated desktop/mobile Playwright, subscribed dashboard visual check, and subscribed/exhausted Plans visual check. The test customer already owns the Free Subscription, so setup/review visual capture was skipped in this resumed run; entitlement behavior passed because Free is not startable again. Evidence: `docs/evidence/customer-launch/e2e-acceptance-20260702.md`.


## 2026-07-03 Customer Signup And Membership Status

Native Frappe signup is now wired as customer-only onboarding. Public signup creates or links a LensCloud Customer, creates a `Customer Member`, and keeps Platform users as admin-created users only. Same-domain signups join the existing Customer as `Pending` members and cannot provision until approved. `Customer Member` is exposed in the Platform Customers and Commerce area for operator review.

Validation passed: `bench --site dev.localhost run-tests --module lenscloud.api.test_customer_identity` passed 6 tests, including native Frappe signup, first company-domain owner, second same-domain pending member, public email individual Customer, Platform/System user skip, and pending-member provisioning rejection. Authenticated desktop and mobile route smoke also passed.


## 2026-07-03 Additional Signup Incident

`LC-E2E-20260703-001` is closed. A reported `user2@example.com` signup created `CUST002` as Active Owner because the existing `CUST001` legacy Customer has no `primary_domain`; same-domain pending membership only applies when Platform has an explicit `Customer.primary_domain` match. Frappe's `Please ask your administrator to verify your sign-up` message is account/email verification copy, not LensCloud Customer Member approval.

Fixes: LensCloud now provides `get_website_user_home_page` so Website Users land at `/lenscloud/customer/dashboard` rather than `/me`; Platform users land at `/lenscloud/platform/dashboard`; Customer Members is present in the Platform sidebar under Customers and Commerce. Validation: `test_customer_identity` passed 9 tests, migration passed, frontend build passed, and authenticated desktop/mobile route smoke passed.


## 2026-07-03 Account And Subscription UI Sanity

`LC-E2E-20260703-002` is closed and superseded for Account action placement by `LC-E2E-20260703-003`. Account no longer exposes password/sign-out actions in the header; those actions live in the shell account widget. Subscription `Choose a Plan` / `Add New Subscription` actions are explicit RouterLinks to `/customer/plans`. Forced all-caps/tracking styling was removed across LensCloud SPA Vue surfaces so headings and labels render in natural title/Pascal Case. Validation: frontend build passed, authenticated desktop/mobile Playwright passed, and the action smoke verifies Account/Subscription navigation.



## 2026-07-03 Password Dialog Editability Retest

`LC-E2E-20260703-003` was reopened after user retest found password fields were not editable. The fix replaces the password entry Dialog surfaces with deterministic native modal markup in Customer Account and Platform shell contexts. The authenticated test now fills Current Password, New Password, and Confirm New Password and verifies the values, so future regressions are caught. Validation: frontend build passed, targeted customer/platform browser probes passed, and authenticated desktop Playwright passed.

## 2026-07-03 Customer Native RBAC And Menus

`LC-E2E-20260703-004` is closed. Customer access now follows native Frappe Role Profiles and DocType permissions. Platform Settings may specify default Customer Admin/Member Role Profiles; if blank, the launch-safe conventional profiles `LensCloud Customer Admin` and `LensCloud Customer Member` are used when present. Signup/member approval creates or repairs Customer User Permission for the Customer. Customer sidebar entries with a DocType appear only when the backend permission payload grants read access. Subscription creation is denied unless native `Subscription` create permission is granted. The customer Members menu/approval page appears only with Customer Member permission. Legacy `Customer.user` owners are repaired without requiring a data migration.

Validation passed: `test_customer_identity` 10 tests, frontend production build, authenticated desktop Playwright, authenticated mobile Playwright, and an authenticated browser menu probe. Evidence: `docs/evidence/customer-launch/e2e-acceptance-20260702.md`.


## 2026-07-03 CUA Site Bootstrap And SSO Plan

Approved direction: implement Site setup wizard completion, OAuth/Social Login configuration, first-user/member sync, Site Access Grants, and passwordless `Open Site` through a Kubernetes API Bench Execute runner contract. Do not use target Site Administrator password as a browser/API credential. Platform documents the model in `docs/architecture/customer-identity-access.md` and the shared sequence in `docs/architecture/cua-site-bootstrap-sso-sequence.md`. Infra handoff: `docs/handoffs/infra/cua-site-bootstrap-sso-runner-20260703.md`.

Resume order: Infra implements/verifies the runner contract and returns sanitized evidence plus a Platform prompt. Platform then adds Site Bootstrap State, Site Access Grant, OAuth/client settings, backend runner calls, customer Subscription/Open Site UI, member access sync, tests, SOP evidence, and E2E acceptance.

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

The canonical Platform contract is `docs/architecture/platform-runtime-lifecycle.md`. After Infra provisions and registers a Cluster, Platform owns routine inspection, reconciliation, suspension, retirement, and deletion of Platform-created Database Servers, Benches, Sites, and explicitly owned dependents. Manager cleanup is an interim blocker, not the intended operating model.

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
5. `docs/architecture/release-model.md`
6. `docs/architecture/database-server-model.md`
7. `docs/architecture/wildcard-domain-model.md`
8. `docs/architecture/state-model.md`
9. `docs/architecture/workflows.md`
10. `.agents/skills/frappe-ui-product/SKILL.md`
11. `docs/architecture/platform-runtime-lifecycle.md`
12. the Infra contracts listed under Runtime Truth

Use `docs/handoffs/platform/platform-agent-live-orchestration-prompt.md` as the executable agent
prompt.


## June 7 Live Run Handoff

Canonical evidence: `docs/evidence/live-orchestration/live-orchestration-evidence-20260607.md`.

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

Canonical evidence: `docs/evidence/live-orchestration/live-orchestration-evidence-20260611.md`. This section supersedes the June 7 statement that the restricted Platform identity has no delete permission; Infra has supplied the lifecycle RBAC contract and host-side evidence.

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

- `docs/architecture/product-topology-model.md`
- `docs/operator-sop/launch-reset-and-acceptance.md`
- `docs/evidence/cleanup/launch-reset-evidence-20260622.md`
- `docs/design/stitch-customer-portal-prompt.md`

Migration, 32 backend tests, and the production frontend build passed before this handoff update. Live reset, fresh Free acceptance, sequential topology acceptance, and final authenticated browser evidence remain pending and must not be inferred from dry-run or unit-test results. Apply must remain disabled outside the controlled window. Site Control Profile runtime enforcement is now expected to use an Infra/operator-provided Bench Command Job/API, not invented FrappeSite CR fields.

Metadata-driven center editor: Platform forms now load LensCloud DocType field order and render Tab Break, Section Break, Column Break, Table, and Table MultiSelect fields. Release Group Included Apps is visible as a compact value-help chip control. Wide child grids keep row identity/primary/actions fixed and scroll remaining columns horizontally.

Customer/Site Platform visibility: restored the missing `Users` icon import that caused both ResourcePage routes to crash before rendering. Customer and Site now grant `LensCloud Platform User` read/create/write but not raw delete; Site deletion remains guarded by lifecycle APIs. Authenticated list regression coverage requires nonzero Customer and Site totals.

Metadata-driven permissions and connections: Resource creation/editing now follows Frappe DocType permissions rather than catalog flags. Related records come only from canonical DocType Links, return permission-filtered counts plus the latest five records, and count navigation opens the target list with the correct link-field filter. Customer editing and Subscription creation are available to LensCloud Platform User; Plan Table MultiSelect metadata remains authoritative over legacy catalog hints. Focused authenticated Playwright, generic metadata-editor Playwright, desktop/mobile Platform Playwright, production build, and 9 backend policy tests passed.

Policy/versioning decision: Subscription remains a regular DocType for the launch path, but native Frappe Workflow approval is now tracked as pending work for Free self-approval and paid/beta multi-level approval/rejection. Site Control Profile and Privacy should move to submitted, BOM-like immutable policy versions with amend/create-version flows, active/default selection, and Subscription snapshot stability. The design anchor is documented in `docs/architecture/product-topology-model.md`; canonical rows are in `docs/platform-workitems.md`.

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

This does not invent FrappeSite CR fields and does not use `kubectl`. Infra live verification/apply for INF-010 is complete at `dcd94d8`; after the firewall refresh, Platform live smoke completed `bench_test.status` successfully. Action logs: `ORCH-2026-00135` for the pre-firewall reachability failure, `ORCH-2026-00136` for unsupported-command behavior, and `ORCH-2026-00137` for the successful live `bench_test.status` run. Temporary smoke Site, Bench, and Customer records are absent. The temporary Job and ConfigMap were deleted and verified absent through the Python Kubernetes API. Current Platform evidence is `docs/evidence/bench-command/bench-command-platform-evidence-20260625.md`.

Next action: production runner support for backup, restore, Bench Test trigger, and LATP remains pending. Infra `f3d8057` completed INF-011 and Platform now integrates runner-backed maintenance mode, developer mode, approved site_config, and CORS commands behind Site Control policy. Current Platform evidence is `docs/evidence/bench-command/bench-command-runner-platform-evidence-20260628.md`.
## June 28 Bench Command Runner Integration

Infra revision `f3d8057` was pulled in `/workspace/lenscloud-infra`. Platform consumed the updated `docs/platform-bench-command-handoff.md` and `docs/bench-command-production-runner-evidence-20260627.md`.

Platform now keeps `bench_test.status` as the verification smoke path and enables the pinned production runner for `maintenance_mode.*`, `developer_mode.*`, approved `site_config.*`, and `cors.allowlist.*` commands. Backup, restore, `bench_test.trigger`, and LATP commands remain `Unsupported / COMMAND_UNSUPPORTED` until Infra publishes those runner contracts.

The backend validates typed args, Site/Bench/Runtime Namespace target, Subscription/Environment Site Control policy, and uses the Python Kubernetes API only. Runner Jobs use the pinned image digest from Infra and mount the expected Bench sites PVC. Current evidence is `docs/evidence/bench-command/bench-command-runner-platform-evidence-20260628.md`.

## June 29 Sequencing Decision

The next Platform gate is not the full lifecycle matrix. First complete live Bench Command runner acceptance against one real Platform-managed Ready Bench and Ready Site, preferably with non-destructive `maintenance_mode.status`, and record sanitized action-log plus Job/ConfigMap cleanup evidence. Current control-plane precheck found no Ready Site and no Ready Bench, so the live runner proof needs a temporary real Bench/Site created through the normal Platform lifecycle path before it can run.

After that evidence is captured, ask Infra to implement the remaining runner families: backup, restore, Bench Test trigger, and LATP. Platform should wire those remaining commands together only after Infra hands back the complete supported matrix. Full end-to-end testing from `docs/operator-sop/full-platform-lifecycle-test-plan-20260625.md` waits until the privacy policies and Site Control Profiles are ready.

June 29 real Free Plan runner attempt: Platform enabled apply for the controlled window, created temporary Bench `run-20260629-free-prod-bench`, and attempted `Reconcile Bench`. Kubernetes API connectivity timed out before FrappeBench acceptance. Action log: `ORCH-2026-00138`. Apply was restored to disabled, no Site/Subscription/Customer was created, and the failed temporary Bench record was cleaned. The devcontainer still cannot list ConfigMaps in `lenscloud-runtime-eu`; ask the host operator to refresh the API authorization watcher before retry. Evidence: `docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md`.

June 29 real Free Plan runner retry: after API reachability was restored, Platform created `run-20260629-free-prod-bench`, requested `run-20260629-free-prod-site.cloud.lmnaslens.com` through the Free Plan path, and created `SUB-00001` for `CUST001`. Bench reached Ready (`ORCH-2026-00140`), Site reached Ready with HTTPS/static asset 200 (`ORCH-2026-00155`), `bench_test.status` succeeded (`ORCH-2026-00156`), and `backup.create` remained Unsupported (`ORCH-2026-00158`). The first runner-backed `maintenance_mode.status` attempt failed with `TARGET_NOT_FOUND` (`ORCH-2026-00157`), then Infra `328846b` fixed the real Frappe Operator `frappe-sites/<site>/site_config.json` runner path and Platform updated the pinned runner digest. The retry passed (`ORCH-2026-00159`) with sanitized summary `layout=frappe-sites`, `maintenance_mode=0`, and cleanup verified no command Job/ConfigMap remains. The real Bench/Site/Customer/Subscription remain for follow-up inspection; apply is disabled. Evidence: `docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md`. Operator retest SOP: `docs/operator-sop/bench-command-real-site-runner-verification.md`.

## June 29 Bench Command Result Display Gap

User validation confirmed `maintenance_mode.status` succeeds but the Platform action result does not clearly display the actual status value, such as `Maintenance mode: Off`. The sanitized runner summary already included `details.key=maintenance_mode`, `details.value=0`, `layout=frappe-sites`, and `redacted=true` in `ORCH-2026-00159`, but the UI/backend needs a stable display contract before rendering all supported command outputs.

Platform handoff for Infra: `docs/handoffs/infra/bench-command-result-display-contract-20260629.md`. Canonical workitem: `Bench Command result display contract` in `docs/platform-workitems.md`.

## June 29 Agent Context Cleanup

The `.agents` folder was audited and documented. It currently contains only the
Frappe UI product skill, its two UI references, and optional metadata. No active
MCP server configuration is owned by `.agents`. `AGENTS.md` now requires the
Frappe UI skill only before Platform/customer frontend changes; backend,
orchestration, docs-only, and Infra-handoff work should not load UI context by
default. Governance and inventory are in `.agents/README.md`; dated evidence is
in `docs/agents/agent-context-cleanup-20260629.md`. Canonical workitem: `Agent context
and skill hygiene` in `docs/platform-workitems.md`.

## June 29 Documentation Structure Cleanup

Platform docs were reorganized by purpose. The root `docs/platform-workitems.md`
remains the canonical backlog. Durable models moved to `docs/architecture/`,
Platform and Infra handoffs moved to `docs/handoffs/`, dated proof moved to
`docs/evidence/`, agent-context docs moved to `docs/agents/`, and historical
backlog material moved to `docs/archive/`. Compatibility stubs remain at
`docs/agent-handoff.md`, `docs/platform-agent-live-orchestration-prompt.md`,
and `docs/platform-runtime-lifecycle.md`. Structure rules are in
`docs/README.md`; decision record is `docs/decisions/docs-structure-20260629.md`.
Canonical workitem: `Platform documentation structure` in
`docs/platform-workitems.md`.

## June 29 Bench Command Result Display Implementation

Infra `405e0c1` completed `INF-016` for sanitized Bench Command display results. Platform updated the pinned runner digest to `sha256:ab69e3ff24584e268bfa92f44c5d71e680ce1780cc8a4a9a5ce1e60b3e4bf4e7`, now returns `display` and `display_text` only when the runner marks `display.safe=true`, and renders the safe result in the Site action result card. The Orchestration Action Log message also includes the readable result. Live proof: `ORCH-2026-00161` returned `Maintenance mode: Off` for `maintenance_mode.status`; cleanup label query returned no Job/ConfigMap. Authenticated Playwright proof passed via `npm --prefix frontend run test:bench-command-display`; browser-driven action log `ORCH-2026-00165` also returned `Maintenance mode: Off` and cleanup was absent by label query. Evidence: `docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md`. Canonical workitem `Bench Command result display contract` is complete.

## June 30 Bench Command Backup Status Implementation

Infra `ac86bdc` completed `INF-017` for the metadata-only `backup.status` runner contract. Platform consumed `docs/handoffs/platform/bench-command-remaining-families-20260630.md` and the adjacent Infra handoff, updated the pinned runner digest to `sha256:eebfa0199c328207b14a949fa6232954a203a3937b1eed4930e9c3ec95b654d6`, and enabled `backup.status` as a supported read/status Site Control command.

Live proof: direct backend `backup.status` succeeded in `ORCH-2026-00170` with safe display `Backups: 0 available`; authenticated UI `backup.status` succeeded in `ORCH-2026-00172` and showed the same result card. Cleanup label verification for the browser-driven command returned no Job and no ConfigMap. `backup.create` remains Unsupported in both direct and UI checks (`ORCH-2026-00171`, `ORCH-2026-00173`), and restore, Bench Test trigger, and LATP commands remain Unsupported until Infra publishes those runner contracts.

Validation passed: Python compile, 17 backend Bench Command tests, production frontend build, and authenticated Playwright `test:bench-command-backup-status`. Evidence: `docs/evidence/bench-command/bench-command-backup-status-evidence-20260630.md`. Canonical workitem `Bench Command backup status` is complete; `Remaining Bench Command runner families handoff` stays In Progress for backup create, restore, Bench Test trigger, and LATP.

## June 30 Free-First Customer E2E Pivot

Platform deferred the remaining Bench Command families (`backup.create`, restore, Bench Test trigger, and LATP) until after Free-first customer E2E. `backup.status` remains supported; the other commands must continue to return Unsupported. Infra handoff: `docs/handoffs/infra/bench-command-remaining-families-deferred-20260630.md`.

The customer launch path is now Plan-first. Customer Dashboard points to Plan browsing, `/customer/plans` displays customer-friendly Plan cards and Free Plan setup, and `/customer/create-site` remains a compatibility setup route that calls the same customer subscription API. Backend context now returns Plans, Subscriptions, Sites, usage counts, and onboarding step without runtime internals. `request_customer_subscription` creates or links the Customer, self-approves Free subscriptions, reserves the hostname, creates the Prod Site, and starts the existing reconcile path; non-Free Plans create Pending Approval requests only.

CUA model is documented in `docs/architecture/customer-identity-access.md`: LensCloud Platform is the Central User Access system; lmnas.com signed-token handoff is documented but not implemented in this pass; user invites/RBAC/site SSO are later work. SOPs were updated so `docs/operator-sop/full-platform-lifecycle-test-plan-20260625.md` starts with the immediate Free-first E2E gate before the multi-tier matrix. Validation so far: Python compile, `bench --site dev.localhost run-tests --module lenscloud.api.test_policy` (15 passed), production frontend build, and authenticated desktop/mobile Playwright passed. Live Free E2E with controlled apply, HTTPS/static-asset proof, and dated evidence remains pending.

## June 30 Stitch Customer Portal UI Rehaul Start

Implementation started for the Free-first customer portal UI rehaul using only non-legacy Stitch artifacts under `docs/design/stitch_lenscloud_designs`. Legacy screenshot folders are excluded from redesign decisions. The target flow is production-wired, not mocked: customer dashboard and Plans must use `get_customer_portal_context`, Free Plan subscription must use `request_customer_subscription`, and provisioning/ready states must reflect real Site and Subscription records.

Documentation/evidence for this pass: `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md`. Canonical workitem: `Stitch customer portal UI rehaul` in `docs/platform-workitems.md`. Required validation: backend tests where touched, production frontend build, authenticated desktop/mobile Playwright, and explicit notes for any design element adapted because the current backend cannot truthfully support it.

## June 30 Stitch Customer Portal UI Rehaul Complete

Customer portal UI rehaul is implemented from non-legacy Stitch artifacts. Customer Dashboard, Plans, Sites, Account, and the compatibility Free setup route now use customer-safe Plan/Subscription/Site language and hide runtime internals. The Plans page includes a guided Plan selection, setup details, Free checkout summary with `₹0` due today and no payment method required, and real `request_customer_subscription` submission. Provisioning and ready states use real Site/Subscription context, not mock state.

Validation passed: Python compile, 15 backend policy/context tests, production frontend build, authenticated desktop Playwright, and authenticated mobile Playwright. Evidence: `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md`. Workitems `Customer dashboard and plan browsing UX` and `Stitch customer portal UI rehaul` are complete. The remaining launch gate is controlled live Free E2E with apply enabled, HTTPS/static asset proof, action-log evidence, and cleanup/retention decision.

## June 30 Customer Guided Activity Correction

User review rejected the first Stitch UI implementation because the Plans page still stacked Plan, setup, and checkout content instead of behaving as a true one-screen-at-a-time guided activity. Corrective workitem: `Customer guided activity correction` in `docs/platform-workitems.md`. The correction must keep production API wiring and customer-safe language while changing the interaction model to explicit step transitions.

## June 30 Customer Guided Activity Correction Complete

Corrected the customer Plans page after user review: `/customer/plans` is now a true one-screen-at-a-time guided activity: Choose Plan -> Setup Site -> Free Checkout -> Provisioning/Approval result. The Free checkout remains production-wired through `request_customer_subscription`, and authenticated desktop/mobile Playwright now walks the guided activity through checkout without creating a live subscription. Workitem `Customer guided activity correction` is complete; evidence is recorded in `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md`.

## June 30 Customer Dashboard Journey Entry Complete

After user review, the customer dashboard was narrowed to the journey entry requirement. `/customer/dashboard` now uses real Subscription state: no Subscription renders the Stitch-token welcome/start screen with a blue `Choose a Plan` primary action; existing Subscription renders the subscribed service dashboard state with `Open Site`, `View progress`, or `Continue setup`. Workitem `Customer dashboard journey entry state` is complete; evidence is recorded in `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md`.

## June 30 Customer Dashboard Visual Evidence And Token Polish Complete

After user review, Platform added Playwright visual comparison for `/customer/dashboard` against non-legacy Stitch references. Artifacts live under `docs/evidence/customer-launch/screenshots/20260630-dashboard/`. The current customer test state is `welcome`, compared against `welcome_to_lenscloud/screen.png` at desktop and mobile capture sizes. The dashboard welcome state was then polished to use the Stitch blue token `#1D4ED8`, one obvious `Choose a Plan` CTA, aligned icon/text, stronger white canvas, and a compact onboarding checklist. Workitems `Customer dashboard visual parity evidence` and `Customer dashboard token polish` are complete.

## June 30 Customer Self-Service Plan Catalog Requirement

New requirement documented in `docs/architecture/customer-self-service-plan-catalog.md` and tracked by canonical workitem `Customer self-service Plan catalog`. The next implementation pass should make `/customer/plans` match the non-legacy Stitch `choose_your_plan` and `choose_plan_mobile` references using first-class submitted Platform `Plan` records, portal visibility flags, feature JSON, default/recommended centering, and request-access/experimental controls. Subscribed dashboard visual evidence remains deferred until after a real customer onboarding cycle.

## June 30 Customer Self-Service Plan Catalog Complete

Implemented the customer Plan catalog from first-class submitted Platform `Plan` records. Added Plan portal flags, feature JSON, submitted-record gating, idempotent tier Plan seed patch, customer-safe API summary, request/self-service CTA gating, and a rebuilt `/customer/plans` selection screen. The customer portal now shows Tier 2 Growth, Free, and Tier 3 Scale; Tier 4 Enterprise is configured but hidden. Visual evidence against non-legacy Stitch plan references is under `docs/evidence/customer-launch/screenshots/20260630-plans/`. Workitem `Customer self-service Plan catalog` is complete.

## June 30 Customer Plan Selection UI Refinement Complete

Refined `/customer/plans` after user review. The Plan choice screen no longer shows redundant usage/legacy activity elements or a separate CTA panel. Plan cards are now the action surface: click selects the card, and the selected card button becomes `Start Free Plan` or `Request access`. Sites, environments, and placement are compact list rows; placement can be filtered by All/Public/Private. Visual evidence now records desktop order `Tier 2 Growth, Free, Tier 3 Scale` and mobile order `Free, Tier 2 Growth, Tier 3 Scale`. Workitem `Customer Plan selection UI refinement` is complete.

## July 1 Customer Plan Page Chrome Cleanup Complete

Completed the focused `/customer/plans` cleanup after user review. The customer Plan activity no longer shows the redundant Free-first launch wrapper, old duplicated Plan heading/helper, or top-right `Refresh`/`Dashboard` actions. The right inspector now owns launch progress and current selection. Setup and checkout visible headings now match the guided activity (`Set up your first Site`, `Confirm your Free subscription`). Validation passed: production frontend build, authenticated desktop/mobile Playwright, and Plan visual comparison against non-legacy Stitch references. Evidence: `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md` and `docs/evidence/customer-launch/screenshots/20260630-plans/report.md`. Workitem `Customer Plan page chrome cleanup` is complete.

## July 1 Customer Setup And Review Stitch Mapping Complete

Completed the focused setup/review mapping pass for `/customer/plans`. Launch progress now shows green completed-step checks, current blue step, and muted pending steps. The setup screen maps to `docs/design/stitch_lenscloud_designs/setup_your_site/screen.png`; the review screen maps to `docs/design/stitch_lenscloud_designs/review_subscription/screen.png` and the available checkout HTML structure. Frappe UI primitives remain in use where compatible (`Button`, `Alert`, `Badge`); the setup step intentionally uses the native `select` and `input` controls from Stitch `code.html`, with custom layout limited to Stitch-specific stepper/card/checkout composition. Validation passed: production frontend build, authenticated desktop/mobile Playwright, and expanded customer guided-flow visual report. Evidence: `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md` and `docs/evidence/customer-launch/screenshots/20260630-plans/report.md`. Workitem `Customer setup and review Stitch mapping` is complete.

## July 1 Customer Setup Exact Code Adaptation Complete

After user review, Platform replaced the approximated setup step with a direct adaptation of `docs/design/stitch_lenscloud_designs/setup_your_site/code.html`. The setup screen now renders the supplied `Setup Your Site` card structure with Region select, segmented `https://` + subdomain + Platform domain input, availability badge, Site Name, Back, and `Continue to Review`. Region choices now come from active Regions attached to active Clusters; the domain suffix comes from Platform Settings `root_domain`; the internal customer/company value is derived from Site Name so the UI stays faithful to Stitch. Validation passed: production frontend build, 3 Plan catalog backend tests, authenticated desktop/mobile Playwright, and expanded visual report. Evidence: `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md` and `docs/evidence/customer-launch/screenshots/20260630-plans/report.md`.

## July 1 Customer Review Subscription Exact Code Adaptation Complete

After user review, Platform replaced the approximated review step with a direct adaptation of `docs/design/stitch_lenscloud_designs/review_subscription/code.html`. The review screen now renders `Review Subscription`, `Order summary`, `Price breakdown`, `Total due today`, `No payment method required for Free Plan`, `Start Free Subscription`, and `Cancel`, with live Plan/Region/Subdomain values. The checkout inspector now uses the Stitch-style `Your service / Checkout details` copy. Customer Dashboard was also corrected to use `get_customer_portal_context.sites` instead of generic `/api/resource/Site`, removing a customer 403 console error. Validation passed: production frontend build, authenticated mobile and desktop Playwright, and expanded visual report. Evidence: `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md` and `docs/evidence/customer-launch/screenshots/20260630-plans/report.md`.

## July 1 Customer Subscription Summary Screen Complete

Added the customer-facing `Subscriptions` sidebar entry and `/customer/subscriptions` page. The page intentionally uses service cards plus a compact detail inspector instead of the Platform list/detail model, because customers are expected to have a small number of subscriptions. It is wired to `get_customer_portal_context` and shows only customer-safe Plan/status/Region/Site/payment information. Runtime internals remain hidden. Validation passed: production frontend build plus authenticated desktop/mobile Playwright. Evidence: `docs/evidence/customer-launch/customer-portal-ui-rehaul-20260630.md`. Canonical workitem `Customer subscription summary screen` is complete.

## July 1 Customer Subscription Lifecycle Detail Complete

Completed the customer Subscription detail refinement. The customer sidebar no longer includes a standalone `Sites` menu; Sites are shown inside the selected Subscription Landscape progression. Backend schema now includes Plan `billing_frequency` plus Subscription `plan_frequency` and `next_renewal_date`. `get_customer_portal_context` enriches each Subscription with Plan-specific payment copy and environment-by-environment progress, including ready Site links and customer-safe release version labels. Update architecture/SOP/evidence before further customer portal work.

## July 1 Mobile Workspace Inspector Access Complete

Added a shared mobile inspector bottom sheet to `WorkspaceLayout`. The desktop right rail remains unchanged, while mobile/tablet users get a persistent `Details` trigger that opens the same inspector slot content. Updated architecture, SOP, canonical workitems, evidence, and authenticated Playwright so mobile tests must open the inspector drawer and verify representative content.

## July 1 Customer Subscription-Led Navigation Cleanup Complete

Customer navigation is now subscription-led. Removed `Create Site` from the customer sidebar, changed Subscriptions CTA to `Add New Subscription`, routed Dashboard progress/setup actions and Subscription count to `/customer/subscriptions`, and left Site count cards informational. Added customer-specific Plan entitlement summaries to `get_customer_portal_context`; exhausted Plans remain visible but disabled, and `request_customer_subscription` enforces limits server-side. Account page redesign remains the next customer UX pass.

## July 1 Customer Account And Access Pass Started

Account redesign is now canonical scope. Dashboard is the service command center; Account is the identity, organization, and Central User Access trust surface. Account should sit in the bottom/profile area of customer navigation and avoid duplicating Plan/Site/provisioning workflows. Architecture, SOP, workitems, and evidence were updated before implementation.

## July 1 Customer Account And Access Pass Complete

Completed Account redesign. Customer navigation now separates primary service workflow items from the bottom Account/profile area. Account is a warm identity/access surface with profile editing through the customer-safe `update_customer_account` API, organization/customer context, Central User Access guidance, coming-soon team invites, support/billing placeholders, and read-only links back to Subscriptions. Dashboard remains the service command center; Account avoids Plan comparison, checkout, and provisioning-heavy timelines. Build, backend plan catalog tests, desktop Playwright, and mobile Playwright passed.

## July 1 Customer Visual Coherence Redesign Handoff

User review found that individual customer screens still do not feel visually coherent enough for launch, even though the functional subscription-led flow is improving. Broad customer UI work should pause until the design team/Stitch returns a complete coherence package. Canonical workitem: `Customer portal visual coherence redesign`.

Design prompt: `docs/design/stitch-customer-portal-coherence-prompt.md`. The prompt explicitly asks Stitch for desktop/mobile screens, Frappe UI mapping, tokens, interaction specs, accessibility notes, and implementation-ready code artifacts. The design should unify Dashboard, Plans, guided setup, review/checkout, provisioning, Subscriptions, Account, navigation, and the mobile Details drawer. The Subscription screen pattern is the current strongest in-product reference.

E2E can continue against the current functional baseline using `docs/operator-sop/platform-customer-e2e-acceptance.md`. Treat visual coherence defects as launch UX findings unless they block the customer from choosing a Plan, creating a Free Subscription, tracking progress, opening the Site, or understanding Account/access boundaries.

## July 2 Pre-Final E2E Attempt And Cleanup Blocker

Started the pre-final Platform/customer E2E reset and fixed the customer provisioning retry gap found by user validation. Backend now maps customer Site reconcile `dry_run` to a customer-safe `paused` state instead of `started`, exposes `retry_customer_site_provisioning`, and reuses an existing reserved Site when retrying after Platform opens the controlled apply window. Customer Plans result screen now renders started, paused, failed, and retry states with customer-safe language based on the Stitch provisioning failure reference.

Evidence and scenario register: `docs/evidence/customer-launch/e2e-acceptance-20260702.md`. Canonical incident tracker: `docs/incidents/e2e-incident-tracker.md`. Incident requirement: `docs/architecture/e2e-incident-management.md`. SOP: `docs/operator-sop/platform-customer-e2e-acceptance.md`.

Cleanup status: `acme.cloud.lmnaslens.com` was dry-run only and is marked Deleted (`ORCH-2026-00179`). `run-20260629-free-prod-site.cloud.lmnaslens.com` was deleted normally and runtime inventory showed the owner/related resources absent (`ORCH-2026-00180` through `ORCH-2026-00183`). `run-20260629-free-prod-bench` delete was accepted and the FrappeBench owner CR is absent (`ORCH-2026-00184`/`ORCH-2026-00187`), but PVC `lenscloud-runtime-eu/run-20260629-free-prod-bench-sites` remains terminating with `kubernetes.io/pvc-protection`. Incident `LC-E2E-20260702-002` blocks clean live E2E reset. Infra handoff: `docs/handoffs/infra/e2e-cleanup-pvc-blocker-20260702.md`.

Validation passed: Python compile for `orchestration.py`, production frontend build, `lenscloud.api.test_plan_catalog` including the new dry-run-to-paused regression, authenticated desktop Playwright, and authenticated mobile Playwright. Live Free provisioning/HTTPS/static-asset proof is still blocked until Infra resolves the terminating PVC or approves fresh capacity creation while the old PVC is handled separately.

## July 3 Customer Account Widget Correction Complete

Closed incident `LC-E2E-20260703-003`. Account actions no longer sit in the Account page header. The shell account chip now opens a floating widget with Profile, Change Password, and Sign Out. Change Password routes to `/customer/account?changePassword=1` and opens a compact in-page dialog that calls Frappe's native password update method without leaving LensCloud. Sign Out remains in the widget and returns the user to `/login`. Validation passed: `npm --prefix frontend run build`, authenticated desktop Playwright, authenticated mobile Playwright, and forced all-caps Vue scan returned no matches.
