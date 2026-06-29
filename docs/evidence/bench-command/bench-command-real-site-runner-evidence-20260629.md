# Bench Command Real Site Runner Evidence - 2026-06-29

## Scope

Prove the Infra production Bench Command runner from Platform against a real Platform-managed Ready Bench and Ready Site before starting the full lifecycle/privacy/topology acceptance matrix. The first run used Infra `f3d8057`; the successful real sites path retry used Infra `328846b`.

This evidence is non-secret. Do not record kubeconfig contents, tokens, passwords, Kubernetes Secret values, DB passwords, private keys, pod logs, raw backup content, or full environment dumps.

## Required Positive Path

Run in order:

1. Select or create one real Platform-managed Ready Bench and Ready Site.
2. Confirm the Bench runs in an approved Runtime Namespace.
3. Run `bench_test.status` as the harmless contract smoke.
4. Run one non-destructive runner-backed command, preferably `maintenance_mode.status`.
5. Confirm the Job uses the pinned runner image and the expected Bench sites PVC mount.
6. Confirm sanitized termination summary is present.
7. Confirm temporary Job and ConfigMap are deleted.
8. Confirm no Secret values, pod logs, kubeconfig material, private keys, or DB passwords are exposed.

## Current Precheck

Control-plane query on 2026-06-29:

```text
Ready Sites: []
Ready Benches: []
```

Result:

```text
No real Ready Bench/Site target is currently available for live runner acceptance.
```

## Next Action

Create one temporary real Bench and Site through the normal Platform lifecycle path, wait until both are Ready, then run the positive path above.

Recommended first live command:

```json
{
  "command": "maintenance_mode.status",
  "args": {},
  "timeout_seconds": 90,
  "reason": "Real Bench/Site runner acceptance before full lifecycle matrix"
}
```

After successful evidence is recorded, hand Infra the remaining runner-family request for backup, restore, Bench Test trigger, and LATP.
## Attempt 1 - 2026-06-29

Intent:

- Create one temporary Free Plan Public Prod Bench: `run-20260629-free-prod-bench`.
- Reconcile the Bench with Kubernetes apply enabled only for the controlled window.
- Request a Free Plan Prod Site through `request_customer_site`.
- Run `bench_test.status` and `maintenance_mode.status` against the real Site.

Result:

```text
status: blocked before Bench creation completed
action_log: ORCH-2026-00138
failure: Kubernetes API connect timeout to 116.203.22.81:6443 while applying FrappeBench
apply flag: restored to disabled
site created: no
subscription created: no
customer created: no
control-plane temporary Bench: cleaned
```

The timeout happened before the FrappeBench resource was accepted by Kubernetes. A follow-up namespace ConfigMap list also timed out, confirming API reachability/firewall authorization is stale from the devcontainer.

Next action before retry:

```bash
cd /Users/arunkumar.ganesan/lensk8s/lenscloud-infra
./scripts/52-authorize-platform-api.sh --watch
```

After the Platform devcontainer can list resources in `lenscloud-runtime-eu`, rerun the same real Free Plan Bench/Site runner acceptance.

## Attempt 2 - 2026-06-29

API reachability was restored and the real Free Plan path was retried.

Control-plane and lifecycle result:

```text
apply original: disabled
apply window: enabled only for the run
apply restored: disabled
Bench: run-20260629-free-prod-bench
Bench action log: ORCH-2026-00139
Bench status sync: ORCH-2026-00140 -> Ready
Site: run-20260629-free-prod-site.cloud.lmnaslens.com
Site request action log: ORCH-2026-00141
Site reconcile action log: ORCH-2026-00142
Site final sync action log: ORCH-2026-00155 -> Ready / HTTPS Ready
Customer: CUST001
Subscription: SUB-00001
Plan: Free
Environment: Prod
```

HTTPS/static asset evidence:

```text
URL: https://run-20260629-free-prod-site.cloud.lmnaslens.com/
page status: 200
static asset: /assets/frappe/dist/css/website.bundle.D4ZWF75O.css
asset status: 200
```

Bench Command smoke:

```text
command: bench_test.status
action log: ORCH-2026-00156
status: Succeeded
summary: Bench Test status contract check completed
cleanup: jobs/lenscloud-runtime-eu/bcmd-2026-00156-job, configmaps/lenscloud-runtime-eu/bcmd-2026-00156-request
post-cleanup verification: job_count=0, configmap_count=0
```

Real runner command:

```text
command: maintenance_mode.status
action log: ORCH-2026-00157
status: Failed
code: TARGET_NOT_FOUND
summary: site_config.json was not found
cleanup: jobs/lenscloud-runtime-eu/bcmd-2026-00157-job, configmaps/lenscloud-runtime-eu/bcmd-2026-00157-request
post-cleanup verification: job_count=0, configmap_count=0
```

Unsupported command behavior:

```text
command: backup.create
action log: ORCH-2026-00158
status: Unsupported
code: COMMAND_UNSUPPORTED
```

Runtime PVC evidence:

```text
PVC: lenscloud-runtime-eu/run-20260629-free-prod-bench-sites
phase: Bound
storageClassName: local-path
requested: 3Gi
```

Current conclusion:

```text
Free Plan, self-approved Subscription, public Prod Bench, public Prod Site, HTTPS route, static asset, and bench_test.status smoke passed.
The production runner reached the real target but could not find site_config.json on the mounted Bench sites PVC/path.
This is now an Infra runner mount/path contract gap, not a Platform policy or API reachability gap.
```

Current cleanup state:

```text
Temporary Bench/Site/Customer/Subscription remain present for follow-up inspection.
Kubernetes apply is disabled.
Temporary Bench Command Jobs and ConfigMaps are cleaned.
```

Next action:

Ask Infra to verify how the production runner should mount or locate the real Bench Site directory and `site_config.json` for Frappe Operator-created Benches. Infra must not expose file contents, Secrets, DB passwords, pod logs, or environment dumps while proving the path.

## Attempt 3 - 2026-06-29

Infra revision `328846b` was pulled in the adjacent read-only `lenscloud-infra` checkout. The updated handoff keeps the Platform mount path unchanged and fixes the production runner to support the real Frappe Operator layout:

```text
sites PVC mount: /home/frappe/frappe-bench/sites
BENCH_PATH: /home/frappe/frappe-bench
observed layout: frappe-sites/<site>/site_config.json
runner image: ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:3c322afc631b7db49759059c6706a3f42668cfbf5017ee66b3f4c26d9235c49e
```

Platform updated the pinned runner digest and retried the non-destructive real runner command against the existing Free Plan target:

```text
command: maintenance_mode.status
action log: ORCH-2026-00159
command id: BCMD-2026-00159
namespace: lenscloud-runtime-eu
bench: run-20260629-free-prod-bench
site: run-20260629-free-prod-site.cloud.lmnaslens.com
status: Succeeded
summary: Read maintenance_mode status
layout: frappe-sites
maintenance_mode value: 0
changed: false
redacted: true
secret_values_returned: false
```

Stored Platform manifest evidence for `ORCH-2026-00159` shows:

```text
ConfigMap: bcmd-2026-00159-request
Job: bcmd-2026-00159-job
resource label: lenscloud.io/resource-id=bcmd-2026-00159
image digest: sha256:3c322afc631b7db49759059c6706a3f42668cfbf5017ee66b3f4c26d9235c49e
request mount: /lenscloud/request
sites PVC: run-20260629-free-prod-bench-sites
sites mount: /home/frappe/frappe-bench/sites
service account token: disabled
Secret mounts: none
pod logs read by Platform: no
```

Cleanup evidence:

```text
initial cleanup: jobs/lenscloud-runtime-eu/bcmd-2026-00159-job, configmaps/lenscloud-runtime-eu/bcmd-2026-00159-request
post-cleanup label query jobs: []
post-cleanup label query configmaps: []
```

Conclusion:

```text
Live real Bench Command runner acceptance is complete for the current supported positive paths: bench_test.status and maintenance_mode.status.
The Free Plan public Prod Bench/Site remains present for operator inspection unless a later cleanup pass retires it through Platform lifecycle APIs.
Kubernetes apply remains disabled.
Backup, restore, Bench Test trigger, and LATP remain Unsupported until Infra provides those runner contracts.
```

## Attempt 4 - Result Display Contract - 2026-06-29

Infra revision `405e0c1` was checked out in the adjacent read-only `lenscloud-infra` reference. Platform consumed the sanitized result display contract from:

```text
docs/handoffs/platform/bench-command-result-display-contract-20260629.md
/workspace/lenscloud-infra/docs/platform-bench-command-handoff.md
/workspace/lenscloud-infra/docs/bench-command-result-display-evidence-20260629.md
```

Platform updated the pinned Bench Command runner image to:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:ab69e3ff24584e268bfa92f44c5d71e680ce1780cc8a4a9a5ce1e60b3e4bf4e7
```

Live verification against the existing Free Plan target:

```text
command: maintenance_mode.status
action log: ORCH-2026-00161
command id: BCMD-2026-00161
namespace: lenscloud-runtime-eu
bench: run-20260629-free-prod-bench
site: run-20260629-free-prod-site.cloud.lmnaslens.com
status: Succeeded
summary: Read maintenance_mode status
display.label: Maintenance mode
display.value: Off
display.kind: boolean
display.safe: true
display_text: Maintenance mode: Off
redacted: true
secret_values_returned: false
```

Action log evidence:

```text
ORCH-2026-00161 status: Succeeded
operation: maintenance_mode.status
message: Bench Command maintenance_mode.status finished with phase Succeeded; cleanup removed 2 resource(s). Result: Maintenance mode: Off.
```

Authenticated UI proof:

```text
Playwright: npm --prefix frontend run test:bench-command-display
result: passed
latest browser-driven action log: ORCH-2026-00165
message: Bench Command maintenance_mode.status finished with phase Succeeded; cleanup removed 2 resource(s). Result: Maintenance mode: Off.
visible UI card: Bench Command result -> Maintenance mode: Off
secret-like text in result card: absent
post-cleanup label query jobs: []
post-cleanup label query configmaps: []
```

Cleanup proof:

```text
initial cleanup: jobs/lenscloud-runtime-eu/bcmd-2026-00161-job, configmaps/lenscloud-runtime-eu/bcmd-2026-00161-request
post-cleanup label query jobs: []
post-cleanup label query configmaps: []
```

Conclusion:

```text
Bench Command result display contract is complete for Platform consumption.
The backend returns safe display/display_text only when display.safe is true.
The Platform action result card renders the safe result separately from raw JSON.
Unsupported and failed commands fall back to sanitized phase/code/summary and do not render unsafe details.value.
Backup, restore, bench_test.trigger, and LATP remain runner-pending/Unsupported.
```

