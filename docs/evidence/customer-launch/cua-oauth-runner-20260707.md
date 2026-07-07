# CUA OAuth Runner Platform Evidence - 2026-07-07

## Scope

Platform consumes INF-022 OAuth runner commands through the existing Python Kubernetes API Bench Command path:

- `oauth.status`
- `oauth.configure`

User/site-access commands remain Unsupported for INF-023:

- `user.ensure`
- `user.disable`
- `user.roles.set`
- `site_access.status`

## Target Site

Use the kept setup-runner Site from the 2026-07-06 pass:

```text
Site: run-20260706-cua-134515.cloud.lmnaslens.com
Bench: run-20260702-free-prod-bench
Namespace: lenscloud-runtime-eu
Customer: CUST004
Subscription: SUB-00002
```

## Implementation Status

Platform implementation is in place for INF-022:

- runner digest updated to `sha256:e003d3f49a1225ccc37df1147bc7f2d1ca704518b90575fc5ad4c4af4ffc7741`;
- `oauth.status` and `oauth.configure` are runner-supported commands;
- `oauth.configure` rejects direct `client_secret` args;
- Platform creates/reuses a Frappe `OAuth Client` per Site;
- request ConfigMap carries only non-secret Social Login Key fields;
- OAuth client secret is passed only through a short-lived Kubernetes Secret mounted read-only at `/lenscloud/secrets/client_secret`;
- cleanup removes Job, ConfigMap, terminal command Pod, and the short-lived Secret after result capture.

## Test Evidence

```text
bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command
Result: 26 tests passed.
```

```text
bench --site dev.localhost migrate
Result: passed; Platform Settings OAuth fields synced.
```

```text
npm --prefix apps/lenscloud/frontend run build
Result: passed; production assets rebuilt after adding the dedicated Configure OAuth Site action and oauth.status command option.
```

## Live Verification Attempt

`oauth.status` was attempted against the kept Site on 2026-07-07. It failed before ConfigMap creation because Platform could not connect to the Kubernetes API server.

```text
Action log: ORCH-2026-00224
Incident: LC-E2E-20260707-001
Failure: Kubernetes API connection timeout to 116.203.22.81:6443 before ConfigMap creation.
Next action: Restore API/firewall authorization and rerun from docs/handoffs/platform/e2e-incident-followup-cua-oauth-api-reachability-20260707.md.
```

No OAuth client secret, Kubernetes Secret value, kubeconfig, token, private key, pod log, or full environment dump was recorded. The kept Site was not deleted.
## Live `oauth.status` Retest After Firewall Authorization

Retest date: 2026-07-07

```text
Command: oauth.status
Site: run-20260706-cua-134515.cloud.lmnaslens.com
Action log: ORCH-2026-00225
Command ID: BCMD-2026-00225
Cluster: lenscloud-eu-dev
Namespace: lenscloud-runtime-eu
Result: Succeeded
Display: Social login: Missing
Secret values returned: false
Cleanup removed:
- jobs/lenscloud-runtime-eu/bcmd-2026-00225-job
- configmaps/lenscloud-runtime-eu/bcmd-2026-00225-request
- pods/lenscloud-runtime-eu/bcmd-2026-00225-job-jg5mg
```

This confirms live `oauth.status` reaches the target Site through the Bench Command runner and returns a sanitized pre-configured state. No OAuth client secret, Kubernetes Secret value, kubeconfig, token, private key, pod log, or full environment dump was recorded.

`LC-E2E-20260707-001` can move to Fixed Pending Retest for the `oauth.status` portion. Full closure still requires `oauth.configure` to pass and prove short-lived Secret cleanup.

## Live `oauth.configure` Attempt

Retest date: 2026-07-07

```text
Command: oauth.configure
Site: run-20260706-cua-134515.cloud.lmnaslens.com
Action log: ORCH-2026-00226
Command ID: BCMD-2026-00226
Cluster: lenscloud-eu-dev
Namespace: lenscloud-runtime-eu
Result: Failed
Summary: phase: Failed; code: RUNNER_FAILED; summary: oauth command failed with sanitized error
Secret values returned: false
Cleanup removed:
- jobs/lenscloud-runtime-eu/bcmd-2026-00226-job
- configmaps/lenscloud-runtime-eu/bcmd-2026-00226-request
- pods/lenscloud-runtime-eu/bcmd-2026-00226-job-c69r7
- secrets/lenscloud-runtime-eu/bcmd-2026-00226-oauth-secret
```

Platform action-log manifest for `ORCH-2026-00226` shows the expected INF-022 shape: request ConfigMap contains non-secret OAuth fields, `client_secret_source` is `mounted_file`, the Job has exactly the read-only `oauth-client-secret` mount at `/lenscloud/secrets`, and the recorded Secret body is redacted. The runner returned only the sanitized generic failure code `RUNNER_FAILED`, so Platform cannot safely infer the root cause without Infra runner evidence.

## Final Status After Failed Configure

```text
Command: oauth.status
Action log: ORCH-2026-00227
Result: Succeeded
Display: Social login: Missing
Cleanup removed:
- jobs/lenscloud-runtime-eu/bcmd-2026-00227-job
- configmaps/lenscloud-runtime-eu/bcmd-2026-00227-request
- pods/lenscloud-runtime-eu/bcmd-2026-00227-job-5pskt
```

Incident `LC-E2E-20260707-001` is closed for API reachability after `oauth.status` passed. New incident `LC-E2E-20260707-002` tracks the `oauth.configure` runner failure.

