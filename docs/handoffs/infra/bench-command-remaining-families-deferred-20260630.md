# Infra Handoff: Bench Command Remaining Families Deferred - 2026-06-30

## Decision

Platform is moving the immediate milestone to Free-first customer E2E: signup handoff, Plan browsing, Free subscription, automatic Site provisioning, customer dashboard, and Platform/customer acceptance evidence.

The remaining Bench Command families are intentionally deferred unless they become a direct production blocker for Free-first launch.

## Current Truth

Supported and consumed by Platform:

```text
backup.status
```

Still Unsupported in Platform and intentionally not required for the next E2E pass:

```text
backup.create
restore.preview
restore.execute
restore.status
bench_test.trigger
latp.trigger
latp.status
```

Platform must continue to render these commands as `Unsupported / COMMAND_UNSUPPORTED`; it must not simulate backup creation, restore, Bench Test trigger, or LATP behavior.

## Request To Infra

Do not prioritize the remaining Bench Command runner families until Platform completes the Free-first customer E2E pass, unless a production launch blocker requires a specific command earlier.

When work resumes, provide one handoff per command family with:

- runner image digest;
- request and sanitized response schema;
- positive live evidence;
- negative proof for Secrets, pod logs, default namespace, and unlabelled resources;
- cleanup proof for temporary Jobs/ConfigMaps;
- exact Platform action expected.

## Platform References

- Canonical backlog: `docs/platform-workitems.md`
- Platform backup status evidence: `docs/evidence/bench-command/bench-command-backup-status-evidence-20260630.md`
- Current Platform handoff: `docs/handoffs/platform/agent-handoff.md`
