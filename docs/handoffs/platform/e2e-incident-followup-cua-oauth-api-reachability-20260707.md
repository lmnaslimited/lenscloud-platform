# E2E Incident Follow-Up: CUA OAuth API Reachability - 2026-07-07

Incident: `LC-E2E-20260707-001`

## Context

Platform has implemented the INF-022 OAuth Bench Command path, but live `oauth.status` against the kept Site failed before ConfigMap creation because the Platform devcontainer could not connect to the Kubernetes API server.

Action log: `ORCH-2026-00224`

Kept Site for resume:

```text
Site: run-20260706-cua-134515.cloud.lmnaslens.com
Bench: run-20260702-free-prod-bench
Namespace: lenscloud-runtime-eu
Customer: CUST004
Subscription: SUB-00002
```

## Recovery Owner

Infra/operator restores Kubernetes API/firewall reachability for the restricted Platform kubeconfig. Platform resumes verification after that.

## Resume Steps

1. Confirm `/run/secrets/lenscloud-eu.kubeconfig` remains mounted read-only and server-side only.
2. Confirm Platform can reach the Kubernetes API from the devcontainer.
3. Rerun focused backend tests:

```text
bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command
```

4. Rerun `oauth.status` for the kept Site.
5. If `oauth.status` succeeds, run `configure_site_oauth` for the kept Site.
6. Verify action logs show sanitized display/result summaries.
7. Verify cleanup removed Job, ConfigMap, terminal command Pod, and the short-lived OAuth Secret.
8. Keep the Site for INF-023 user/site-access work unless the operator explicitly approves cleanup.
9. Update `docs/evidence/customer-launch/cua-oauth-runner-20260707.md`.
10. Move `LC-E2E-20260707-001` to Closed only after live `oauth.status` and `oauth.configure` pass.

## Safety

- Do not print kubeconfig, tokens, OAuth client secret, Kubernetes Secret values, pod logs, or private keys.
- Do not mutate `default/frappe-mariadb`.
- Do not delete the kept Site.

## 2026-07-07 Retest Update

Firewall authorization was restored. `oauth.status` succeeded on the kept Site as action log `ORCH-2026-00225` and returned `Social login: Missing`. Cleanup removed the command Job, ConfigMap, and terminal Pod.

Remaining closure steps:

1. Run `lenscloud.api.bench_command.configure_site_oauth` on the kept Site.
2. Verify the result is sanitized and no secret appears in API response/action log.
3. Verify cleanup removed Job, ConfigMap, terminal Pod, and short-lived OAuth Secret.
4. Run final `oauth.status` and confirm Social Login is configured/enabled as expected.
5. Close `LC-E2E-20260707-001`.

