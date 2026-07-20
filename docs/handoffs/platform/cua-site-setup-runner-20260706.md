# Infra Handoff - CUA Site Setup Runner - 2026-07-06

## Source

Infra handoff:

```text
lenscloud-infra/docs/handoffs/platform/cua-site-setup-runner-handoff-20260706.md
```

Infra evidence:

```text
lenscloud-infra/docs/evidence/cua/site-setup-runner-evidence-20260706.md
```

Infra workitem:

```text
INF-021 CUA setup wizard runner gate
```

## Status

Reconciled against Platform commit `c520b5a` and Infra handoff copy on 2026-07-06. Infra has implemented and live-verified:

- `site_setup.status`
- `site_setup.complete`

Setup live verification used this runner:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:2905fb71dfb449258214a7b76016a67d9b98bd66ea378394f98d791ab293dad5
```

Current runner for new Platform work is published at:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:e003d3f49a1225ccc37df1147bc7f2d1ca704518b90575fc5ad4c4af4ffc7741
```

2026-07-19 update: `site_setup.status` remains on the synced generic runner,
but `site_setup.complete` must use the digest-pinned Release Group runtime
image because setup completion can execute installed-app setup hooks. This
supersedes the original all-setup-commands-through-generic-runner wording.

Platform may run `site_setup.status` through the existing Bench Command Python
Kubernetes API path during the controlled Free Plan live E2E.
Customer-facing automation may use OAuth after consuming the dedicated INF-022
handoff. User sync and Site access commands remain Unsupported until INF-023 is
implemented and live-verified.

## Contract Summary

The setup commands use native Frappe v16 APIs:

```text
frappe.is_setup_complete()
frappe.client_cache.get_doc("Installed Applications")
frappe.desk.page.setup_wizard.setup_wizard.setup_complete(args)
```

No LensCloud branding/bootstrap app is required for setup wizard completion.

OAuth runner live verification is complete under `INF-022`; Platform may adapt
OAuth through the Bench Command path. User and site access commands remain
`Unsupported` until `INF-023`.

## Platform Follow-Up

Platform should:

1. Pull latest `lenscloud-infra`.
2. Read `lenscloud-infra/docs/infra-workitems.md`.
3. Read `lenscloud-infra/docs/platform-bench-command-handoff.md`.
4. Read `lenscloud-infra/docs/handoffs/platform/cua-site-setup-runner-handoff-20260706.md`.
5. Wire `site_setup.status` through the existing Bench Command Python
   Kubernetes API path with the generic runner digest.
6. Wire `site_setup.complete` as an app-aware Job with the Release Group
   runtime image digest.
7. Keep request args non-secret.
8. Use the dedicated `INF-022` OAuth handoff for OAuth integration; keep
   user/site access commands disabled or shown as unsupported.
9. Parse only sanitized termination summaries.
10. Update Platform workitems, action logs, UI states, and evidence.

Evidence reference:

```text
lenscloud-infra/docs/evidence/cua/site-setup-runner-evidence-20260706.md
```

Platform commit `c520b5a` removed the setup-runner live-verification block. Treat `docs/handoffs/infra/cua-site-bootstrap-sso-runner-20260703.md` as the local Platform handoff showing `site_setup.status` and `site_setup.complete` live-verified.

Platform must not use kubectl, target Site Administrator HTTP login, raw
Secrets, pod logs, invented `FrappeSite` fields, or raw setup dumps.
