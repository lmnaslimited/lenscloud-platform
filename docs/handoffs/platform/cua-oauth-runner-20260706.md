# Platform Handoff - CUA OAuth Runner - 2026-07-06

## Source

Infra source handoff:

```text
lenscloud-infra/docs/handoffs/platform/cua-oauth-runner-handoff-20260706.md
```

Infra evidence:

```text
lenscloud-infra/docs/evidence/cua/oauth-runner-evidence-20260706.md
```

Infra workitem:

```text
INF-022 CUA OAuth runner gate
```

## Status

Ready for Infra live verification, not yet Platform-enabled.

Infra has implemented and locally verified:

- `oauth.status`
- `oauth.configure`

Platform must not enable OAuth commands in customer workflows until Infra
applies the admission update and records live verification with:

```text
lenscloud-infra/scripts/65-verify-cua-oauth-runner.sh
```

Published runner image:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner:v0.1.9
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:31973edd01e9c6ea75f2a3b4ef323d5ff643fcec97b2d49b6da9d9d10b7f7580
```

## Ownership Boundary

Platform owns the Platform-side `OAuth Client`.

Infra runner owns only the target Site `Social Login Key`.

Platform should create/maintain the OAuth Client and pass non-secret target
Social Login Key fields to the Bench Command runner.

## Secret Boundary

`oauth.status` does not need a Secret mount.

`oauth.configure` requires the OAuth client secret as a short-lived Kubernetes
Secret mounted read-only at:

```text
/lenscloud/secrets/client_secret
```

The request ConfigMap must set:

```json
{"client_secret_source":"mounted_file"}
```

The request ConfigMap must never include `client_secret`.

## Request Args For `oauth.configure`

```json
{
  "provider": "nectar",
  "provider_name": "Nectar",
  "social_login_provider": "Custom",
  "enable_social_login": true,
  "client_id": "platform-oauth-client-id",
  "client_secret_source": "mounted_file",
  "base_url": "https://nectar.lmnas.com",
  "authorize_url": "/api/method/frappe.integrations.oauth2.authorize",
  "access_token_url": "/api/method/frappe.integrations.oauth2.get_token",
  "redirect_url": "https://customer.cloud.lmnaslens.com/api/method/frappe.integrations.oauth2_logins.custom/nectar",
  "api_endpoint": "/api/method/frappe.integrations.oauth2.openid_profile",
  "custom_base_url": true,
  "auth_url_data": {
    "response_type": "code",
    "scope": "openid"
  },
  "sign_ups": ""
}
```

## Platform Next Step

Do not enable OAuth as a live customer workflow yet.

Platform may prepare code behind a feature gate, but runtime calls must stay
disabled until Infra marks `INF-022` Complete with live evidence.

When Infra completes live verification, Platform should:

1. create or select the Platform OAuth Client;
2. create a short-lived Kubernetes Secret for the target Social Login Key
   client secret;
3. create the `oauth.configure` request ConfigMap and Job through the existing
   Bench Command path;
4. parse only sanitized termination summaries;
5. clean the Job, request ConfigMap, terminal Pod, and short-lived Secret after
   evidence capture;
6. record status, result, and cleanup in Orchestration Action Log.

## Remaining Gaps

- live admission apply;
- live verifier run;
- `INF-023` user/access runner gate;
- `INF-024` full CUA E2E handoff.
