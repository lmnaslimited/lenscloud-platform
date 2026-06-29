# Infra Handoff: Bench Command Result Display Contract - 2026-06-29

## Context

Platform completed real Bench Command runner verification after Infra revision `328846b`.

Evidence:

```text
apps/lenscloud/docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md
apps/lenscloud/docs/operator-sop/bench-command-real-site-runner-verification.md
```

The live command succeeded:

```text
command: maintenance_mode.status
action log: ORCH-2026-00159
status: Succeeded
summary: Read maintenance_mode status
details.key: maintenance_mode
details.value: 0
layout: frappe-sites
redacted: true
secret_values_returned: false
```

User validation found a Platform usability gap: the action succeeds, but the UI does not clearly show the actual command result, for example whether maintenance mode is On or Off. The sanitized summary has enough data for this case, but Platform needs a stable Infra response/display contract before wiring every command family into the UI.

## Prompt For Infra Agent

Work inside `lenscloud-infra`.

Start from revision `328846b` or newer. Read:

1. `docs/infra-workitems.md`
2. `docs/platform-bench-command-handoff.md`
3. `docs/bench-command-real-site-path-evidence-20260629.md`
4. Platform evidence: `apps/lenscloud/docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md`
5. Platform operator SOP: `apps/lenscloud/docs/operator-sop/bench-command-real-site-runner-verification.md`

Update the canonical Infra backlog first with a dated workitem for the Bench Command sanitized result display contract.

Goal:

Formalize a stable, secret-safe response schema for supported Bench Command status/read commands so Platform can render clear human-readable results such as:

```text
Maintenance mode: Off
Developer mode: Off
CORS allowlist: <safe origin list>
Site config <approved key>: <safe redacted/scalar value>
```

Issue found by Platform validation:

`maintenance_mode.status` succeeds, but Platform currently shows only success. The runner returns useful sanitized data under `details`, for example:

```text
details.key = maintenance_mode
details.value = 0
layout = frappe-sites
summary = Read maintenance_mode status
```

Infra task:

1. Update `docs/infra-workitems.md` with a dated workitem for the result display contract.
2. Confirm and document the stable response schema for currently supported read/status commands:
   - `maintenance_mode.status`
   - `developer_mode.status`
   - `site_config.get`
   - `cors.allowlist.get`
3. Provide safe sample termination summaries for each command.
4. Explicitly mark which fields are safe for Platform UI display.
5. Normalize runner output if these commands currently return inconsistent shapes.
6. Confirm safe display values for booleans and flags:
   - `0` / `false` -> `Off`
   - `1` / `true` -> `On`
7. Define redaction behavior for approved `site_config.get` keys that could still be sensitive.
8. Confirm unsupported and failed command result shapes:
   - `COMMAND_UNSUPPORTED`
   - `INVALID_ARGUMENTS`
   - `TARGET_NOT_FOUND`
   - `RUNNER_FAILED`
9. Run live or local verification for supported read/status commands and record sanitized evidence.
10. Update `docs/platform-bench-command-handoff.md` with the result display contract.
11. Return a Platform handoff prompt describing:
    - response schema;
    - display labels;
    - safe fields;
    - redaction rules;
    - unsupported/failed result behavior;
    - evidence and cleanup proof.

Security rules:

- Never expose kubeconfig contents, tokens, Secret values, DB passwords, private keys, raw full `site_config.json`, pod logs, or full environment dumps.
- Do not require Platform to read pod logs.
- Do not require Platform to read Secrets.
- Keep backup, restore, Bench Test trigger, and LATP marked runner-pending unless their contracts are also implemented and verified.

## Expected Platform Follow-Up

After Infra hands back the result display contract, Platform will:

1. Add command-result formatting in the backend and UI.
2. Show readable status output in the action result and Orchestration Action Log.
3. Add per-command display mappings for supported commands.
4. Add tests proving safe fields are displayed and secret-like fields are not displayed.
5. Keep runner-pending families as `Unsupported` until Infra completes those contracts.
