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

Complete. Platform may adapt OAuth.

Infra has implemented and locally verified:

- `oauth.status`
- `oauth.configure`

Infra applied the admission update and recorded live verification with:

```text
lenscloud-infra/scripts/65-verify-cua-oauth-runner.sh
```

Published runner image:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner:v0.1.10
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:e003d3f49a1225ccc37df1147bc7f2d1ca704518b90575fc5ad4c4af4ffc7741
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

The target Site must have a valid Frappe Fernet-compatible `encryption_key` in
`site_config.json`. `oauth.configure` writes `Social Login Key.client_secret`,
which is a Password field. If the Site encryption key is invalid, Frappe rejects
the write.

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

## Live Evidence

Live proof passed on 2026-07-07:

```text
CUA OAuth runner verification passed.
Runtime namespace: lenscloud-runtime-eu
Bench: run-20260702-free-prod-bench
Site: run-20260702-free-site.cloud.lmnaslens.com
Sites PVC: run-20260702-free-prod-bench-sites
Positive commands: oauth.status, oauth.configure
Negative checks: direct client_secret arg rejected; non-oauth Secret volume denied
Temporary resource prefix: run-20260707-cua-oauth
```

Cleanup proof:

- no Jobs, ConfigMaps, Secrets, or Pods remained for
  `run-20260707-cua-oauth`;
- diagnostic prefixes `run-20260707-cua-oauth-debug` and
  `run-20260707-cua-oauth-rootcause` were clean;
- the verifier-created target Site `Social Login Key`
  `lenscloud_oauth_smoke` was removed after evidence capture;
- target Bench, Site, and sites PVC remained Ready/Bound;
- restricted Platform RBAC verification passed after the OAuth run.

## Platform Next Step

Platform may now implement OAuth through this Bench Command path.

Platform should:

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

- `INF-023` user/access runner gate;
- `INF-024` full CUA E2E handoff.
