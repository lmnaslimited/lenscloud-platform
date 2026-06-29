# Bench Command Real Site Runner Verification SOP

## Purpose

Use this SOP to independently verify, as a Platform operator, that LensCloud Platform can run the Infra Bench Command runner against a real Frappe Operator Bench/Site and record secret-safe evidence.

This SOP verifies the same gate recorded in:

```text
docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md
```

The positive live evidence from Platform is:

```text
bench_test.status: ORCH-2026-00156 -> Succeeded
maintenance_mode.status: ORCH-2026-00159 -> Succeeded
Infra revision for real sites path fix: 328846b
runner image digest: sha256:3c322afc631b7db49759059c6706a3f42668cfbf5017ee66b3f4c26d9235c49e
```

## Safety Rules

1. Do not expose kubeconfig contents, tokens, passwords, Secret values, DB passwords, private keys, pod logs, raw `site_config.json`, or full environment dumps.
2. Keep `Platform Settings.kubernetes_apply_enabled` disabled. Bench Command verification creates its own temporary command Job/ConfigMap through the Python Kubernetes API and does not require enabling lifecycle apply.
3. Use only non-destructive commands for this verification:
   - `bench_test.status`
   - `maintenance_mode.status`
4. Do not run `maintenance_mode.enable`, `maintenance_mode.disable`, `developer_mode.enable`, `site_config.set`, `site_config.unset`, or `cors.allowlist.update` unless a separate approved maintenance window exists.
5. Do not mutate or delete `MariaDB/default/frappe-mariadb`.
6. Do not use `kubectl` from the Platform devcontainer.

## Prerequisites

You need a LensCloud Platform user with `System Manager` access.

Confirm these records exist and are Ready:

```text
Bench: run-20260629-free-prod-bench
Site: run-20260629-free-prod-site.cloud.lmnaslens.com
Customer: CUST001
Subscription: SUB-00001
Runtime namespace: lenscloud-runtime-eu
```

If these records were cleaned up, first create a new Free Plan public Prod Bench/Site using the full lifecycle SOP, then substitute that Bench/Site name in the steps below.

## 1. Confirm Apply Is Disabled

1. Open Platform.
2. Go to `/lenscloud/platform/settings`.
3. Confirm `Kubernetes apply enabled` is off.

Expected result:

```text
Apply is disabled before starting Bench Command verification.
```

If apply is enabled, disable it before continuing.

## 2. Confirm The Site Is Ready

1. Open `/lenscloud/platform/sites`.
2. Filter `name` equals:

```text
run-20260629-free-prod-site.cloud.lmnaslens.com
```

3. Select the Site row.
4. Confirm the inspector header clearly shows you are editing/reviewing that Site.
5. Confirm these fields, or equivalent status fields, show Ready/healthy state:
   - Site status: `Ready`
   - Provisioning status: `Ready` or complete
   - Route/HTTPS status: `Ready`
   - Bench: `run-20260629-free-prod-bench`
   - Environment: `Prod`
   - Subscription: `SUB-00001`

Expected result:

```text
The selected Site is the real Platform-managed Free Plan Prod Site and is Ready.
```

Stop if the selected record is different from the intended Site.

## 3. Run The Harmless Contract Smoke

1. With the Site selected, open the `Actions` tab.
2. Choose `Run Site Control command`.
3. Enter:

```text
Command: bench_test.status
Args: {}
Timeout seconds: 120
Reason: Operator verification of Bench Command contract smoke
```

4. Run the action.

Expected result:

```text
status: Succeeded
command: bench_test.status
secret_values_returned: false
cleanup includes one Job and one ConfigMap
```

Record the returned action log ID, for example:

```text
ORCH-2026-_____
```

## 4. Run The Real Runner Status Check

1. Stay on the same selected Site.
2. Open `Actions`.
3. Choose `Run Site Control command`.
4. Enter:

```text
Command: maintenance_mode.status
Args: {}
Timeout seconds: 120
Reason: Operator verification of real Bench/Site runner path
```

5. Run the action.

Expected result:

```text
status: Succeeded
command: maintenance_mode.status
summary: Read maintenance_mode status
layout: frappe-sites
changed: false
redacted: true
secret_values_returned: false
cleanup includes one Job and one ConfigMap
```

For the 2026-06-29 proof, the successful action log was:

```text
ORCH-2026-00159
```

A correct result proves Platform can mount the real Bench sites PVC at the contracted path and the runner can locate the real Frappe Operator site layout without exposing file contents.

## 5. Inspect The Action Log Evidence

1. Open `/lenscloud/platform/orchestration-logs`.
2. Filter `name` equals the action log from Step 4.
3. Open the log.
4. Confirm:
   - Status is `Succeeded`.
   - Operation is `maintenance_mode.status`.
   - Message says the command finished with phase `Succeeded`.
   - Cleanup removed two resources.
   - Manifest shows a ConfigMap request and one Job only.
   - Job image uses the pinned runner digest:

```text
sha256:3c322afc631b7db49759059c6706a3f42668cfbf5017ee66b3f4c26d9235c49e
```

5. Confirm the manifest shape:

```text
ConfigMap key: request.json
Job label: lenscloud.io/resource-kind=bench-command
Job label: lenscloud.io/managed-by=platform
service account token: disabled
request mount: /lenscloud/request
sites PVC mount: /home/frappe/frappe-bench/sites
Secret mounts: none
```

Do not copy or expose kubeconfig material, Secret data, DB passwords, pod logs, or site config contents.

## 6. Verify Unsupported Command Behavior

This proves Platform is not pretending unfinished runner families are implemented.

1. Open the same Site.
2. Run `Run Site Control command` with:

```text
Command: backup.create
Args: {}
Timeout seconds: 120
Reason: Operator verification that backup remains unsupported until runner contract exists
```

Expected result:

```text
status: Unsupported
code: COMMAND_UNSUPPORTED
message says the command is contracted but unsupported by the current runner/API
```

For the 2026-06-29 proof, the action log was:

```text
ORCH-2026-00158
```

No command Job should be created for unsupported runner-pending commands.

## 7. Optional Server-Side Cleanup Proof

Use this only if you want cluster-level absence proof from the Platform backend. This still uses the Platform Python Kubernetes API, not `kubectl`.

From `/workspace/frappe-bench`, replace the label value with the command ID from your action result, lowercased. Example for `BCMD-2026-00159`:

```sh
bench --site dev.localhost execute "(lambda o,frappe: (lambda cluster: (lambda client: {'jobs':[item.get('metadata',{}).get('name') for item in client.list_namespaced('jobs','lenscloud-runtime-eu',label_selector='lenscloud.io/resource-id=bcmd-2026-00159',group='batch',version='v1')], 'configmaps':[item.get('metadata',{}).get('name') for item in client.list_namespaced('configmaps','lenscloud-runtime-eu',label_selector='lenscloud.io/resource-id=bcmd-2026-00159')], 'closed': (client.close() or True)})(o.get_cluster_client(cluster)))(frappe.get_doc('Cluster','lenscloud-eu-dev')))(__import__('lenscloud.api.orchestration', fromlist=['get_cluster_client']), frappe)"
```

Expected result:

```json
{"jobs": [], "configmaps": [], "closed": true}
```

If a Job or ConfigMap remains, do not delete anything manually from the cluster. Open the action log, confirm the exact command resource names, and use the Platform cleanup/remediation path or hand the exact resource IDs to the Platform agent.

## 8. Optional Backend Regression Test

This verifies the Platform code contract, not the live cluster path.

From `/workspace/frappe-bench`:

```sh
bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command
```

Expected result:

```text
Ran 11 tests
OK
```

This test confirms the secret-safe manifest shape, supported/unsupported command matrix, typed argument validation, timeout bounds, and next-action guidance.

## Pass Criteria

The verification passes only when all are true:

- selected Site is Ready and belongs to the expected Bench/Subscription;
- `bench_test.status` succeeds;
- `maintenance_mode.status` succeeds;
- termination summary is sanitized and redacted;
- action log manifest uses the pinned runner digest;
- no Secret mount, service-account token, pod log, kubeconfig, DB password, or site config content is exposed;
- cleanup removes the command Job and request ConfigMap;
- optional cluster label query returns no remaining Job or ConfigMap;
- `backup.create` or another runner-pending command returns `Unsupported / COMMAND_UNSUPPORTED`.

## Failures And Next Actions

| Failure | What it means | Next action |
| --- | --- | --- |
| Site is not Ready | Real target is not suitable for runner verification | Run Site status sync and inspect runtime before retrying |
| API timeout | Platform devcontainer cannot reach Kubernetes API | Ask the host operator to refresh the Infra API authorization watcher |
| 403 / Forbidden | RBAC/admission contract does not allow the operation | Ask Infra to verify Platform restricted access for the runtime namespace |
| `TARGET_NOT_FOUND` / `site_config.json` | Runner cannot see the real Site layout | Confirm Infra revision `328846b` or newer and the pinned runner digest |
| Unsupported for `backup.create` | Expected current behavior | Wait for Infra to implement remaining runner families |
| Cleanup did not remove resources | Temporary command resources remain | Do not delete manually; use exact Job/ConfigMap names for Platform remediation |

## Evidence To Record

Record these in the evidence document or test notes:

```text
Date/time:
Operator:
Platform revision:
Infra revision:
Site:
Bench:
Runtime namespace:
bench_test.status action log:
maintenance_mode.status action log:
Unsupported command action log:
Cleanup proof:
Secrets exposed: No
Apply enabled during test: No
Remaining gaps: backup, restore, bench_test.trigger, LATP
```
