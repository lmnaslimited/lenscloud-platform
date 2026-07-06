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
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:31973edd01e9c6ea75f2a3b4ef323d5ff643fcec97b2d49b6da9d9d10b7f7580
```

Platform may now run these setup commands through the existing Bench Command
Python Kubernetes API path during the controlled Free Plan live E2E.
Customer-facing automation should keep OAuth disabled until INF-022 live
verification is published. User sync and Site access commands remain
Unsupported until INF-023 is implemented and live-verified.

## Contract Summary

The setup commands use native Frappe v16 APIs:

```text
frappe.is_setup_complete()
frappe.client_cache.get_doc("Installed Applications")
frappe.desk.page.setup_wizard.setup_wizard.setup_complete(args)
```

No LensCloud branding/bootstrap app is required for setup wizard completion.

OAuth runner source/local verification is complete under `INF-022`, and the
runner image is published/repo-pinned, but Platform must keep OAuth commands
disabled until Infra applies admission and records live verification. User and
site access commands remain `Unsupported` until `INF-023`.

## Platform Follow-Up

Platform should:

1. Pull latest `lenscloud-infra`.
2. Read `lenscloud-infra/docs/infra-workitems.md`.
3. Read `lenscloud-infra/docs/platform-bench-command-handoff.md`.
4. Read `lenscloud-infra/docs/handoffs/platform/cua-site-setup-runner-handoff-20260706.md`.
5. Wire `site_setup.status` and `site_setup.complete` through the existing
   Bench Command Python Kubernetes API path.
6. Keep request args non-secret.
7. Keep OAuth disabled until `INF-022` live evidence is published; keep
   user/site access commands disabled or shown as unsupported.
8. Parse only sanitized termination summaries.
9. Update Platform workitems, action logs, UI states, and evidence.

Evidence reference:

```text
lenscloud-infra/docs/evidence/cua/site-setup-runner-evidence-20260706.md
```

Platform commit `c520b5a` removed the setup-runner live-verification block. Treat `docs/handoffs/infra/cua-site-bootstrap-sso-runner-20260703.md` as the local Platform handoff showing `site_setup.status` and `site_setup.complete` live-verified.

Platform must not use kubectl, target Site Administrator HTTP login, raw
Secrets, pod logs, invented `FrappeSite` fields, or raw setup dumps.
