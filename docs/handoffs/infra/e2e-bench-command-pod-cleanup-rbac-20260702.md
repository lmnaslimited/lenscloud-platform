# Infra Handoff - Bench Command Terminal Pod Cleanup RBAC - 2026-07-02

## Summary

Platform completed the final Free Plan live E2E launch path, but Bench Command cleanup is blocked at terminal pod removal. The updated Platform cleanup now deletes the command Job and ConfigMap first, waits for Kubernetes garbage collection, then verifies/removes terminal command pods. The restricted Platform service account is currently forbidden to delete pods in `lenscloud-runtime-eu`.

## Platform Evidence

- Site: `run-20260702-free-site.cloud.lmnaslens.com`
- Subscription: `SUB-00001`
- Bench: `run-20260702-free-prod-bench`
- Site Ready/HTTPS/static asset proof: `ORCH-2026-00199`
- Runtime inventory proof without Secret values: `ORCH-2026-00200`
- Bench Command cleanup failures: `ORCH-2026-00201`, `ORCH-2026-00202`, `ORCH-2026-00203`
- Final command cleanup inventory: command Jobs `[]`, command ConfigMaps `[]`, terminal command pods remain.

## Remaining Runtime Objects

The following Platform-labelled Bench Command pods are `Succeeded` and remain in `lenscloud-runtime-eu`:

- `bcmd-2026-00137-job-5pnxl`
- `bcmd-2026-00156-job-9kv4d`
- `bcmd-2026-00201-job-pdw5r`
- `bcmd-2026-00202-job-s2tpd`
- `bcmd-2026-00203-job-5kfxd`

No Bench Command Jobs or request ConfigMaps remain after Platform exact cleanup.

## Request For Infra

Please update INF-010/Bench Command RBAC and admission so the Platform service account can clean up only terminal Platform-labelled Bench Command pods in approved runtime namespaces, or provide an alternate runner cleanup contract that guarantees these pods are removed after result capture.

The permission should remain narrow:

- namespace-scoped runtime namespaces only;
- Platform-labelled Bench Command pods only, enforced by admission/policy where Kubernetes RBAC cannot express label selectors;
- no pod log read permission;
- no Secret read/list permission;
- no access to `default/frappe-mariadb` or cluster infrastructure.

## Safety Boundary

Do not ask Platform operators to remove PVC finalizers manually. Do not mutate `default/frappe-mariadb`. Do not broaden Platform into namespace or cluster infrastructure ownership.

## Platform Follow-Up

After Infra publishes the fix, Platform will rerun `bench_test.status` against the Free Plan Site and verify:

1. sanitized result capture;
2. Job absence;
3. ConfigMap absence;
4. terminal command pod absence;
5. no stuck Bench sites PVC protection during cleanup.

Tracked as `LC-E2E-20260702-003` in `docs/incidents/e2e-incident-tracker.md`.
