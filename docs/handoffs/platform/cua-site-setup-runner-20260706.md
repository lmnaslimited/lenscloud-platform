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

Infra has implemented and live-verified:

- `site_setup.status`
- `site_setup.complete`

Live-verified runner image:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:2905fb71dfb449258214a7b76016a67d9b98bd66ea378394f98d791ab293dad5
```

Platform may integrate these commands through the existing Bench Command
Python Kubernetes API path.

## Contract Summary

The setup commands use native Frappe v16 APIs:

```text
frappe.is_setup_complete()
frappe.client_cache.get_doc("Installed Applications")
frappe.desk.page.setup_wizard.setup_wizard.setup_complete(args)
```

No LensCloud branding/bootstrap app is required for setup wizard completion.

OAuth, user, and site access commands remain `Unsupported` until Infra
implements and live-verifies `INF-022` and `INF-023`.

## Platform Follow-Up

Platform should:

1. Pull latest `lenscloud-infra`.
2. Read `lenscloud-infra/docs/infra-workitems.md`.
3. Read `lenscloud-infra/docs/platform-bench-command-handoff.md`.
4. Read `lenscloud-infra/docs/handoffs/platform/cua-site-setup-runner-handoff-20260706.md`.
5. Wire `site_setup.status` and `site_setup.complete` through the existing
   Bench Command Python Kubernetes API path.
6. Keep request args non-secret.
7. Keep OAuth/user/site access commands disabled or shown as unsupported.
8. Parse only sanitized termination summaries.
9. Update Platform workitems, action logs, UI states, and evidence.

Live verification evidence:

```text
lenscloud-infra/docs/evidence/cua/site-setup-runner-evidence-20260706.md
```

Platform must not use kubectl, target Site Administrator HTTP login, raw
Secrets, pod logs, invented `FrappeSite` fields, or raw setup dumps.
