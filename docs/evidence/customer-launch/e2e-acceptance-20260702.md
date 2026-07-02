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
| LIVE-004 | Runtime | Bench Command result and cleanup | Result should be captured and command Job/ConfigMap/terminal pods cleaned or verified absent | Partial Pass / Blocked Cleanup | `bench_test.status` result path reached terminal command pod cleanup; command Jobs/ConfigMaps are absent; terminal pods remain because Platform is denied `delete pods` | LC-E2E-20260702-003 |
| SAFE-001 | Runtime safety | Protected baseline MariaDB | `default/frappe-mariadb` remains untouched | Pass | No Platform mutation was made to `default/frappe-mariadb`; shared DB remained the selected protected baseline |  |

## Incident Register

Canonical tracker: `docs/incidents/e2e-incident-tracker.md`.

- `LC-E2E-20260702-001`: customer paused/dry-run retry gap, closed by fresh live Free Plan launch retest.
- `LC-E2E-20260702-002`: old PVC cleanup blocker, closed after Infra `1bfc57c` and Platform runtime inventory verification.
- `LC-E2E-20260702-003`: Bench Command terminal pods remain because Platform service account cannot delete pods; open for Infra RBAC/admission follow-up.

## Reset And Launch Inventory

After reset and fresh launch:

- Customers: 1 (`CUST001`)
- Subscriptions: 1 (`SUB-00001`, status `Approved`, Plan `Free`, Region `EU`, next renewal `2026-08-02`, frequency `Monthly`)
- Sites: 1 (`run-20260702-free-site.cloud.lmnaslens.com`, provisioning `Ready`, route `Ready`)
- Benches: 1 (`run-20260702-free-prod-bench`, namespace `lenscloud-runtime-eu`)
- Database Servers: 1 protected baseline (`EU Shared MariaDB 01`, runtime `default/frappe-mariadb`)
- Orchestration Action Logs after reset/fresh run: 15

## Runtime Evidence

- Old PVC/PV from `LC-E2E-20260702-002`: Infra evidence says both are `NotFound`; Platform inventory `ORCH-2026-00188` verified the old Bench owner and related runtime resources absent.
- Fresh Bench: `run-20260702-free-prod-bench`; reconcile accepted `ORCH-2026-00189`; Ready sync `ORCH-2026-00190`/`ORCH-2026-00191`.
- Fresh Site: `run-20260702-free-site.cloud.lmnaslens.com`; request `ORCH-2026-00192`; reconcile accepted `ORCH-2026-00193`; Ready/HTTPS/static asset proof `ORCH-2026-00199`; inventory `ORCH-2026-00200`.
- Bench Command cleanup: `ORCH-2026-00201`, `ORCH-2026-00202`, and `ORCH-2026-00203` failed only at terminal pod deletion. Exact final command cleanup inventory: five `Succeeded` `bcmd-*` pods remain; no command Jobs or ConfigMaps remain.

## Test Results

- Bench Command backend syntax: `python3 -m py_compile lenscloud/api/bench_command.py lenscloud/api/test_bench_command.py` passed.
- Bench Command backend tests: `bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command` passed, 19 tests.
- Live Free provisioning: passed through real Kubernetes apply and reached HTTPS/static-asset Ready.
- Live Bench Command cleanup verification: blocked at pod-delete RBAC; Platform now deletes Job/ConfigMap first, waits for pod garbage collection, then attempts/raises on terminal pod cleanup.
- Apply gate: `kubernetes_apply_enabled=0` after the controlled live window.

## Go/No-Go

Free Plan customer launch E2E is functionally passing for subscription, Site creation, HTTPS, static asset, and customer-safe provisioning state.

Reset-clean is not yet fully green because `LC-E2E-20260702-003` leaves terminal Bench Command pods in `lenscloud-runtime-eu`. Infra should clear the listed pods and update the INF-010 contract so Platform can remove or verify terminal command pods after result capture without manual PVC finalizer intervention.
