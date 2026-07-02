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
| LC-E2E-20260702-003 | 2026-07-02 | LIVE-004 | High | Runtime/RBAC | Infra | Open | Bench Command result capture succeeds, Job/ConfigMap cleanup succeeds, but terminal command pods remain and Platform is forbidden to delete pods in `lenscloud-runtime-eu`. Terminal pods can keep Bench sites PVCs protected during reset. | `ORCH-2026-00201`, `ORCH-2026-00202`, `ORCH-2026-00203`; final inventory shows five `Succeeded` `bcmd-*` pods and no command Jobs/ConfigMaps; evidence: `docs/evidence/customer-launch/e2e-acceptance-20260702.md`; Infra handoff: `docs/handoffs/infra/e2e-bench-command-pod-cleanup-rbac-20260702.md`. | Infra to add/confirm narrowly scoped terminal Bench Command pod cleanup permission/admission for the Platform service account, or provide an alternate runner cleanup contract. Platform must not remove PVC finalizers manually. | Pending Infra fix and Platform rerun of `bench_test.status` cleanup verification. |

## Closed Incidents

| Incident ID | Date Closed | Resolution Evidence | Retest |
| --- | --- | --- | --- |
| LC-E2E-20260702-002 | 2026-07-02 | Infra `1bfc57c` evidence: `lenscloud-infra/docs/e2e-cleanup-pvc-blocker-evidence-20260702.md`; Platform runtime inventory `ORCH-2026-00188` verified old Bench owner and related PVC/PV absent. | Closed after Platform verified `run-20260629-free-prod-bench` owner and related runtime resources absent. |
| LC-E2E-20260702-001 | 2026-07-02 | Fresh Free Plan flow created a real Site with apply enabled: `SUB-00001`, `run-20260702-free-site.cloud.lmnaslens.com`, reconcile `ORCH-2026-00193`, Ready/HTTPS/static asset proof `ORCH-2026-00199`. | Closed by fresh launch retest; exact old dry-run Site retry is no longer required for the reset baseline. |

## Operating Rule

Every failed E2E scenario must add or update a row here before the next major test segment starts. Dated evidence files should link to these incident IDs rather than becoming the tracker themselves.
