# Platform Follow-Up Prompt - CUA OAuth Contract Self-Heal - 2026-07-07

## Purpose

Self-heal the CUA OAuth drift introduced while adapting INF-022. The previous pass used `nectar` as if it were the Platform issuer and briefly changed customer `Open Site` links to call the target Site OAuth callback directly. That is incorrect.

Read first:

- `AGENTS.md`
- `docs/platform-workitems.md`
- `docs/architecture/customer-identity-access.md`
- `docs/architecture/cua-site-bootstrap-sso-sequence.md`
- `docs/operator-sop/platform-customer-e2e-acceptance.md`
- `docs/handoffs/platform/cua-oauth-runner-20260706.md`
- `docs/handoffs/platform/cua-oauth-configure-runner-failed-20260707.md`
- `docs/evidence/customer-launch/cua-oauth-runner-20260707.md`

## Correct Contract

LensCloud Platform is the OAuth provider and CUA authority. In local/dev, the Platform issuer/base URL is the current Platform site, normally:

```text
http://dev.localhost:8000
```

For every target Site:

- create or reuse a Platform-side `OAuth Client`;
- app name should be derived from target Site prefix and Environment, for example `<site-prefix>-<environment>`;
- redirect URI must be derived from target Site access URL:
  `<site.access_url>/api/method/frappe.integrations.oauth2_logins.custom/lenscloud`;
- target Site Social Login Key provider/key is `lenscloud`;
- provider name is `LensCloud`;
- OAuth base URL sent to the target Site is the LensCloud Platform URL;
- customer `Open Site` opens `site.access_url`, not the OAuth callback/login method directly;
- the target Site owns redirecting unauthenticated users to LensCloud Platform OAuth.

`nectar` was only an example shape reference. Do not use it as provider key, provider name, or default issuer in Platform code/docs.

## Required Code Fixes

1. Keep backend defaults:
   - `oauth_provider`: `lenscloud`
   - `oauth_provider_name`: `LensCloud`
2. Set local/dev `Platform Settings.oauth_base_url` to the current Platform URL, `http://dev.localhost:8000`, unless the operator provides a different reachable Platform URL.
3. Ensure Platform OAuth Client app name is derived from target Site prefix and Environment, not `LensCloud <provider> <site>`.
4. Ensure redirect URI is always `<site.access_url>/api/method/frappe.integrations.oauth2_logins.custom/lenscloud`.
5. Undo any customer portal behavior that makes `Open Site` prefer an OAuth callback/login URL. `Open Site` must use `site.access_url`.
6. Keep short-lived OAuth Secret mount behavior unchanged. Never put `client_secret` in request args, browser responses, logs, or evidence.
7. Keep new Site encryption-key generation Fernet-compatible.

## Retest

Run focused tests first:

```text
bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command
npm --prefix frontend run build
bench --site dev.localhost migrate
```

Then run live against the fresh Site kept for CUA, or a newly created fresh Site if the kept one is invalid:

1. `oauth.status` with provider `lenscloud`.
2. `configure_site_oauth` with the corrected Platform OAuth base URL.
3. final `oauth.status` with provider `lenscloud`.
4. verify cleanup removed Job, ConfigMap, terminal Pod, and short-lived OAuth Secret.
5. verify customer portal `Open Site` href is `site.access_url`.

Do not claim full passwordless Open Site until INF-023 user/access runner contract exists and the first Customer Owner/Admin is ensured on the target Site with an Active Site Access Grant.

## Documentation Closure

Update:

- `docs/evidence/customer-launch/cua-oauth-runner-20260707.md`
- `docs/incidents/e2e-incident-tracker.md`
- `docs/platform-workitems.md`
- `docs/handoffs/platform/agent-handoff.md`
- `docs/operator-sop/platform-customer-e2e-acceptance.md`

Close `LC-E2E-20260707-002` only after the corrected fresh-Site OAuth configure/status retest passes with sanitized evidence.
