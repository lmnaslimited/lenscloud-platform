# Platform Handoff: Bench Command Remaining Families - 2026-06-30

## Source

Infra completed the remaining Bench Command runner families gate.

```text
Infra repo: lenscloud-infra
Infra commit: ac86bdc
Infra workitem: INF-017
Infra evidence: docs/bench-command-remaining-families-evidence-20260630.md
Infra handoff: docs/platform-bench-command-handoff.md
```

This handoff is the Platform-local pointer for the next Platform agent pass.
The Infra repository remains the source of truth for RBAC, runner image,
verification scripts, and live evidence.

## Objective

Update LensCloud Platform so Site Control / Bench Command UX understands the
current Infra runner matrix:

- `backup.status` is supported and live-verified.
- `backup.create` remains Unsupported.
- `restore.preview`, `restore.execute`, and `restore.status` remain
  Unsupported.
- `bench_test.trigger` remains Unsupported.
- `latp.trigger` and `latp.status` remain Unsupported.

Platform must show this truthfully and must not simulate successful backup,
restore, Bench Test trigger, or LATP behavior.

## Runner Image

Use the current Infra-pinned runner digest:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:eebfa0199c328207b14a949fa6232954a203a3937b1eed4930e9c3ec95b654d6
```

## Supported Command Addition

`backup.status` now returns safe backup metadata through the existing display
contract:

```json
{
  "phase": "Succeeded",
  "command": "backup.status",
  "summary": "Read backup status",
  "display": {
    "label": "Backups",
    "value": "0 available",
    "kind": "backup-status",
    "rawValue": {
      "count": 0,
      "latest": null
    },
    "safe": true
  }
}
```

Platform may render:

- `display.label`
- `display.value`
- safe latest-backup metadata from `display.rawValue.latest`, if present

Platform must not render or request:

- backup file contents
- database dumps
- raw private files
- Kubernetes Secrets
- DB passwords
- pod logs

## Unsupported Commands

These commands are known but must continue to render as Unsupported:

```text
backup.create
restore.preview
restore.execute
restore.status
bench_test.trigger
latp.trigger
latp.status
```

Expected status shape:

```text
phase: Unsupported
code: COMMAND_UNSUPPORTED
summary: command family is contracted but runner-pending
display: absent
```

Platform should render sanitized `phase`, `code`, and `summary` when `display`
is absent.

## Required Platform Work

1. Pull latest `lenscloud-infra` and confirm commit `ac86bdc` or newer.
2. Update the Platform runner digest to:
   `sha256:eebfa0199c328207b14a949fa6232954a203a3937b1eed4930e9c3ec95b654d6`.
3. Enable `backup.status` as a read/status Site Control action where policy
   allows it.
4. Render `backup.status` using the safe top-level `display` object.
5. Keep `backup.create`, restore, Bench Test trigger, and LATP actions
   unavailable or explicitly Unsupported.
6. Add backend tests for:
   - `backup.status` successful display parsing;
   - unsupported `backup.create`;
   - unsupported `restore.preview`;
   - no secret-like values in action log/display.
7. Add UI coverage proving `Backups: <count> available` is visible and
   unsupported commands do not look successful.
8. Record Orchestration Action Log evidence for supported and unsupported
   paths.
9. Keep command Job/ConfigMap cleanup behavior unchanged.

## Security Rules

Never expose:

- kubeconfig contents
- tokens
- Kubernetes Secret values
- DB passwords
- private keys
- pod logs
- raw `site_config.json`
- backup file contents
- full environment dumps

Do not require Platform operators to use `kubectl`.

## Platform Agent Prompt

```text
Work inside /workspace/frappe-bench/apps/lenscloud.

Pull latest /workspace/lenscloud-infra and confirm Infra commit ac86bdc or newer.

Read:
- docs/handoffs/platform/bench-command-remaining-families-20260630.md
- /workspace/lenscloud-infra/docs/infra-workitems.md
- /workspace/lenscloud-infra/docs/platform-bench-command-handoff.md
- /workspace/lenscloud-infra/docs/bench-command-remaining-families-evidence-20260630.md
- docs/handoffs/platform/bench-command-result-display-contract-20260629.md
- docs/platform-workitems.md

Implement Platform-side handling for INF-017:

- update the runner image digest to sha256:eebfa0199c328207b14a949fa6232954a203a3937b1eed4930e9c3ec95b654d6;
- enable backup.status as a read/status action where policy allows it;
- render backup.status using top-level display when display.safe is true;
- show Backups: <count> available in the action output and action log;
- keep backup.create, restore.*, bench_test.trigger, and latp.* Unsupported;
- never render backup file contents, Secrets, DB passwords, pod logs, raw site_config.json, or full env dumps;
- preserve existing command Job/ConfigMap cleanup behavior;
- add backend and UI tests for backup.status display and unsupported-command behavior.

Return:
- files changed;
- tests/build run;
- action log evidence for backup.status;
- UI evidence for Backups display;
- unsupported-command evidence;
- cleanup proof;
- remaining gaps.
```

## Remaining Infra Gaps

- Operator-compatible backup creation contract.
- Backup retention/location policy and evidence model.
- Restore preview/execute runbook with destructive confirmation.
- Bench Test trigger/status production suite definition.
- LATP trigger/status source and non-destructive result model.
- NetworkPolicy/resource quotas for command Jobs.
