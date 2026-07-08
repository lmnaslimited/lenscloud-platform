# E2E Incident Follow-Up Prompt - LC-E2E-20260708-001

Work inside `/workspace/frappe-bench/apps/lenscloud`.

Read first:
- `AGENTS.md`
- `docs/architecture/e2e-incident-management.md`
- `docs/incidents/e2e-incident-tracker.md`
- `docs/handoffs/platform/e2e-incident-followup-template.md`

Incident:
Platform cluster gate RBAC contract mismatch during `Validate cluster gates`.

Owner: Platform
Severity: High
Scenario: Platform cluster gate validation
Status: Open

Evidence references:
- Infra host-side RBAC verification: `lenscloud-infra/scripts/54-verify-platform-access.sh` and `lenscloud-infra/scripts/55-verify-platform-lifecycle.sh` passed on the manager host.
- Platform gate output: `negative-rbac` / `positive-rbac` mismatch against the same restricted kubeconfig.
- Pending evidence file: `docs/evidence/customer-launch/<to-add>.md`

Expected result:
- Platform `Validate cluster gates` should accept the Infra restricted access contract and pass RBAC preflight when Infra verification passes.
- Protected operations remain denied, and runtime namespace operations permitted by contract remain allowed.

Actual result:
- Platform RBAC preflight expected a denied `get pods` permission in `lenscloud-runtime-eu`, while Infra RBAC contract permits `list pods` and `delete pods` only.
- As a result, `Validate cluster gates` failed even though Infra host-side RBAC validation was successful.

Safe reproduction steps:
1. Confirm the restricted kubeconfig from Infra is mounted as `file:/run/secrets/lenscloud-eu-test.kubeconfig` in Platform.
2. Open the Cluster record for `lenscloud-eu-test` and run `Validate cluster gates`.
3. Capture the full gate output JSON and note the exact RBAC check failure.
4. Compare with the Infra host-side script `lenscloud-infra/scripts/54-verify-platform-access.sh` expected permissions.

Implementation / contract boundary:
- Platform owns its Python Kubernetes client preflight and gate validation logic.
- Infra owns the restricted kubeconfig generation, service account RBAC, namespace labels, admission policy, and host-side verification scripts.
- This incident is a Platform-owned contract alignment issue, not an Infra runtime RBAC failure.

Retest plan:
1. Apply the Platform code change that aligns `check_cluster_permissions` with the Infra RBAC contract.
2. Re-run `Validate cluster gates` in the Platform UI for `lenscloud-eu-test`.
3. Confirm the gate output shows both `positive-rbac` and `negative-rbac` passing.
4. Confirm Infra scripts `54-verify-platform-access.sh` and `55-verify-platform-lifecycle.sh` still pass with the same kubeconfig, then attach evidence.

Closure checklist:
- [ ] Update Platform RBAC gate code and unit tests.
- [ ] Re-run Platform `Validate cluster gates` successfully.
- [ ] Add dated evidence file and link the incident ID.
- [ ] Update `docs/incidents/e2e-incident-tracker.md` with status and closure evidence.
- [ ] Update `docs/platform-workitems.md` if this changes acceptance or launch status.
- [ ] Resume from the next unpassed E2E scenario after closure.
