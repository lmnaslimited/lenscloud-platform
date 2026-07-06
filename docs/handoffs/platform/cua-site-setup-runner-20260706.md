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

Infra has implemented runner source for:

- `site_setup.status`
- `site_setup.complete`

Platform must not enable these commands for customer-facing workflows until
Infra publishes the new runner image, pins the digest in admission, and returns
live verification evidence from a real Platform-managed Bench/Site.

## Contract Summary

The setup commands use native Frappe v16 APIs:

```text
frappe.is_setup_complete()
frappe.core.doctype.installed_applications.installed_applications.get_setup_wizard_pending_apps()
frappe.desk.page.setup_wizard.setup_wizard.setup_complete(args)
```

No LensCloud branding/bootstrap app is required for setup wizard completion.

OAuth, user, and site access commands remain `Unsupported` until Infra completes
the setup proof and opens the next gates.

## Platform Follow-Up

After Infra returns live verification evidence, Platform should:

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

Platform must not use kubectl, target Site Administrator HTTP login, raw
Secrets, pod logs, invented `FrappeSite` fields, or raw setup dumps.
