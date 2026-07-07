# Platform Handoff - CUA OAuth Configure Failure Follow-Up - 2026-07-07

## Infra Workitem

`INF-025` CUA OAuth configure runner failure follow-up.

## Status

Infra diagnosis is complete.

`INF-022` remains complete. The OAuth runner contract is still valid and
Platform does not need to change the `oauth.configure` request shape.

## Source Paths

Infra evidence:

```text
lenscloud-infra/docs/evidence/cua/oauth-configure-runner-failed-20260707.md
```

Infra source handoff:

```text
lenscloud-infra/docs/handoffs/platform/cua-oauth-configure-runner-failed-20260707.md
```

Platform incident source:

```text
apps/lenscloud/docs/handoffs/infra/cua-oauth-configure-runner-failed-20260707.md
```

## Target

```text
namespace: lenscloud-runtime-eu
bench: run-20260702-free-prod-bench
site: run-20260706-cua-134515.cloud.lmnaslens.com
frappesite: run-20260706-cua-134515
```

## Root Cause

The kept CUA Site has an invalid Frappe `encryption_key` shape in
`site_config.json`.

Non-secret evidence:

```text
has_encryption_key: true
encryption_key_length: 48
base64_decoded_length: 36
```

Expected Frappe/Fernet shape:

```text
encryption_key_length: 44
base64_decoded_length: 32
```

`oauth.configure` writes `Social Login Key.client_secret`, a Frappe Password
field. Frappe rejects the write when the Site encryption key is invalid.

Sanitized diagnostic:

```text
ValidationError Encryption key is in invalid format!
```

## Platform Request Shape

No change is required.

The failed command used the correct shape:

- non-secret OAuth args in ConfigMap;
- `client_secret_source=mounted_file`;
- short-lived OAuth Secret mounted read-only at `/lenscloud/secrets`;
- `LENS_COMMAND_OAUTH_CLIENT_SECRET_PATH=/lenscloud/secrets/client_secret`;
- pinned OAuth runner digest;
- cleanup of Job, ConfigMap, terminal Pod, and short-lived OAuth Secret.

## Platform Next Action

Do not repeatedly retry `oauth.configure` against the kept Site until the Site
is repaired or recreated.

Recommended Platform behavior:

1. Treat invalid target Site encryption-key shape as a repair/recreate condition
   before OAuth configure.
2. Prefer recreating the CUA test Site with a valid generated encryption key.
3. If the operator explicitly approves repair of the kept throwaway Site, retry
   the same `oauth.configure` request after repair.

The kept Site has at least one encrypted `User.password` row, so key repair may
require password reset or other cleanup. Infra intentionally did not repair it
without explicit operator approval.

## Go/No-Go

- Go: Platform may continue adapting OAuth through the existing runner contract.
- Go: Platform may retry unchanged on a healthy Site.
- No-Go: Do not treat `RUNNER_FAILED` on this kept Site as an OAuth request
  schema issue.

No OAuth client secret, Kubernetes Secret value, kubeconfig, token, private key,
or password value was exposed.
