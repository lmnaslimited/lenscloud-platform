# Bench Command Platform Evidence - 2026-06-25

## Scope

Implement the Platform consumer side of Infra INF-010 Bench Command Job/API for Site Control runtime enforcement.

Infra reference pulled:

- repo: `/workspace/lenscloud-infra`
- revision: `dcd94d8`
- handoff: `docs/platform-bench-command-handoff.md`
- evidence: `docs/bench-command-job-evidence-20260625.md`

## Platform Implementation

Files added or changed for this pass:

- `lenscloud/api/bench_command.py`
- `lenscloud/api/kubernetes_client.py`
- `lenscloud/lenscloud/doctype/orchestration_action_log/orchestration_action_log.json`
- `frontend/src/lib/catalog.js`
- `lenscloud/api/test_bench_command.py`

The Platform implementation:

- resolves and validates Site, Bench, Cluster, Runtime Namespace, Subscription, and Environment policy;
- validates command allowlist, typed args, and timeout;
- creates the request ConfigMap and labelled Job through the Python Kubernetes API only;
- watches Job and Pod status;
- parses sanitized termination summary;
- records Orchestration Action Log evidence;
- deletes the command Job and request ConfigMap after terminal state and evidence capture;
- returns `Unsupported` for contracted commands whose runner/API implementation is pending;
- never uses `kubectl`;
- never returns kubeconfig, token, Secret values, DB passwords, private keys, pod logs, or full env dumps.

## Supported Path

The first supported positive contract path is:

```text
bench_test.status
```

Example Platform request body:

```json
{
  "site": "example.cloud.lmnaslens.com",
  "command": "bench_test.status",
  "args": {"mode": "status"},
  "timeout_seconds": 60,
  "reason": "Verify Site Control command contract"
}
```

Platform-generated Bench Command request shape:

```json
{
  "apiVersion": "lenscloud.io/v1",
  "kind": "BenchCommand",
  "command": "bench_test.status",
  "target": {
    "cluster": "lenscloud-eu-dev",
    "namespace": "lenscloud-runtime-eu",
    "bench": "<bench-runtime-name>",
    "site": "<site-name>"
  },
  "args": {"mode": "status"},
  "timeoutSeconds": 60
}
```

The actual action log stores only sanitized evidence.

## Unsupported Behavior

Contracted but runner-pending commands return:

```json
{
  "status": "Unsupported",
  "code": "COMMAND_UNSUPPORTED"
}
```

Examples include production execution for backup, restore, maintenance mode, developer mode, site config, CORS, Bench Test trigger, and LATP trigger/status until Infra/operator publishes the runner support.

## Live Smoke Attempts

Infra INF-010 is complete at revision `dcd94d8`; the Infra evidence says:

- `scripts/54-verify-platform-access.sh` passed;
- `scripts/58-verify-platform-bench-command.sh` passed;
- positive `bench_test.status` contract Job completed;
- temporary Job and ConfigMap were cleaned;
- negative RBAC/admission proof passed for unlabelled Jobs, Secret volumes, Secret listing, pod logs, default namespace mutation, and unapproved namespace mutation.

Platform first attempted live `bench_test.status` through the Python Kubernetes API before the firewall was refreshed.

Result:

- action log: `ORCH-2026-00135`;
- status: `Failed`;
- failure point: ConfigMap creation in `lenscloud-runtime-eu`;
- sanitized failure: connection timeout to Kubernetes API `116.203.22.81:6443`;
- no kubeconfig, token, Secret, DB password, private key, pod log, or full environment dump was exposed.

Because the timeout happened before ConfigMap creation completed, Platform did not receive live Job/ConfigMap creation or cleanup proof from this attempt.

Post-firewall cleanup verification for the failed attempt:

```text
resource_id=bcmd-2026-00135
job_count=0
configmap_count=0
```

After the firewall update, Platform retried the live `bench_test.status` smoke through the Python Kubernetes API.

Result:

- action log: `ORCH-2026-00137`;
- status: `Succeeded`;
- command id: `BCMD-2026-00137`;
- request ConfigMap: `lenscloud-runtime-eu/bcmd-2026-00137-request`;
- Job: `lenscloud-runtime-eu/bcmd-2026-00137-job`;
- sanitized summary: `Bench Test status contract check completed`;
- changed: `false`;
- redacted: `true`;
- `secret_values_returned`: `false`.

Cleanup returned:

```text
jobs/lenscloud-runtime-eu/bcmd-2026-00137-job
configmaps/lenscloud-runtime-eu/bcmd-2026-00137-request
```

Post-cleanup Kubernetes API verification:

```text
job_count=0
configmap_count=0
```

Temporary control-plane cleanup check:

- smoke Site prefix `run-20260625-platform-bcmd%`: no records remained;
- smoke Bench prefix `run-20260625-platform-bcmd%`: no records remained;
- smoke Customer `Bench Command`: no records remained.

Unsupported-command behavior was also exercised:

- action log: `ORCH-2026-00136`;
- status: `Unsupported`;
- expected code: `COMMAND_UNSUPPORTED`;
- behavior: Platform reports runner-pending commands truthfully and does not invent FrappeSite CR fields.

Next action:

```text
Confirm the Kubernetes API is reachable from the Platform devcontainer and the host-side API authorization watcher is current, then retry. If the operator network changed, ask Infra to run ./scripts/52-authorize-platform-api.sh --watch from the lenscloud-infra host checkout.
```

## Validation

Completed:

- `bench --site dev.localhost migrate`
- `bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command`
- `bench --site dev.localhost run-tests --module lenscloud.api.test_policy`
- `npm --prefix apps/lenscloud/frontend run build`

Note: one parallel test run hit a transient Frappe `tabSingles` concurrency error while two test processes initialized at the same time. The policy suite passed when rerun serially.

## Remaining Gaps

- Production bench-command runner image/API is pending.
- Only `bench_test.status` is implemented as the positive live Platform path.
- Authenticated browser proof for the new Site action remains pending.
