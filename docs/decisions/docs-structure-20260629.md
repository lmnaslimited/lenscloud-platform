# Docs Structure Decision - 2026-06-29

## Decision

LensCloud Platform docs are organized by document purpose instead of by date or
current milestone.

The canonical Platform backlog remains:

```text
docs/platform-workitems.md
```

All other docs support that backlog and must not become independent status
trackers.

## Folder Model

- `architecture/`: durable models and contracts owned by Platform.
- `handoffs/platform/`: Platform agent handoffs and executable prompts.
- `handoffs/infra/`: Platform-authored prompts for the Infra agent.
- `operator-sop/`: operator runbooks and manual acceptance plans.
- `evidence/`: dated proof and cleanup records.
- `design/`: design briefs and external design prompts.
- `agents/`: documentation about repo-local agent context.
- `archive/`: historical or superseded docs retained for reference.

## Compatibility

Short redirect stubs remain at these old paths because existing prompts and
operators may still open them directly:

- `docs/agent-handoff.md`
- `docs/platform-agent-live-orchestration-prompt.md`
- `docs/platform-runtime-lifecycle.md`

New references should use the structured paths.

## Agent Context

The `.agents` folder remains outside `docs/` because it is operational agent
context, not documentation backlog. Its governance is documented in:

```text
.agents/README.md
docs/agents/agent-context-cleanup-20260629.md
```
