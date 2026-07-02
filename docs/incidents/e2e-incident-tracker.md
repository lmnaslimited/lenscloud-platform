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

| Incident ID | Date | Scenario | Severity | Scope | Owner | Status | Symptom | Evidence | Fix / Next Action | Retest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LC-E2E-20260702-001 | 2026-07-02 | CUST-005/CUST-006 | High | Customer/Runtime | Platform | Fixed Pending Retest | Customer provisioning could end as dry run without a customer-safe retry path for the already reserved Site. | `acme.cloud.lmnaslens.com`; `ORCH-2026-00174` Site Request succeeded; `ORCH-2026-00175` Site Reconcile dry-run; evidence: `docs/evidence/customer-launch/e2e-acceptance-20260702.md`. | Customer retry API and paused/failed provisioning UI implemented; backend regression, build, desktop Playwright, and mobile Playwright passed. | Pending live retry after `LC-E2E-20260702-002` is resolved. |
| LC-E2E-20260702-002 | 2026-07-02 | LIVE-003 | High | Runtime | Infra | Open | Bench CR deletion completed, but `run-20260629-free-prod-bench-sites` PVC remains terminating with `kubernetes.io/pvc-protection`; Platform record remains `Deleting` and cleanup cannot be declared clean. | `ORCH-2026-00184` delete accepted; `ORCH-2026-00187` runtime inventory shows owner absent but PVC still present/deletionTimestamp set; Infra handoff: `docs/handoffs/infra/e2e-cleanup-pvc-blocker-20260702.md`. | Infra to inspect why PVC protection finalizer has not cleared; Platform must not remove finalizers manually. | Pending Infra resolution and Platform rerun of cleanup/runtime inventory. |

## Closed Incidents

None yet.

## Operating Rule

Every failed E2E scenario must add or update a row here before the next major test segment starts. Dated evidence files should link to these incident IDs rather than becoming the tracker themselves.
