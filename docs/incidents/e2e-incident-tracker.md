# E2E Incident Tracker

This is the canonical incident tracker for Platform/customer E2E acceptance. Evidence files may reference incident IDs, but the current incident status lives here.

## Status Values

- `Open`: reported and not yet fixed.
- `In Progress`: owner is actively working the fix.
- `Fixed Pending Retest`: fix exists, but acceptance retest is not complete.
- `Closed`: fix and retest evidence are complete.
- `Deferred`: accepted as non-blocking with a follow-up workitem.

## Severity Values

- `Critical`: launch cannot proceed.
- `High`: launch is risky or live E2E is blocked.
- `Medium`: acceptance can continue with a documented workaround.
- `Low`: polish or documentation cleanup.

## Active Incidents

| Incident ID | Date | Scenario | Severity | Scope | Owner | Status | Symptom | Evidence | Follow-Up Prompt | Fix / Next Action | Retest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Closed Incidents

| Incident ID | Date Closed | Resolution Evidence | Retest |
| --- | --- | --- | --- |
| LC-E2E-20260703-003 | 2026-07-03 | Reopened after user retest found Change Password fields were not editable. Replaced fragile Frappe UI Dialog usage with deterministic native modal markup for customer and platform password entry while keeping Account actions in the shell widget. Playwright now types into all three password fields and verifies values instead of only asserting the dialog opens. | `npm --prefix frontend run build` passed; targeted customer and platform browser probes filled Current Password, New Password, and Confirm New Password; authenticated desktop Playwright passed with input-value assertions. |
| LC-E2E-20260703-004 | 2026-07-03 | Customer access now uses configured or conventional Customer Role Profiles, creates/repairs Customer User Permission, falls back to legacy `Customer.user` safely, filters customer sidebar by native DocType read permission, gates Subscription creation by native create permission, exposes a permission-driven Members approval page, keeps Platform password change inside Platform, and themes account widget copy/avatar. | `test_customer_identity` passed 10 tests; `npm --prefix frontend run build` passed; authenticated desktop and mobile Playwright passed; browser probe confirmed Plans, Subscriptions, and Members appear from server DocType permissions. |
| LC-E2E-20260703-002 | 2026-07-03 | Account header exposed native Change Password and Sign Out, removed noisy Linked/Refresh actions, used clean single-row action links, Subscription Plan actions became explicit RouterLinks, and forced all-caps/tracking classes were removed from SPA Vue surfaces. Superseded for action placement by `LC-E2E-20260703-003`. | `npm --prefix frontend run build` passed; authenticated desktop/mobile Playwright passed with Account/Subscription action navigation assertions; forced all-caps scan returned no Vue matches. |
| LC-E2E-20260703-001 | 2026-07-03 | Platform home-page hook routes customer users to `lenscloud/customer/dashboard`; Workspace Sidebar fixture/model includes Customer Members; architecture documents that Frappe admin-verification copy is not Customer Member approval and legacy blank-domain Customers do not capture same-domain signups. | `test_customer_identity` passed 9 tests; `bench --site dev.localhost migrate` passed; frontend build and authenticated desktop/mobile route smoke passed; sidebar DB row verified. |
| LC-E2E-20260702-003 | 2026-07-02 | Infra `e2a5483` evidence: `lenscloud-infra/docs/bench-command-pod-cleanup-rbac-evidence-20260702.md`; Platform guarded cleanup deleted existing terminal command pods; fresh `bench_test.status` `ORCH-2026-00206` succeeded and removed Job, ConfigMap, and terminal pod. | Closed after final inventory showed no Platform-labelled Bench Command Pods, Jobs, or ConfigMaps in `lenscloud-runtime-eu`; Bench sites PVCs were Bound with no deletion timestamp. |
| LC-E2E-20260702-002 | 2026-07-02 | Infra `1bfc57c` evidence: `lenscloud-infra/docs/e2e-cleanup-pvc-blocker-evidence-20260702.md`; Platform runtime inventory `ORCH-2026-00188` verified old Bench owner and related PVC/PV absent. | Closed after Platform verified `run-20260629-free-prod-bench` owner and related runtime resources absent. |
| LC-E2E-20260702-001 | 2026-07-02 | Fresh Free Plan flow created a real Site with apply enabled: `SUB-00001`, `run-20260702-free-site.cloud.lmnaslens.com`, reconcile `ORCH-2026-00193`, Ready/HTTPS/static asset proof `ORCH-2026-00199`. | Closed by fresh launch retest; exact old dry-run Site retry is no longer required for the reset baseline. |

## Operating Rule

Every failed E2E scenario must add or update a row here before the next major test segment starts. Dated evidence files should link to these incident IDs rather than becoming the tracker themselves.

Every active incident must link a follow-up prompt. The prompt is mandatory recovery scaffolding: it tells the next Platform or Infra agent exactly how to reproduce, fix, retest, close, and then resume the E2E matrix from the next unpassed row. Closed incidents may keep the prompt reference in the evidence file instead of the closed table.
