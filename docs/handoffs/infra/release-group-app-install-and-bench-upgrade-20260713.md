# Infra Handoff: Release Group App Install And Bench Upgrade Wiring

Date: 2026-07-13
Owner: Platform hands off the contract; Infra owns operator/command execution.

## Context

`Release Group.included_apps` is no longer a Table MultiSelect. It is a child
table using `Release Group Apps` rows:

- `app`
- `install_at_site_creation`
- `install_sequence`

Platform needs Infra support for three related flows:

1. New Site bootstrap installs Release Group apps selected for site creation.
2. Bench upgrade moves a Bench from `current_release` to `next_release` only
   after every Site on the Bench is scheduled and tested.
3. Existing Sites can install newly available Release Group apps through a
   Platform/customer action.

## New Site Bootstrap Contract

When Platform creates a Site, it will derive install apps from the Site Bench's
Release Group:

- include only child rows where `install_at_site_creation` is checked;
- exclude `frappe`; Frappe is the framework/base site runtime and Platform will not send it as an install app;
- sort by ascending `install_sequence`, with empty sequence values last;
- pass stable app identifiers/names, not display labels;
- keep the submitted order in the operator command payload.

Infra must install those apps during new Site bootstrap after the base Frappe
site exists and before the Site is marked Ready. The command must be
idempotent: retrying a bootstrap with the same ordered apps must not fail
because an app is already installed. Infra must not require `frappe` to appear
in `install_apps`; the first app may be a product app such as `erpnext`.

Expected payload shape from Platform:

```json
{
  "site": "customer-site.example",
  "bench": "bench-name",
  "release_group": "lens-pure",
  "release": "v16.14.1",
  "install_apps": [
    {
      "app": "erpnext",
      "install_sequence": 20
    },
    {
      "app": "hrms",
      "install_sequence": 30
    }
  ]
}
```

Infra should return a safe display/result payload that names attempted apps,
successful apps, skipped already-installed apps, failed app, exit code, and a
sanitized error excerpt.

## Bench Upgrade Contract

Platform will set `Bench.next_release` only to a released/eligible Release in
the same Release Group as the Bench. Site upgrade scheduling is manual for the
initial implementation.

Before Platform lets a Site move to `upgrade_state = Scheduled`, the Site must
have:

- `upgrade_tested` checked;
- `tested_on` filled;
- `tested_by` filled.

Before Platform sends the Bench `update bench` action to Infra:

- Bench must have `next_release`;
- every active Site on the Bench must be in `upgrade_state = Scheduled`;
- the target Release must belong to the Bench Release Group.

Infra must expose or extend the Bench command execution path so Platform can
request the Bench update to the target Release and receive observable progress,
terminal status, and a sanitized result.

## Existing Site App Install Contract

When a Release Group gains apps, Platform needs a way to refresh the app
catalog available to Benches/Sites in that Release Group. Platform/customer
portal users will then be able to install eligible apps to existing Sites.

Infra needs to provide an idempotent command that installs one eligible app, or
a small ordered batch, into an existing Site:

```json
{
  "site": "customer-site.example",
  "bench": "bench-name",
  "release_group": "lens-pure",
  "apps": [
    {
      "app": "payments",
      "install_sequence": 30
    }
  ],
  "requested_by": "platform-or-customer-user"
}
```

The command must verify the Site belongs to the Bench, run inside the correct
Bench context, skip already-installed apps safely, and report installed,
skipped, and failed apps without exposing secrets.

## Infra Docs And SOPs To Update

Infra must update its own canonical docs before marking the work complete:

- `docs/infra-workitems.md` with dated workitems for new Site app install,
  Bench update, and existing Site app install.
- `docs/platform-bench-command-handoff.md` or the current canonical Bench
  Command/API contract with command names, request schema, result schema,
  supported/unsupported matrix, admission/RBAC expectations, and cleanup rules.
- The production runner/operator SOP that explains how to verify these commands
  on a real Bench/Site. If the existing Bench Command runner SOP is reused, add
  these commands as a gated section instead of creating a parallel truth source.
- A dated Infra evidence document with positive, negative, cleanup, and
  secret-safety proof.

The SOPs must spell out that `frappe` is not an install app payload item. The
base Frappe runtime must already exist before app install commands run.

## Handover Back To Platform

When Infra finishes, return a Platform handoff document with:

- Infra commit revision and runner image/digest if changed.
- Exact command names for new Site bootstrap app install, Bench update, and
  existing Site app install.
- Final request/response schemas with fake/sanitized examples.
- Supported/unsupported command matrix and any feature flags/admission pins.
- RBAC/admission evidence, including rejection of wrong namespace, wrong Bench,
  wrong Site, invalid command, unsafe Job shape, and Secret/pod-log access.
- Positive live evidence for ordered app install, idempotent retry, Bench update,
  and existing Site app install.
- Cleanup proof for Jobs, ConfigMaps, terminal Pods, temporary Secrets if any,
  and runner artifacts.
- Secret-safety proof showing no kubeconfig, passwords, Secret values, private
  keys, raw site config, pod logs, or environment dumps are returned.
- Remaining Infra gaps and exact Platform integration prompt: fields to send,
  commands to allowlist, validations to add, UI states to expose, and tests/SOPs
  Platform should run.

Platform will then update `docs/platform-workitems.md`, Platform command
allowlists/typed validation, customer/platform UI actions, dated Platform
evidence, `docs/operator-sop/bench-command-real-site-runner-verification.md` or
a focused successor SOP, and `docs/handoffs/platform/agent-handoff.md`.

## Acceptance

- New Site creation installs only Release Group apps marked Install At Site
  Creation and preserves install order.
- `install_apps` does not include `frappe`, and Infra does not require `frappe`
  in the app install payload.
- App install retry is safe when some/all requested apps are already installed.
- Bench update rejects a target Release outside the Bench Release Group.
- Bench update is observable through the existing Bench Command result path.
- Existing Site app install is available as an Infra command/API that Platform
  can call from Platform and customer portal workflows.
- Results are secret-safe and suitable for action logs and customer-facing
  progress where applicable.
