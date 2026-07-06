# Infra Handoff - CUA Site Bootstrap And SSO Runner

Work inside `lenscloud-infra`. Treat this Platform document as the product/runtime contract to implement and hand back with evidence.

## Current Status - 2026-07-06

Infra has completed the first setup-wizard gate from this handoff:

- `site_setup.status`: implemented and live-verified.
- `site_setup.complete`: implemented and live-verified.
- Live-verified runner image:
  `ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:2905fb71dfb449258214a7b76016a67d9b98bd66ea378394f98d791ab293dad5`
- Infra evidence:
  `lenscloud-infra/docs/evidence/cua/site-setup-runner-evidence-20260706.md`
- Infra handoff back to Platform:
  `lenscloud-infra/docs/handoffs/platform/cua-site-setup-runner-handoff-20260706.md`
- Platform-facing handoff:
  `apps/lenscloud/docs/handoffs/platform/cua-site-setup-runner-20260706.md`

Platform may now integrate `site_setup.status` and `site_setup.complete`
through the existing Bench Command Python Kubernetes API path. The previous
live-verification block for setup wizard automation is removed.

OAuth, user sync, role sync, and `site_access.status` remain unsupported until
Infra implements and live-verifies the next gates:

- `INF-022` CUA OAuth runner gate.
- `INF-023` CUA user/access runner gate.

Platform reference docs:

- `apps/lenscloud/docs/platform-workitems.md` -> `CUA Site bootstrap and SSO automation`
- `apps/lenscloud/docs/architecture/customer-identity-access.md`
- `apps/lenscloud/docs/architecture/cua-site-bootstrap-sso-sequence.md`
- `apps/lenscloud/docs/operator-sop/platform-customer-e2e-acceptance.md`

## Objective

Extend the existing Bench Command / Kubernetes API runner pattern so Platform can complete a provisioned Frappe Site setup wizard, configure Platform-backed OAuth/Social Login, and sync Site users/access grants without exposing Administrator passwords or Secret values.

This is a critical Central User Access differentiator. The target customer outcome is: customer signs in to LensCloud Platform, clicks `Open Site`, and enters the provisioned Site without a Site password prompt.

## Preferred Contract

Use Kubernetes API Bench Execute / Bench Command style, not direct Platform browser/API calls to target Site HTTP APIs with Administrator password.

Infra/operator owns the runner implementation. Platform will create labelled request ConfigMaps and Jobs through Python Kubernetes API only.

## Required Command Families

Implement and live-verify these command families, in order. Current status:

1. `site_setup.status` - Complete / live-verified by Infra.
2. `site_setup.complete` - Complete / live-verified by Infra.
3. `oauth.status` - Unsupported / pending `INF-022`.
4. `oauth.configure` - Unsupported / pending `INF-022`.
5. `user.ensure` - Unsupported / pending `INF-023`.
6. `user.disable` - Unsupported / pending `INF-023`.
7. `user.roles.set` - Unsupported / pending `INF-023`.
8. `site_access.status` - Unsupported / pending `INF-023`.

Unsupported commands must return `COMMAND_UNSUPPORTED` until implemented.

## Target Site App Assumption

The setup wizard portion no longer requires a LensCloud branding/bootstrap app.
Infra confirmed that native Frappe v16 APIs cover the setup gate:

- `frappe.is_setup_complete()`
- `frappe.client_cache.get_doc("Installed Applications")`
- `frappe.desk.page.setup_wizard.setup_wizard.setup_complete(args)`

For OAuth and user/access work, Infra should continue to prefer standard
Frappe APIs or bench-executed standard Frappe methods first. Add a
LensCloud branding/bootstrap app only if standard APIs are insufficient and the
gap is documented.

If a branding/bootstrap app is required for later gates, it may expose safe
bench-executable methods, for example:

- `lenscloud_branding.bootstrap.status`
- `lenscloud_branding.bootstrap.complete_setup`
- `lenscloud_branding.oauth.status`
- `lenscloud_branding.oauth.configure`
- `lenscloud_branding.access.ensure_user`
- `lenscloud_branding.access.disable_user`
- `lenscloud_branding.access.set_roles`

If Infra needs different method names, document the exact final contract.

## Request Schema Requirements

Each runner request must include:

- correlation ID;
- command family and command;
- runtime namespace;
- Bench identity;
- Site identity/hostname;
- Platform ownership labels;
- Customer/Subscription/Site identifiers;
- typed args;
- timeout;
- requested_by;
- non-secret setup/OAuth/user fields only.

Setup args may include company name, country, timezone, language, currency, chart of accounts, fiscal year, first user email/name, and role mapping.

OAuth args may include issuer URL, client ID, redirect URI, allowed scopes, provider label, and secret reference name only if the contract permits server-side secret references. Never include OAuth client secret value in a ConfigMap, action log, or evidence.

## Result Schema Requirements

Every command must return a sanitized summary with:

- status: Succeeded, Failed, Unsupported, Timed Out;
- code;
- display text safe for Platform operator;
- customer-safe display text where applicable;
- setup_complete / oauth_configured / user_synced booleans where relevant;
- target Site;
- correlation ID;
- retryable flag;
- next action;
- no Secret values, no raw pod logs, no raw `site_config.json`, no full environment dumps.

## RBAC And Admission

Allow only tightly scoped Platform-labelled Jobs/ConfigMaps in approved runtime namespaces. The runner must reject:

- unlabelled Jobs;
- wrong resource kind labels;
- wrong namespace;
- wrong Bench/Site ownership;
- default namespace operations;
- cluster-scoped mutation;
- Secret listing/reading by Platform;
- pod log reads by Platform;
- raw Secret-volume attempts not explicitly part of the approved runner design.

## Administrator Password Boundary

Administrator password must not be a normal Platform input. If the runner needs Administrator access internally, use an Infra/operator-owned secret or one-time bootstrap mechanism consumed only inside the runner. Do not return it, print it, log it, or put it in request ConfigMaps.

Prefer bench-executed app methods that do not require HTTP Administrator login.

## Live Verification Required

Infra live verification status:

1. `site_setup.status` reports setup state - Complete.
2. `site_setup.complete` completes setup wizard idempotently - Complete.
3. `oauth.status` reports missing/configured state - Pending `INF-022`.
4. `oauth.configure` configures LensCloud Platform as provider - Pending `INF-022`.
5. `user.ensure` creates or updates a target Site user without a password response - Pending `INF-023`.
6. `user.disable` prevents access for a disabled/revoked member - Pending `INF-023`.
7. `site_access.status` reports user/access state - Pending `INF-023`.
8. Cleanup removes terminal Jobs/ConfigMaps/pods as per existing command cleanup contract - Complete for `site_setup`.

Negative proof must show rejected unsafe requests and no credential leakage.

Setup runner live verification used:

```text
Namespace: lenscloud-runtime-eu
Bench: run-20260702-free-prod-bench
Site: run-20260702-free-site.cloud.lmnaslens.com
Sites PVC: run-20260702-free-prod-bench-sites
Temporary prefix: run-20260706-cua-existing
Cleanup proof: no resources found with that prefix
```

## Handover Back To Platform

For future gates, return a Platform handoff document with:

- Infra commit revision;
- exact runner image/digest if changed;
- command request examples with fake/sanitized values;
- sanitized result examples;
- RBAC/admission evidence;
- positive live command evidence;
- negative security evidence;
- cleanup evidence;
- remaining runner gaps;
- exact Platform integration prompt.

Do not expose kubeconfig, tokens, passwords, Kubernetes Secret values, OAuth client secrets, private keys, pod logs, or raw setup/site config contents.
