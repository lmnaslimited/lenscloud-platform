# Infra Handoff - CUA OAuth Configure Runner Failure - 2026-07-07

## Source Incident

`LC-E2E-20260707-002`

Platform evidence:

```text
apps/lenscloud/docs/evidence/customer-launch/cua-oauth-runner-20260707.md
```

## Context

Platform consumed INF-022 and ran live OAuth commands against the kept CUA Site.

```text
Site: run-20260706-cua-134515.cloud.lmnaslens.com
Bench: run-20260702-free-prod-bench
Namespace: lenscloud-runtime-eu
Customer: CUST004
Subscription: SUB-00002
```

`oauth.status` passed after firewall authorization:

```text
Action log: ORCH-2026-00225
Result: Social login: Missing
Cleanup: Job, ConfigMap, terminal Pod removed
```

`oauth.configure` reached the runner but failed:

```text
Action log: ORCH-2026-00226
Command ID: BCMD-2026-00226
Result: Failed
Code: RUNNER_FAILED
Summary: oauth command failed with sanitized error
Cleanup: Job, ConfigMap, terminal Pod, and short-lived OAuth Secret removed
```

Final status after failed configure:

```text
Action log: ORCH-2026-00227
Result: Social login: Missing
Cleanup: Job, ConfigMap, terminal Pod removed
```

## Platform Request Shape Observed

Platform action-log manifest for `ORCH-2026-00226` shows:

- ConfigMap args include non-secret OAuth fields only;
- `client_secret_source` is `mounted_file`;
- `base_url` is `https://nectar.lmnas.com`;
- `redirect_url` is `https://run-20260706-cua-134515.cloud.lmnaslens.com/api/method/frappe.integrations.oauth2_logins.custom/nectar`;
- Job uses runner image `ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:e003d3f49a1225ccc37df1147bc7f2d1ca704518b90575fc5ad4c4af4ffc7741`;
- Job mounts exactly one OAuth Secret volume named `oauth-client-secret` read-only at `/lenscloud/secrets`;
- env `LENS_COMMAND_OAUTH_CLIENT_SECRET_PATH=/lenscloud/secrets/client_secret` is present;
- action log redacts the Secret value.

## Ask For Infra

Please inspect runner-side evidence for `BCMD-2026-00226` without exposing Secrets to Platform.

Determine whether the failure is caused by:

1. target Site encryption key / Fernet setup;
2. runner command implementation or argument expectation mismatch;
3. target Site Social Login Key validation behavior;
4. Platform request shape needing adjustment;
5. another runtime or admission issue.

Return a handoff with:

- sanitized root cause;
- whether Platform request shape must change;
- whether the kept Site requires repair;
- exact verification command/result;
- cleanup proof for any Infra diagnostic resources;
- whether Platform should retry `configure_site_oauth` unchanged.

## Safety

- Do not expose OAuth client secret, Kubernetes Secret values, kubeconfig, tokens, private keys, or full pod logs.
- Do not delete the kept Site unless explicitly approved by the operator.
- Do not mutate `default/frappe-mariadb`.
