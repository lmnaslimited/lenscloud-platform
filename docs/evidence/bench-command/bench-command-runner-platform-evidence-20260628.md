# Bench Command Runner Platform Evidence - 2026-06-28

## Scope

Integrate Infra revision `f3d8057` Bench Command production runner support into LensCloud Platform Site Control command execution.

Infra references read:

- `/workspace/lenscloud-infra/docs/infra-workitems.md`
- `/workspace/lenscloud-infra/docs/platform-bench-command-handoff.md`
- `/workspace/lenscloud-infra/docs/bench-command-production-runner-evidence-20260627.md`

No kubeconfig, token, password, Kubernetes Secret value, DB password, private key, pod log, raw backup content, or full environment dump is recorded here.

## Infra Contract State

Infra `INF-011` is complete at revision `f3d8057`.

The production runner image is admission-pinned:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:c3e0922ca034c840ebd06c29b52794fec54c655b62444df60393f2ed5501d920
```

Infra live-verified the runner for `maintenance_mode.enable`. Local/source verification covers maintenance mode, developer mode, approved `site_config` keys, and CORS allowlist behavior. Platform still treats backup, restore, Bench Test trigger, and LATP as runner-pending.

## Platform Implementation

Files changed:

- `lenscloud/api/bench_command.py`
- `lenscloud/api/policy.py`
- `lenscloud/api/test_bench_command.py`
- `lenscloud/api/test_policy.py`
- `frontend/src/lib/catalog.js`
- `docs/platform-workitems.md`
- `docs/handoffs/platform/agent-handoff.md`
- `docs/architecture/product-topology-model.md`

Platform now:

- keeps `bench_test.status` as the harmless verification smoke path;
- enables runner-backed `maintenance_mode.*`, `developer_mode.*`, `site_config.*`, and `cors.allowlist.*` commands;
- keeps `backup.*`, `restore.*`, `bench_test.trigger`, and `latp.*` returning `Unsupported / COMMAND_UNSUPPORTED`;
- validates command args before creating Kubernetes resources;
- validates Site Control Profile policy from the Subscription/Environment snapshot;
- uses the pinned runner image for runner-backed Jobs;
- mounts the request ConfigMap and the expected Bench sites PVC at `/home/frappe/frappe-bench/sites`;
- preserves the secret-safe Job shape: no service-account token, no envFrom, no Secret volumes, one container, `restartPolicy: Never`;
- records sanitized action-log evidence and cleans temporary Job/ConfigMap after terminal state.

## Supported Commands

Runner-backed in Platform:

```text
maintenance_mode.enable
maintenance_mode.disable
maintenance_mode.status
developer_mode.enable
developer_mode.disable
developer_mode.status
site_config.set
site_config.unset
site_config.get
cors.allowlist.update
cors.allowlist.get
```

Verification-only:

```text
bench_test.status
```

Still unsupported until Infra runner contracts are built:

```text
backup.create
backup.status
restore.preview
restore.execute
restore.status
bench_test.trigger
latp.trigger
latp.status
```

## Request Examples

Maintenance mode:

```json
{
  "command": "maintenance_mode.enable",
  "args": {},
  "timeout_seconds": 90
}
```

Approved site config:

```json
{
  "command": "site_config.set",
  "args": {"key": "server_script_enabled", "value": 1},
  "timeout_seconds": 90
}
```

CORS allowlist:

```json
{
  "command": "cors.allowlist.update",
  "args": {"origins": ["https://example.com"]},
  "timeout_seconds": 90
}
```

Unsupported example:

```json
{
  "command": "backup.create",
  "args": {},
  "status": "Unsupported",
  "code": "COMMAND_UNSUPPORTED"
}
```

## Validation

Completed in Platform after the integration:

```text
bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command
bench --site dev.localhost run-tests --module lenscloud.api.test_policy
npm --prefix frontend run build
git diff --check
```

Results:

```text
bench command tests: 10/10 passed
policy tests: 14/14 passed
frontend production build: passed
whitespace check: passed
```

The frontend build emitted the existing Vite large-chunk warning. No live runner-backed mutation was executed in this pass; the next live acceptance should run against a real ready Site whose Bench sites PVC follows the documented `<bench operator_resource_name>-sites` mount contract.

## Remaining Gaps

- Live Platform acceptance for each runner-backed command must run against a real Site with the expected Bench sites PVC.
- The exact PVC naming/mount contract is implemented as `<bench operator_resource_name>-sites`, matching current live evidence; if Infra changes this, the handoff contract must be updated.
- Backup, restore, Bench Test trigger, and LATP production runner contracts remain pending.
- Authenticated browser coverage for the expanded command choices remains pending in this pass.
