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
| PLAT-001 | Platform | Preflight, migrations, build, backend tests | All gates pass before live run | Partial Pass | `python3 -m py_compile`, frontend build, `test_plan_catalog`, desktop/mobile Playwright passed; migration pending live rerun; full policy tests passed |  |
| PLAT-002 | Platform | Product baseline: Plan, Landscape, Privacy, Site Control, Release | Free Plan resolves to Single/Prod/Public and approved Release | Pending |  |  |
| PLAT-003 | Platform | Runtime baseline: Cluster, Region, Runtime Namespace, Free Bench | One ready shared Free Bench exists in target Region | Pending |  |  |
| PLAT-004 | Platform | Permission/protection checks | Protected/default resources remain safe; no secret exposure | Pending |  |  |
| CUST-001 | Customer | No-subscription dashboard | Customer sees one clear `Choose a Plan` action | Pending |  |  |
| CUST-002 | Customer | Plan browse | Plans are first-class submitted records; hidden/exhausted Plans behave correctly | Pending |  |  |
| CUST-003 | Customer | Setup Site | Region/domain/subdomain use Platform data, no runtime choices | Pending |  |  |
| CUST-004 | Customer | Review and Free checkout | Free checkout shows zero due and no payment method required | Pending |  |  |
| CUST-005 | Customer | Paused provisioning | Apply-disabled run shows saved request and retry guidance, not fake success | Fixed Pending Retest | Backend now maps reconcile `dry_run` to `paused`; UI renders paused/retry state; existing dry-run evidence `ORCH-2026-00175` | LC-E2E-20260702-001 |
| CUST-006 | Customer | Retry provisioning | Existing reserved Site retries after controlled apply is enabled | Blocked | Retry API implemented; live retest blocked by cleanup PVC incident | LC-E2E-20260702-001, LC-E2E-20260702-002 |
| LIVE-001 | Runtime | Real Site provisioning | FrappeSite accepted by Kubernetes API and reaches ready/accessible state | Blocked | Runtime reset not clean; Free Bench deleted but PVC remains terminating | LC-E2E-20260702-002 |
| LIVE-002 | Runtime | HTTPS/static asset | Site HTTPS and static asset return success | Pending |  |  |
| LIVE-003 | Runtime | Cleanup | Test resources are removed or retained by explicit launch decision | Blocked | Bench CR absent; sites PVC still terminating | LC-E2E-20260702-002 |
| UX-001 | Customer | Mobile drawer/detail access | Required details are reachable on mobile | Pass | Authenticated mobile Playwright passed |  |
| UX-002 | Customer | No runtime internals | Customer screens hide Bench, Database Server, namespace, CR, Secret, action-log terms | Pass | Authenticated desktop/mobile Playwright passed for current customer pages |  |

## Incident Register

Canonical tracker: `docs/incidents/e2e-incident-tracker.md`.

Active incidents for this evidence file:

- `LC-E2E-20260702-001`: customer dry-run/retry gap, fixed pending live retest.
- `LC-E2E-20260702-002`: runtime cleanup PVC blocker, open for Infra.

## Cleanup Inventory

Captured before and during cleanup:

- Customers: 2 (`CUST001`, `CUST002`)
- Subscriptions: 3 (`SUB-00001`, `SUB-00002`, `SUB-00003`)
- Sites: 2 (`run-20260629-free-prod-site.cloud.lmnaslens.com` Ready, `acme.cloud.lmnaslens.com` Requested/Pending dry-run)
- Benches: 1 (`run-20260629-free-prod-bench`, Ready, namespace `lenscloud-runtime-eu`)
- Database Servers: 1 protected baseline (`EU Shared MariaDB 01`, namespace `default`, operator resource `frappe-mariadb`)
- Orchestration Action Logs: 41
- Runtime resources: `acme` FrappeSite absent; `run-20260629-free-prod-site` FrappeSite absent; `run-20260629-free-prod-bench` FrappeBench absent; `run-20260629-free-prod-bench-sites` PVC still terminating with `kubernetes.io/pvc-protection`

## Test Results

- Backend syntax: `python3 -m py_compile apps/lenscloud/lenscloud/api/orchestration.py` passed.
- Frontend build: `npm --prefix apps/lenscloud/frontend run build` passed.
- Backend focused tests: `bench --site dev.localhost run-tests --module lenscloud.api.test_plan_catalog` passed, 6 tests.
- Backend policy tests: `bench --site dev.localhost run-tests --module lenscloud.api.test_policy` passed, 15 tests.
- Authenticated Playwright desktop: `LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix apps/lenscloud/frontend run test:auth` passed.
- Authenticated Playwright mobile: `LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix apps/lenscloud/frontend run test:auth` passed.
- Live Free provisioning: blocked by `LC-E2E-20260702-002` until terminating PVC is resolved or Infra approves separate fresh capacity creation.

## Go/No-Go

Blocked for live reset/E2E until `LC-E2E-20260702-002` is resolved or Infra confirms the terminating PVC is safe/expected and new capacity can be provisioned separately.
