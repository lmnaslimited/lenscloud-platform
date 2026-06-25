# Bench Command Platform Evidence - 2026-06-25

## Scope

Implement the Platform consumer side of Infra INF-010 Bench Command Job/API for Site Control runtime enforcement.

Infra reference pulled:

- repo: `/workspace/lenscloud-infra`
- revision: `a7de2ad`
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

## Validation

Completed:

- `bench --site dev.localhost migrate`
- `bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command`
- `bench --site dev.localhost run-tests --module lenscloud.api.test_policy`
- `npm --prefix apps/lenscloud/frontend run build`

Note: one parallel test run hit a transient Frappe `tabSingles` concurrency error while two test processes initialized at the same time. The policy suite passed when rerun serially.

## Remaining Gaps

- Live command execution is pending Infra live verification/apply of INF-010 RBAC/admission.
- Production bench-command runner image/API is pending.
- Only `bench_test.status` is implemented as the positive Platform path.
- Authenticated browser proof for the new Site action remains pending.

