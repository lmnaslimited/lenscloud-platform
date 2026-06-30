# Infra Handoff: Remaining Bench Command Families - 2026-06-29

## Use Condition

Send this prompt to Infra only after Platform records successful real Bench/Site runner evidence in:

```text
apps/lenscloud/docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md
```

Platform should include the successful action log, sanitized summary, display result, authenticated UI proof, and Job/ConfigMap cleanup proof when handing this to Infra.

## Current Platform Baseline

As of 2026-06-30, Platform has completed:

```text
Infra 328846b: real Bench sites path fix consumed
Infra 405e0c1 / INF-016: sanitized result display contract consumed
Live display proof: ORCH-2026-00161 -> Maintenance mode: Off
Authenticated UI proof: ORCH-2026-00165 -> Maintenance mode: Off
Platform runner digest currently used: sha256:ab69e3ff24584e268bfa92f44c5d71e680ce1780cc8a4a9a5ce1e60b3e4bf4e7
```

Platform currently keeps these families Unsupported until Infra completes and hands back contracts:

```text
backup.create
backup.status
restore.preview
restore.execute
restore.status
bench_test.trigger
latp.trigger
latp.status
```

## Prompt For Infra Agent

Work inside `lenscloud-infra`.

Start from Infra revision `405e0c1` or newer. Read:

1. `docs/infra-workitems.md`
2. `docs/platform-bench-command-handoff.md`
3. `docs/bench-command-production-runner-evidence-20260627.md`
4. `docs/bench-command-result-display-evidence-20260629.md`
5. the Platform real Bench/Site runner evidence supplied in the task context:
   `apps/lenscloud/docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md`

Update the canonical Infra backlog first with a dated workitem for the remaining Bench Command runner families.

Goal:

Implement and live-verify the remaining production runner contracts so Platform can wire Site Control commands as one complete set.

Remaining families:

- `backup.create`
- `backup.status`
- `restore.preview`
- `restore.execute`
- `restore.status`
- `bench_test.trigger`
- `latp.trigger`
- `latp.status`

Keep the existing INF-010/INF-011 Job/ConfigMap contract and the INF-016 sanitized result display contract unless a contract change is explicitly documented and handed to Platform.

Safety and display requirements:

- No kubeconfig, token, password, Kubernetes Secret value, DB password, private key, pod log, raw backup content, raw `site_config.json`, or full environment dump may appear in responses or evidence.
- Backup responses return metadata only, never raw backup contents or credentials.
- Restore requires explicit destructive confirmation and backup identity.
- Production LATP must be non-destructive unless a future approved policy says otherwise.
- Bench Test and LATP status must have a clear status source and stable summary schema.
- All commands must return sanitized termination summaries and stable error codes.
- Supported status/read commands should return top-level `display` only when the result is safe for Platform UI display.
- For any new read/status result, set `display.safe=true` only for explicitly safe fields and include `display.label`, `display.value`, `display.kind`, and optional safe `display.rawValue`.
- Do not require Platform to render arbitrary `details.value`; details may remain audit/test context only.
- Temporary Jobs, ConfigMaps, Pods, and runner artifacts must be cleaned.
- `MariaDB/default/frappe-mariadb` and all cluster infrastructure remain protected.

Validation required:

- Positive live proof for each implemented command.
- Negative proof for invalid args, invalid target, wrong namespace, unsafe Job shape, Secret access, pod log access, and unsupported command behavior.
- Cleanup proof for every temporary resource.
- Supported/unsupported matrix after implementation.
- Exact request/response examples for Platform, including `display` blocks where safe.
- Confirmation that runner-pending commands remain `COMMAND_UNSUPPORTED` until fully implemented and verified.

Return to Platform:

- Infra commit hash.
- Updated `docs/infra-workitems.md`.
- Updated `docs/platform-bench-command-handoff.md` if the contract changed.
- Dated evidence document.
- Supported command matrix.
- Request/response examples.
- Cleanup proof.
- Remaining gaps.
- Platform handoff prompt specifying exactly what Platform should enable and test.
- Explicit note whether Platform must update runner digest, command allowlist, typed args, display mappings, UI copy, or tests.
