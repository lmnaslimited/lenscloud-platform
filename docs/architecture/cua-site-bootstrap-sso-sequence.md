# CUA Site Bootstrap And SSO Sequence

## Purpose

This is the shared Platform/Infra sequence for making LensCloud Platform the Central User Access authority for provisioned Sites. It extends `docs/architecture/customer-identity-access.md` and must not be treated as a separate backlog. The canonical workitem is `CUA Site bootstrap and SSO automation` in `docs/platform-workitems.md`.

## Design Choice

Use the Kubernetes API Bench Execute / Bench Command style. Platform creates a secret-safe request object and labelled Job through the Python Kubernetes client. Infra/operator supplies the runner wrapper inside the runtime namespace. The runner executes approved bench/site commands in the target Bench/Site context and returns a sanitized summary.

Do not make browser-visible Platform APIs call target Site HTTP APIs with Administrator credentials. Administrator passwords, OAuth client secrets, bootstrap tokens, private keys, kubeconfig contents, pod logs, raw `site_config.json`, and full environment dumps must never appear in browser responses, action logs, evidence, or docs.

## Site Setup Runner

INF-021 established that setup wizard completion does not require a special LensCloud branding/bootstrap app. The Bench Command runner uses native Frappe v16 APIs inside the target Bench/Site context:

- `frappe.is_setup_complete()`
- `frappe.core.doctype.installed_applications.installed_applications.get_setup_wizard_pending_apps()`
- `frappe.desk.page.setup_wizard.setup_wizard.setup_complete(args)`

Platform integrates only the setup-wizard slice first:

- `site_setup.status`
- `site_setup.complete`

OAuth, social login, user sync, role sync, and Site access status remain separate runner-gated slices. Prefer standard Frappe APIs for those commands first; add a branding/helper app only where standard APIs prove insufficient and the gap is documented.

## Platform Data Model

Platform adds or extends records for:

- `Site Bootstrap State`: Site, Subscription, Environment, setup wizard status, OAuth status, first user status, last action log, bootstrap version, last error, retry state.
- `Site Access Grant`: Customer, Customer Member, User, Subscription, Site, Environment, role mapping, status (`Pending`, `Syncing`, `Active`, `Failed`, `Revoked`), last sync action log, last error.
- Platform Settings OAuth fields: Platform issuer URL, OAuth client defaults, redirect URI pattern, allowed scopes, token lifetime policy, and secret reference policy.

Platform remains responsible for resolving setup inputs from Customer, Subscription, Plan, Landscape, Environment, Site Control Profile, and Customer Member records.

## OAuth Contract

LensCloud Platform is the OAuth provider and Central User Access authority.
Example names from earlier proofs, such as `nectar`, were only references for
the Frappe OAuth Client and Social Login Key shape; they are not the production
provider identity.

For each target Site, Platform must create or reuse a Platform-side
`OAuth Client` with:

- app name derived from target Site prefix and Environment, for example
  `<site-prefix>-<environment>`;
- redirect URI derived from the target Site access URL:
  `<site.access_url>/api/method/frappe.integrations.oauth2_logins.custom/lenscloud`;
- scopes required for the target Site login, currently `openid` plus Frappe
  defaults as needed;
- client ID and client secret kept server-side.

Platform then configures the target Site Social Login Key through
`oauth.configure` with:

- provider key: `lenscloud`;
- provider name: `LensCloud`;
- base URL: the LensCloud Platform URL for the current environment, such as
  `http://dev.localhost:8000` in local/dev;
- authorize URL: `/api/method/frappe.integrations.oauth2.authorize`;
- token URL: `/api/method/frappe.integrations.oauth2.get_token`;
- API endpoint: `/api/method/frappe.integrations.oauth2.openid_profile`;
- redirect URL:
  `<site.access_url>/api/method/frappe.integrations.oauth2_logins.custom/lenscloud`;
- client secret supplied only through the short-lived mounted Secret contract.

Customer `Open Site` must open the target Site URL (`site.access_url`). It must
not open the OAuth callback/login method directly. The target Site, once
configured, owns redirecting unauthenticated users to the LensCloud Platform
OAuth provider. Until target Site username/password login is disabled, the
customer may see the Site login screen and choose `Login with LensCloud`; this
is acceptable for the interim SSO proof as long as no Site-local password is
entered.

Disabling username/password login on the target Site is a later Site
Control/System Settings automation and must be handled as an explicit
runner-backed command or documented target Site setting.

## Setup Input Sources

Platform should build a typed setup payload from server-side data only:

- company/customer name: Customer organization name, Subscription company, or signup profile.
- first user: active Owner/Admin Customer Member for the Subscription Customer.
- timezone, country, language, currency, chart of accounts, fiscal year: Plan/Site Control/Profile defaults with Customer/Subscription overrides where explicitly supported.
- site URL and redirect URIs: Site access URL and Platform Settings root domain.
- role mapping: Customer Member role to target Site role/profile mapping.

Missing required setup inputs block bootstrap with a customer-safe message and a Platform action-log entry.

## End-To-End Sequence

1. Customer signs up or signs in to LensCloud Platform.
2. Platform creates/links Customer and Customer Member.
3. Customer selects Free Plan and confirms Subscription.
4. Platform provisions Bench/Site through existing orchestration.
5. Operator reports Site Ready.
6. Platform creates `Site Bootstrap State` as `Pending`.
7. Platform creates first `Site Access Grant` for the Customer Owner/Admin as `Pending`.
8. Platform triggers `site_setup.status` through the Kubernetes API Bench Execute contract.
9. If setup is incomplete, Platform triggers `site_setup.complete` with typed setup inputs.
10. Runner executes in the target Bench/Site context and calls native Frappe setup wizard APIs to complete setup wizard.
11. Runner returns sanitized status: setup complete/incomplete, safe warnings, no secrets.
12. Platform records an Orchestration Action Log and marks setup status.
13. Platform triggers `oauth.status`.
14. Platform creates or resolves the OAuth client/issuer configuration for LensCloud Platform.
15. Platform triggers `oauth.configure` on the target Site with only the safe request fields and server-side secret references permitted by the runner contract.
16. Runner configures Frappe Social Login/OAuth client state on the target Site.
17. Platform triggers `user.ensure` for the first Customer Owner/Admin.
18. Runner creates or updates the target Site user without setting or returning a password.
19. Platform marks the Site Access Grant `Active`.
20. Customer sees `Open Site` in Platform.
21. Customer clicks `Open Site`; Platform either opens the Site URL directly or starts a signed handoff route.
22. Target Site redirects to LensCloud Platform OAuth when no Site session exists.
23. Platform authenticates the user and returns the user to the Site without a password prompt.
24. When a Customer Admin approves/adds another member and grants Site access, Platform creates a `Site Access Grant` and triggers `user.ensure`.
25. When a member is disabled or access is revoked, Platform triggers `user.disable` or `user.roles.set` and marks the grant `Revoked`.

## Runner Command Families

Minimum positive path for Infra contract:

- `site_setup.status`
- `site_setup.complete`
- `oauth.status`
- `oauth.configure`
- `user.ensure`
- `user.disable`
- `user.roles.set`
- `site_access.status`

Commands must be idempotent where possible and include a stable correlation ID. Unsupported families must return `COMMAND_UNSUPPORTED` until implemented.

Current implementation status:

- INF-021 provides `site_setup.status` and `site_setup.complete`.
- INF-022 provides `oauth.status` and `oauth.configure`; Platform owns the Platform-side OAuth Client and the runner configures only the target Site Social Login Key.
- `oauth.configure` may pass only non-secret Social Login Key fields in the request ConfigMap. The OAuth client secret must be created as a short-lived Kubernetes Secret, mounted read-only at `/lenscloud/secrets/client_secret`, then deleted after sanitized evidence capture.
- `user.*` and `site_access.status` remain unsupported until INF-023 publishes and verifies those runner contracts.
- Platform commit `c520b5a` removed the setup-runner live-verification block; the setup-wizard slice may run in the controlled Free Plan live E2E.


## Security Boundaries

- Platform calls Kubernetes API from Python only; no `kubectl` runtime dependency.
- Platform creates only labelled runner Jobs/ConfigMaps in approved runtime namespaces.
- Runner accepts only Platform-labelled requests for Platform-managed Bench/Site targets.
- Namespace, Bench, Site, Customer, Subscription, and ownership labels are validated before execution.
- No pod logs are read by Platform for normal evidence.
- No Secret values are returned. Secret references may be used only when explicitly allowed by the contract.
- Administrator password is not a Platform/browser API parameter. If a bootstrap secret is required, it remains Infra/operator-side and is consumed only inside the runner.
- Every command writes an Orchestration Action Log with sanitized request/response metadata.

## Acceptance Criteria

- Fresh Free Plan Site reaches Ready.
- Setup wizard completes automatically through runner-backed `site_setup.complete`.
- OAuth/social login is configured on the target Site.
- First Customer Owner/Admin can click `Open Site` in Platform and enter the Site without a password dialog.
- Added Customer Member receives a Site Access Grant and can enter the assigned Site without password entry.
- Disabled/revoked Customer Member cannot access the Site.
- Platform and target Site show no customer-facing runtime internals.
- Evidence contains no credentials, Secret values, Administrator password, OAuth client secret, bootstrap token, kubeconfig, pod logs, or raw environment dumps.

## Ownership Split

Platform owns:

- CUA product model, Customer Member policy, Site Access Grants, setup input resolution, OAuth issuer/client configuration data, UI, action logs, retry state, and customer-safe status.

Infra/operator owns:

- Runner implementation, RBAC/admission, safe mounts/secret references, target Bench/Site execution mechanics, negative security proofs, and cleanup behavior.

The two agents work sequentially: Platform documents this contract and handoff first, Infra implements/verifies the runner contract, then Platform implements backend/UI integration against the published contract.
