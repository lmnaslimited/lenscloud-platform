# Full Platform Lifecycle Test Plan - Clean Baseline

## Goal

Validate the Free-first LensCloud launch path first, then run the broader Platform lifecycle matrix after the customer E2E gate passes:

- Platform readiness and cluster gates
- Free Plan signup, Plan browsing, Subscription, and automatic provisioning
- Subscription, Landscape, Environment, Privacy Profile, and Site Control Profile resolution
- Platform-created Database Server, Bench, and Site lifecycle
- Runtime inspection and status synchronization
- Deletion through Platform lifecycle APIs
- Policy rejection and namespace filtering
- Customer portal usability, dashboard, and Plan browsing
- Authenticated desktop and mobile Playwright coverage

## Baseline

Start from the verified clean state:

- `Platform Settings.kubernetes_apply_enabled = 0`
- Sites: 0
- Benches: 0
- Customers: 0
- Subscriptions: 0
- Orchestration Action Logs: 0
- Database Servers: only `EU Shared MariaDB 01`
- Approved runtime namespace: `lenscloud-runtime-eu`
- Protected runtime resource: `default/frappe-mariadb`

Do not delete or mutate `default/frappe-mariadb`.


## 0. Immediate Free-First E2E Gate

Run this gate before the multi-tier lifecycle matrix. The remaining Bench Command families (`backup.create`, restore, Bench Test trigger, and LATP) are deferred and must not block this gate while they truthfully return Unsupported.

1. Confirm Platform readiness:
   - signup enabled;
   - wildcard root domain configured;
   - active Free Plan exists;
   - one ready shared Free Bench exists for the target Region;
   - Kubernetes apply is disabled before the controlled window.
2. Sign in or sign up as a customer through the native LensCloud flow. Record the future `lmnas.com` signed-token handoff as an integration gap; do not require it for this pass.
3. Open Customer Dashboard and confirm the primary action is Plan browsing, not direct runtime setup.
4. Open Customer Plans and confirm Plan cards show friendly outcomes only: price/availability, environments, Site limit, approval state, and isolation summary. No Bench, Database Server, namespace, CR, Secret, or kubeconfig details may appear.
5. Select the Free Plan, Region, Site name, company/project, and subdomain.
6. Submit and confirm Platform creates or reuses the Customer, creates an Approved Free Subscription, reserves the hostname, creates the Prod Site, and starts reconcile through the existing orchestration service.
7. Watch Customer Dashboard and Sites until provisioning progress is visible. If apply is enabled for the controlled window, continue until HTTPS and static asset checks pass.
8. In Platform, verify Customer, Subscription, Site, Bench, and Orchestration Action Log records. Counts must match dashboard values.
9. Capture evidence: user, Customer, Subscription, Site, Plan, Region, hostname, action log IDs, HTTPS/static asset result, unsupported-command behavior if tested, and cleanup state.
10. Disable apply after the run unless another controlled live scenario is explicitly approved.

Expected result: the Free Plan launch journey is understandable without operator terminology, and provisioning is driven by Subscription + Plan policy rather than customer runtime choices.

## 1. Preflight

1. Open Platform as a Platform operator.
2. Open Platform Settings and confirm Kubernetes apply is disabled.
3. Run Cluster readiness / validate cluster gates.
4. Confirm:
   - restricted kubeconfig is readable server-side;
   - runtime namespace is `lenscloud-runtime-eu`;
   - namespace discovery shows only approved Runtime Namespace records for lifecycle choices;
   - default MariaDB is visible as protected/read-only;
   - no Secret values are shown in UI, API responses, or logs.
5. Run backend/frontend checks if this is a release candidate:
   - `bench --site dev.localhost migrate`
   - `bench --site dev.localhost run-tests --module lenscloud.api.test_policy`
   - `npm --prefix apps/lenscloud/frontend run build`

Expected result: all gates pass, apply remains disabled, and no old tenant/runtime records are visible.

## 2. Seed Product Baseline

Confirm these master/config records exist:

- Region: `EU`
- Cluster: `lenscloud-eu-dev`
- Runtime Namespace: `lenscloud-runtime-eu`
- Release Group: approved launch release group
- Release: approved launch image and digest
- Privacy records: Public, Private Shared, Private
- Privacy Profiles: submitted/default profiles as configured
- Landscapes: Single, Two, Three, Four tier
- Site Control Profiles for the active environments
- Plan: Free Plan

For Free Plan, confirm:

- availability allows signup;
- release group is set;
- landscape resolves to Single/Prod;
- default privacy resolves to Public;
- exactly one active Free Plan exists per release group.

## 3. Product Topology Acceptance

Run these checks before live provisioning. This proves that runtime resources are created from product policy, not from manually assembled Bench/Database choices.

### 3.1 Plan Resolution

For every Plan used in this test, confirm:

- Release Group is set.
- Landscape is set.
- Default Privacy Profile is set.
- Default Privacy Profile is included in Allowed Privacy Profiles.
- Allowed Privacy Profiles are submitted/non-cancelled profiles only.
- Availability is correct:
  - Free Plan: Public or signup-eligible.
  - Paid/beta plans: Beta, Invite Only, or approval-gated as intended.
- Subscription and Site limits are configured.

Expected result: a customer-facing Plan resolves to one release group, one landscape, and one default privacy policy without requiring the customer to know Bench, Database Server, namespace, or CR names.

### 3.2 Landscape and Environment Resolution

Validate the active Landscape rows:

| Landscape | Required Environments | Expected Behavior |
| --- | --- | --- |
| Single | Prod | one production Site path |
| Two | QA, Prod | QA and Prod Sites are separate environments |
| Three | Dev, QA, Prod | Dev/QA and Prod policy boundaries are enforced |
| Four | Dev, QA, Pre-Prod, Prod | Pre-Prod and Prod are independently controlled higher environments |

For each Landscape:

1. Open the Landscape in Platform.
2. Confirm each child Environment row has an Environment.
3. Confirm each row resolves an active/submitted Site Control Profile for that Environment.
4. Confirm row order and labels match the customer journey.
5. Confirm inactive/cancelled control profiles cannot be selected.

Expected result: the Site creation flow can derive valid environment choices from the Subscription's Landscape.

### 3.3 Site Control Profile Resolution

For each Environment used by the test:

- Confirm the default Site Control Profile is active/submitted.
- Confirm environment-specific controls are set:
  - developer mode;
  - server scripts;
  - client scripts;
  - CORS allowlist;
  - typed site configuration;
  - Bench Test gate;
  - LATP gate.
- Confirm higher environments, especially Pre-Prod and Prod, use restricted controls.
- Confirm Production LATP permits only non-destructive suites.
- Confirm the Infra/operator Bench Command Job/API contract is available for supported runtime enforcement.
- Dedicated real Bench/Site runner proof is complete as of 2026-06-29:
  - evidence: `docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md`;
  - `bench_test.status`: passed in `ORCH-2026-00156`;
  - `maintenance_mode.status`: passed in `ORCH-2026-00159` after Infra `328846b` real sites path fix;
  - Platform used the pinned runner Job, mounted the Bench sites PVC at `/home/frappe/frappe-bench/sites`, recorded sanitized evidence, and deleted the temporary Job/ConfigMap.
- Attempt one runner-pending command, such as `backup.create` or `latp.trigger`, and confirm Platform returns `Unsupported` instead of pretending enforcement succeeded.
- Do not start the full privacy/topology end-to-end matrix until privacy policies and all required Site Control runner contracts are ready.
- If a specific command family is not available, record that control as Platform policy-only or Unsupported and do not claim live runtime enforcement.

Expected result: each Site receives the effective controls for its Subscription and Environment. If the Bench Command Job/API exists, Platform applies or verifies supported controls through that API. If it does not exist, Platform records a production gap instead of inventing unsupported CR fields.

### 3.4 Privacy Profile Resolution

For each Privacy Profile used by the test:

- Confirm it is submitted/non-cancelled.
- Confirm it links to the correct Privacy record.
- Confirm database boundary rule is clear.
- Confirm Bench boundary rule is clear.
- Confirm customer boundary rule is clear.
- Confirm environment sharing rules are explicit.

Minimum policy matrix:

| Privacy Shape | Database Policy | Bench Policy | Required Rejection |
| --- | --- | --- | --- |
| Public | shared platform database allowed | shared Free/Public Bench allowed | customer cannot select runtime internals |
| Private Shared | customer-owned shared database allowed where configured | separate Benches by environment where configured | cross-customer sharing rejected |
| Private | customer-owned/exclusive database | exclusive Bench according to profile | second Bench/Site shape rejected where profile forbids it |

Safe default expectation:

- Dev and QA may share a customer database only if the selected Privacy Profile allows it.
- Dev and QA should use separate Benches unless the selected Privacy Profile explicitly allows sharing.
- Pre-Prod and Prod must not share a database or Bench with lower environments unless a deliberate, audited profile says otherwise.

Expected result: Product policy produces deterministic database and Bench placement for each Environment.

### 3.5 Subscription Resolution

For each test customer:

1. Create a Subscription from Customer, Plan, Region, Landscape, and Privacy Profile.
2. Confirm the Subscription captures an immutable policy snapshot or equivalent effective policy evidence.
3. Confirm the Subscription exposes only Environments from its Landscape.
4. Confirm one active Site per Subscription and Environment.
5. Confirm changing Plan, Landscape, or Privacy Profile after creation requires the approved upgrade/versioning path, not silent mutation.

Expected result: Sites are created from `Subscription + Environment`, and the runtime shape follows the Subscription policy.

### 3.6 Free Plan Rules

Validate the Free Plan specifically:

- Free Subscription is self-approved.
- Landscape is Single.
- Environment is Prod only.
- Privacy Profile is Public.
- Region selection maps to the ready shared Free Bench for that Region.
- Customer cannot choose Bench, Database Server, Runtime Namespace, or Secret-related fields.
- Exactly one active Free Plan exists per Release Group.
- Exactly one ready shared Free Bench exists per Free Plan and Region, or the readiness dashboard reports the gap.

Expected result: Free signup is simple and deterministic while Platform keeps operational control.

### 3.7 Non-Free Approval Rules

For Two-tier and higher Plans:

1. Create a Subscription request.
2. Confirm it starts as Pending Approval or the configured workflow state.
3. Confirm provisioning actions are blocked before Platform approval.
4. Approve as Platform operator.
5. Confirm allowed Environments become provisionable after approval.
6. Reject one request and confirm no runtime records are created.

Expected result: non-Free provisioning is governed by Subscription approval/workflow, not by direct customer access to runtime records.

## 4. Controlled Apply Window

1. Record the current time and tester.
2. Enable Kubernetes apply in Platform Settings.
3. Keep the test sequential; do not start another live scenario while one is still cleaning up.

Expected result: apply is enabled only for this controlled test window.

## 5. Subscription-Driven Runtime Lifecycle

Use a unique run prefix, for example:

```text
run-YYYYMMDD-HHMM
```

1. Create a temporary customer.
2. Create or request a Subscription from the target Plan.
3. Confirm the Subscription resolves:
   - Region;
   - Release Group;
   - Landscape;
   - allowed Environments;
   - selected Privacy Profile;
   - Site Control Profile per Environment.
4. For each Environment in the Subscription:
   - create the Site from `Subscription + Environment`;
   - verify the effective policy snapshot on the Site;
   - verify generated/selected Bench and Database placement matches the Privacy Profile;
   - preview generated runtime manifests.
5. Reconcile any required platform-managed Database Server.
6. Sync Database Server status until accepted/ready or a clear blocker is shown.
7. Inspect Database Server runtime inventory.
8. Reconcile required Bench records.
9. Sync Bench status and inspect runtime.
10. Reconcile Site records.
11. Sync Site status and inspect runtime.
12. Open every ready HTTPS route and confirm static assets load.

Evidence to capture:

- record names;
- Subscription, Plan, Landscape, Environment, Privacy Profile, and Site Control Profile names;
- effective policy snapshot/hash where available;
- action log IDs;
- runtime namespace/name;
- status transitions;
- route URL;
- finalizer/condition summary;
- no Secret values exposed.
- Bench Command Job/API action IDs and sanitized output for any applied Site Control operations.
- cleanup proof for temporary Bench Command Jobs and request ConfigMaps.

## 6. Deletion Lifecycle

Clean the objects through Platform, in this order:

1. Delete Site.
2. Inspect until owner CR is absent and Site is `Deleted`.
3. Delete Bench.
4. Inspect until owner CR is absent and Bench is `Deleted`.
5. Delete the platform-managed Database Server.
6. Inspect until owner CR is absent and Database Server is `Deleted`.

Expected result:

- Platform accepts deletion only with exact confirmation text.
- Dependent cleanup prevents Bench deletion while Sites remain.
- Dependent cleanup prevents Database Server deletion while Benches remain.
- Normal operator finalizers are used.
- Platform never manually removes finalizers as a routine action.
- Subscription state reflects deleted/cleaned Sites after teardown.

## 7. Free Signup Journey

1. Sign up or log in as a customer.
2. Create/link Customer through the guided flow.
3. Select Free Plan.
4. Confirm Region.
5. Enter a unique subdomain.
6. Review and submit.
7. Watch provisioning progress.
8. Open the ready HTTPS site.

Expected result:

- customer never chooses Bench, Database Server, namespace, CR name, Secret, or Kubernetes details;
- Free Plan creates a self-approved Subscription;
- Subscription resolves to Single Landscape, Prod Environment, Public Privacy Profile, and the default Prod Site Control Profile;
- Free Plan creates/uses the correct public shared Bench for the selected Region;
- customer dashboard shows product-level progress and recovery guidance;
- Platform dashboard counts match direct records.

## 8. Policy Rejection Tests

Attempt and confirm rejection for:

- selecting an unapproved runtime namespace;
- selecting a namespace for the wrong customer;
- mutating `default/frappe-mariadb`;
- deleting a Bench with active Sites;
- deleting a Database Server with active Benches;
- creating a second Bench where Private policy allows only one;
- sharing Production with non-production where policy forbids it;
- cross-customer use of Private or Private Shared runtime resources.
- creating a Site for an Environment not present in the Subscription Landscape;
- creating a second active Site for the same Subscription and Environment;
- using a Privacy Profile not allowed by the Plan;
- using a cancelled Privacy Profile or cancelled Site Control Profile;
- provisioning a non-Free Subscription before approval.
- executing a Site Control command that is not allowed by the active Site Control Profile;
- executing a Site Control command against the wrong customer, Subscription, Environment, Bench, or Site.

Expected result: each rejection gives a clear message and next action.

## 9. Multi-Tier Sequential Acceptance

Run one scenario at a time and clean it before starting the next:

1. Single tier:
   - Subscription resolves Single Landscape.
   - Prod Site only.
   - Public/Free behavior verified.
2. Two tier:
   - Subscription resolves Two-tier Landscape.
   - QA and Prod Sites.
   - selected Privacy Profile drives Database and Bench sharing policy.
3. Three tier:
   - Subscription resolves Three-tier Landscape.
   - Dev, QA, Prod.
   - Dev/QA sharing policy and Prod isolation verified from the Privacy Profile.
4. Four tier:
   - Subscription resolves Four-tier Landscape.
   - Dev, QA, Pre-Prod, Prod.
   - Site Control Profile restrictions and higher-environment isolation verified.

Use this minimum matrix:

| Scenario | Plan Type | Landscape | Environments | Privacy Profile | Expected Runtime Shape |
| --- | --- | --- | --- | --- | --- |
| Free launch | Free | Single | Prod | Public | shared public database and shared Free/Public Bench |
| Two-tier beta | approval-gated | Two | QA, Prod | configured allowed profile | QA and Prod placement follows profile; no customer runtime choices |
| Three-tier growth | approval-gated | Three | Dev, QA, Prod | configured allowed profile | Dev/QA may share database only if profile allows; Prod isolated |
| Four-tier enterprise | approval-gated | Four | Dev, QA, Pre-Prod, Prod | Private or configured profile | Pre-Prod and Prod isolated; cross-customer sharing rejected |
| Rejection path | any non-Free | any | any | disallowed/cancelled profile | Subscription/Site creation or provisioning is blocked |

For each scenario:

- create Customer and Subscription;
- confirm Subscription policy resolution;
- create Sites from allowed Environments;
- reconcile sequentially;
- verify HTTPS;
- verify policy boundaries;
- delete through Platform;
- confirm runtime absence before moving on.

## 10. Authenticated Playwright

Use the credential file provided for test automation and ensure it is mode `0600` before running.

Run:

```bash
npm --prefix apps/lenscloud/frontend run build
```

Then run the authenticated Platform and Customer Playwright scripts used by the repo. Capture:

- desktop Platform console journey;
- mobile Platform navigation;
- desktop customer signup/provisioning journey;
- mobile customer journey;
- no browser console errors.

## 11. Closeout

Before ending the test window:

1. Disable Kubernetes apply.
2. Capture final Platform counts.
3. Capture final runtime inventory for `lenscloud-runtime-eu`.
4. Preserve only required shared launch capacity.
5. Update the dated evidence doc with:
   - successes;
   - failures;
   - action log IDs;
   - cleanup results;
   - Bench Command supported/unsupported behavior;
   - remaining production gaps;
   - any Infra handoff items.

## Customer Subscription Screen Check

During Free-first E2E, validate the customer `Subscriptions` menu after the Plan flow:

1. Confirm the customer sidebar shows `Subscriptions` and does not show a standalone `Sites` menu.
2. Open Customer portal > Subscriptions.
3. Confirm the page uses customer-safe service cards, not a Platform list view.
4. Confirm each card shows Plan, status, Region, Landscape, environment count, and a next action.
5. Confirm the detail panel shows Subscription, Plan, Region, start date, end date when set, billing frequency, next renewal date, and Plan-specific payment summary.
6. Confirm Free Plan copy says `₹0 due today` and no payment method is required, while paid/beta/request-access Plans do not reuse Free Plan payment copy.
7. Confirm the detail panel shows Landscape progress as environment rows. Each row should show the environment, Site status/provisioning state, customer-safe version when available, and an `Open Site` link only for ready Sites.
8. Confirm the screen never exposes Bench, Database Server, Runtime Namespace, Kubernetes, CR names, Secrets, action logs, pod logs, kubeconfig, or raw operator resource names.
9. For no subscription, confirm the empty state points to `Choose a Plan`.
10. On mobile, tap the shared `Details` button and confirm the bottom-sheet inspector opens.
11. Confirm the mobile inspector shows the same customer-safe Subscription/Landscape detail as the desktop right pane.
12. Close the drawer and confirm focus returns to the page without navigation loss.
13. Run desktop and mobile authenticated Playwright with console-error checks. The mobile test must open the inspector drawer; route-load checks alone are not sufficient.

## Mobile Workspace Inspector Check

For every customer or Platform surface that uses `WorkspaceLayout`:

1. Open the page at a mobile viewport.
2. Confirm the `Details` trigger is visible near the bottom of the workspace.
3. Tap `Details` and confirm a bottom-sheet drawer opens with the page inspector title/subtitle and inspector content.
4. Confirm the drawer content matches the desktop inspector contract for that page.
5. Confirm close/backdrop behavior returns to the same page state.
6. Confirm customer drawers do not expose Bench, Database Server, Runtime Namespace, Kubernetes, CR names, Secrets, action logs, pod logs, kubeconfig, or raw operator resource names.

## Customer Navigation And Entitlement Check

During Free-first E2E and customer regression testing:

1. Confirm customer navigation shows Dashboard, Plans, Subscriptions, and Account.
2. Confirm customer navigation does not show `Create Site`.
3. Confirm Dashboard `View progress` or `Continue setup` opens Subscriptions.
4. Confirm the Dashboard Subscription count card opens Subscriptions.
5. Confirm Site and Ready count cards are informational and do not navigate.
6. Open Subscriptions and confirm the Plan catalog CTA is `Add New Subscription`.
7. Provision or reuse a customer that has exhausted the Free Plan limits.
8. Open Plans and confirm Free remains visible but disabled with a limit message.
9. Confirm attempting to request the exhausted Plan through the API is rejected or returns the existing Subscription without creating another Site.
10. Confirm customer screens still hide Bench, Database Server, Runtime Namespace, Kubernetes, CR names, Secrets, action logs, pod logs, kubeconfig, and raw operator resource names.
