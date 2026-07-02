# Infra Handoff - E2E Cleanup PVC Blocker - 2026-07-02

## Summary

Platform began the pre-final E2E reset using Platform lifecycle APIs only. Site cleanup completed, and the old FrappeBench owner CR was deleted normally, but the Bench sites PVC remains terminating.

## Evidence

- Site `acme.cloud.lmnaslens.com`: dry-run only; runtime owner absent; Platform delete returned `deleted` in `ORCH-2026-00179`.
- Site `run-20260629-free-prod-site.cloud.lmnaslens.com`: delete accepted in `ORCH-2026-00180`; later inventory `ORCH-2026-00182`/`ORCH-2026-00183` showed owner and related resources absent; Platform Site status is `Deleted`.
- Bench `run-20260629-free-prod-bench`: delete accepted in `ORCH-2026-00184`; runtime inventory `ORCH-2026-00187` shows FrappeBench owner absent.
- Remaining runtime object: PVC `lenscloud-runtime-eu/run-20260629-free-prod-bench-sites` with `deletionTimestamp` set and finalizer `kubernetes.io/pvc-protection`.
- Warning event: `StatusUpdateFailed`, message indicates the FrappeBench CR is already not found.

## Request For Infra

Please inspect why PVC `lenscloud-runtime-eu/run-20260629-free-prod-bench-sites` remains terminating after the Bench owner CR is absent.

Do not delete or mutate `default/frappe-mariadb` or cluster infrastructure. Do not remove finalizers unless Infra determines it is the correct cluster-owner action and records evidence.

## Platform Impact

Platform cannot declare reset clean or continue live Free Plan E2E against a fresh baseline until this is resolved or Infra confirms new capacity may be created while the old terminating PVC is handled separately.

## Platform Incident

Tracked as `LC-E2E-20260702-002` in `docs/incidents/e2e-incident-tracker.md`; supporting evidence is in `docs/evidence/customer-launch/e2e-acceptance-20260702.md`.
