# Platform And Customer E2E Acceptance Evidence - 2026-07-02

## Scope

Pre-final Free-first E2E acceptance covering Platform operator readiness, Customer Plan/Subscription flow, controlled real Site provisioning, retry behavior, HTTPS/static asset proof, cleanup, and incident tracking.

## Safety Baseline

- Do not expose kubeconfig, tokens, passwords, Secret values, private keys, pod logs, or full environment dumps.
- Preserve `default/frappe-mariadb` and all cluster infrastructure.
- Clean only Platform-owned test Sites, Benches, Database Servers, Subscriptions, Customers, Orchestration Action Logs, and related transactional records.
- Kubernetes apply must be enabled only during the controlled live provisioning window.

## Scenario Matrix

| Scenario ID | Segment | Scenario | Expected Result | Status | Evidence | Incident |
| --- | --- | --- | --- | --- | --- | --- |
| PLAT-001 | Platform | Preflight, focused tests, apply gate | Apply is controlled and focused backend tests pass | Pass | `python3 -m py_compile lenscloud/api/bench_command.py lenscloud/api/test_bench_command.py`; `bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command` passed 19 tests; apply disabled after live window |  |
| PLAT-002 | Platform | Runtime baseline after Infra PVC fix | Old 2026-06-29 Bench/Site/PVC state is absent | Pass | Infra `1bfc57c`; Platform inventory `ORCH-2026-00188` | LC-E2E-20260702-002 closed |
| PLAT-003 | Platform | Free Bench capacity | One fresh shared Free Bench reaches Ready in `lenscloud-runtime-eu` | Pass | `run-20260702-free-prod-bench`; reconcile `ORCH-2026-00189`; sync `ORCH-2026-00190`/`ORCH-2026-00191` |  |
| CUST-001 | Customer | Free Plan subscription and Site request | Customer gets approved Subscription and Prod Site without choosing runtime internals | Pass | `CUST001`; `SUB-00001` Approved; Site Request `ORCH-2026-00192` |  |
| LIVE-001 | Runtime | Real Site provisioning | FrappeSite accepted by Kubernetes API and reaches Ready | Pass | Site reconcile `ORCH-2026-00193`; status sync Ready `ORCH-2026-00199` |  |
| LIVE-002 | Runtime | HTTPS/static asset | Site HTTPS route and generated static asset return success | Pass | `https://run-20260702-free-site.cloud.lmnaslens.com`; route `200`; asset `200`; `ORCH-2026-00199` |  |
| LIVE-003 | Runtime | Secret-safe runtime inventory | Platform can inspect runtime without Secret values | Pass | `ORCH-2026-00200` collected Site inventory without Secret values |  |
| LIVE-004 | Runtime | Bench Command result and cleanup | Result should be captured and command Job/ConfigMap/terminal pods cleaned or verified absent | Pass | Existing terminal pods cleaned by guarded Platform cleanup; fresh `bench_test.status` succeeded in `ORCH-2026-00206`; command Job, ConfigMap, and terminal pod removed | LC-E2E-20260702-003 closed |
| SAFE-001 | Runtime safety | Protected baseline MariaDB | `default/frappe-mariadb` remains untouched | Pass | No Platform mutation was made to `default/frappe-mariadb`; shared DB remained the selected protected baseline |  |
| AUTO-001 | Automated | Migration, build, backend tests | Release-candidate gates pass | Pass | `bench --site dev.localhost migrate`; `npm --prefix frontend run build`; `test_plan_catalog` 6 passed; `test_policy` 15 passed; `test_bench_command` 20 passed |  |
| AUTO-002 | Automated | Authenticated Platform/customer desktop | Platform and customer routes pass without unexpected console/page errors | Pass | `LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth` passed |  |
| AUTO-003 | Automated | Authenticated Platform/customer mobile | Mobile navigation and Details drawer pass | Pass | `LENSCLOUD_VIEWPORT=mobile ... npm --prefix frontend run test:auth` passed |  |
| UX-001 | Customer UX | Subscribed customer dashboard visual check | Ready/subscribed dashboard shows customer-safe Open Site state | Pass | `node frontend/tests/customer-dashboard-visual.mjs`; desktop/mobile subscribed screenshots captured; errors `0` |  |
| UX-002 | Customer UX | Plan catalog visual and entitlement state | Plans come from Platform records; Tier 4 hidden; default Free first on mobile; exhausted Free entitlement is not startable | Pass | `node frontend/tests/customer-plans-visual.mjs`; desktop/mobile plan screenshots captured; setup/review capture skipped because test user already has Free Subscription |  |
| UX-003 | Customer UX | Account and Subscription actions, signout/password, and label casing sanity | Pass | Incident `LC-E2E-20260703-002` closed; build passed; authenticated desktop/mobile Playwright passed with action navigation assertions; no forced `uppercase`/tracking classes remain in Vue files | LC-E2E-20260703-002 |
| UX-004 | Customer UX | Account widget and in-page password dialog | Account click opens a floating widget; Sign Out is in the widget; Change Password opens an Account-page dialog without leaving the workspace | Pass | Incident `LC-E2E-20260703-003` closed; build passed; authenticated desktop/mobile Playwright passed with account-widget and password-dialog assertions; forced all-caps scan returned no Vue matches | LC-E2E-20260703-003 |
| REC-001 | Recovery | Incident recovery mechanism | Incidents carry executable follow-up prompt and closure/resume checklist | Pass | `docs/architecture/e2e-incident-management.md`; `docs/operator-sop/platform-customer-e2e-acceptance.md`; `docs/handoffs/platform/e2e-incident-followup-template.md`; tracker schema updated |  |
| SIGNUP-001 | Customer Identity | Native signup creates or links Customer identity and routes by role | Pass | `bench --site dev.localhost run-tests --module lenscloud.api.test_customer_identity` passed 6 tests on 2026-07-03; authenticated desktop/mobile route smoke passed; Customer Member visible in Platform |  |
| SIGNUP-002 | Customer Identity | Additional signup, legacy blank-domain Customer, and login home route | Pass | Incident `LC-E2E-20260703-001` closed; `test_customer_identity` passed 9 tests; customer users route to `/lenscloud/customer/dashboard`; Customer Members sidebar row verified; `user2@example.com` correctly created separate `CUST002` because `CUST001.primary_domain` is blank | LC-E2E-20260703-001 |

## Incident Register

Canonical tracker: `docs/incidents/e2e-incident-tracker.md`. Recovery process: every future incident must link a follow-up prompt under `docs/handoffs/platform/` or `docs/handoffs/infra/` and resume from the next unpassed scenario after closure.

- `LC-E2E-20260702-001`: customer paused/dry-run retry gap, closed by fresh live Free Plan launch retest.
- `LC-E2E-20260702-002`: old PVC cleanup blocker, closed after Infra `1bfc57c` and Platform runtime inventory verification.
- `LC-E2E-20260702-003`: Bench Command terminal pod cleanup RBAC, closed after Infra `e2a5483` and Platform retest `ORCH-2026-00206`.

## Reset And Launch Inventory

After reset and fresh launch:

- Customers: 1 (`CUST001`)
- Subscriptions: 1 (`SUB-00001`, status `Approved`, Plan `Free`, Region `EU`, next renewal `2026-08-02`, frequency `Monthly`)
- Sites: 1 (`run-20260702-free-site.cloud.lmnaslens.com`, provisioning `Ready`, route `Ready`)
- Benches: 1 (`run-20260702-free-prod-bench`, namespace `lenscloud-runtime-eu`)
- Database Servers: 1 protected baseline (`EU Shared MariaDB 01`, runtime `default/frappe-mariadb`)
- Orchestration Action Logs after reset/fresh run and INF-019 retest: 18

## Runtime Evidence

- Old PVC/PV from `LC-E2E-20260702-002`: Infra evidence says both are `NotFound`; Platform inventory `ORCH-2026-00188` verified the old Bench owner and related runtime resources absent.
- Fresh Bench: `run-20260702-free-prod-bench`; reconcile accepted `ORCH-2026-00189`; Ready sync `ORCH-2026-00190`/`ORCH-2026-00191`.
- Fresh Site: `run-20260702-free-site.cloud.lmnaslens.com`; request `ORCH-2026-00192`; reconcile accepted `ORCH-2026-00193`; Ready/HTTPS/static asset proof `ORCH-2026-00199`; inventory `ORCH-2026-00200`.
- Bench Command cleanup before INF-019: `ORCH-2026-00201`, `ORCH-2026-00202`, `ORCH-2026-00203`, and `ORCH-2026-00204` failed only at terminal pod deletion. After Infra `e2a5483`, guarded Platform cleanup deleted six terminal Platform-labelled command pods. `ORCH-2026-00205` hit a transient Kubernetes API read timeout during verification, then `ORCH-2026-00206` succeeded and removed the fresh Job, ConfigMap, and terminal command pod.

## Test Results

- Bench Command backend syntax: `python3 -m py_compile lenscloud/api/bench_command.py lenscloud/api/test_bench_command.py` passed.
- Bench Command backend tests: `bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command` passed, 19 tests.
- Live Free provisioning: passed through real Kubernetes apply and reached HTTPS/static-asset Ready.
- Live Bench Command cleanup verification: passed after Infra `e2a5483`; Platform deletes Job/ConfigMap first, waits for pod garbage collection, deletes only terminal Platform-labelled Bench Command pods, and verifies absence.
- Final reset-clean inventory: no Platform-labelled Bench Command Pods, Jobs, or ConfigMaps; PVCs `run-20260702-free-prod-bench-sites` and `storage-run-iron-monkey-life-db-0` are `Bound` with no deletion timestamp.
- Apply gate: `kubernetes_apply_enabled=0` after the controlled live window.
- Customer signup identity gate: native Frappe signup creates a LensCloud Customer plus active Owner membership; second same-domain signup creates Pending Customer Member; public email creates individual Customer; Platform/System users are not auto-converted.

## Remaining SOP Coverage Notes

The Free-first launch path, runtime cleanup, policy tests, and authenticated customer/platform journeys are now covered. The current credential set has an existing Free Subscription, so setup/review visual screenshots are not recaptured in a fresh no-subscription state during this resumed run. The entitlement behavior itself passed: Free is not startable again for the subscribed customer. A future visual-only pass can use a clean customer identity if design wants fresh setup/review screenshots without consuming the live launch customer.

The broader paid/beta and multi-tier topology live matrix remains intentionally outside the Free-first launch gate until those Plans and approval/payment paths are activated.

## 2026-07-03 Signup Incident Retest

`LC-E2E-20260703-001` clarified the additional signup flow. `CUST001` is a legacy Customer without `primary_domain`, so `user2@example.com` was not eligible for same-domain pending membership under `CUST001`; Platform correctly created `CUST002` with an Active Owner membership. The confusing signup popup was Frappe account/email verification copy, not LensCloud Customer Member approval. Platform now documents this distinction, routes customer Website Users to `/lenscloud/customer/dashboard` instead of `/me`, and exposes Customer Members under Customers and Commerce.


## 2026-07-03 Account Widget Retest

`LC-E2E-20260703-003` closed the account action placement gap. The shell account affordance now opens a floating widget with Profile, Change Password, and Sign Out. Change Password routes to `/customer/account?changePassword=1` and opens a compact Account-page dialog backed by Frappe's native password update API, so the user does not leave the Account workspace. Retest passed with production frontend build and authenticated desktop/mobile Playwright.

## Go/No-Go

Free Plan customer launch E2E is passing for subscription, Site creation, HTTPS, static asset, customer-safe provisioning state, and Bench Command cleanup. No remaining launch blocker is known from this pass.

## 2026-07-03 Customer RBAC/Menu Retest

Incident `LC-E2E-20260703-004` is closed. Platform repaired customer access so native Frappe Role Profiles and DocType permissions drive customer menus and actions. The legacy `Customer.user` owner path now receives Customer User Permission and the configured/conventional Customer Admin Role Profile before permissions are calculated. Customer APIs remain scoped to the active membership or legacy Customer owner if User Permission is missing.

Validation:

- `bench --site dev.localhost run-tests --module lenscloud.api.test_customer_identity` passed 10 tests.
- `npm --prefix frontend run build` passed.
- `LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth` passed.
- `LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth` passed.
- Authenticated browser probe for `iron_monkey_private@example.com` returned Plan, Subscription, Site, and Customer Member permissions from the server and the customer sidebar showed Dashboard, Plans, Subscriptions, and Members. No secrets or passwords were printed.

## 2026-07-03 Password Dialog Editability Retest

Incident `LC-E2E-20260703-003` was reopened after user retest showed the Change Password dialog opened but its password fields were not editable. Platform replaced the password entry surfaces with deterministic native modal markup in both Customer Account and Platform shell contexts. The validation was tightened so tests type into fields and assert accepted DOM values, rather than only checking that the dialog opens.

Validation:

- `npm --prefix frontend run build` passed.
- Targeted customer browser probe opened `/lenscloud/customer/account?changePassword=1`, filled Current Password, New Password, and Confirm New Password, and verified all three values.
- Targeted platform browser probe opened the Platform account widget, filled all three password fields, and verified all three values while staying inside Platform.
- `LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth` passed for authenticated Platform desktop and Customer flow with field-value assertions.
- No real password values, tokens, or secrets were printed.
