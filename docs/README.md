# LensCloud Platform Docs

This folder is organized by document purpose. The canonical Platform backlog is
`platform-workitems.md`; supporting docs may link to it, but they do not track
status independently.

## Structure

| Folder | Purpose |
| --- | --- |
| `platform-workitems.md` | Single canonical Platform backlog and status tracker. |
| `architecture/` | Durable product, runtime, state, release, database, wildcard, and workflow models. |
| `handoffs/platform/` | Platform agent handoffs and executable platform prompts. |
| `handoffs/infra/` | Platform-authored prompts and handoffs for the Infra agent. |
| `operator-sop/` | Operator runbooks, acceptance plans, and manual test SOPs. |
| `evidence/` | Dated proof, cleanup records, and live acceptance results. |
| `design/` | Design briefs and external design prompts. |
| `agents/` | Documentation about repo-local agent context, skills, and MCP expectations. |
| `decisions/` | Future architecture decision records. |
| `archive/` | Historical or superseded docs retained for reference. |

## Compatibility Stubs

These legacy paths remain as short redirect stubs because older prompts and
agents may still start there:

- `agent-handoff.md` -> `handoffs/platform/agent-handoff.md`
- `platform-agent-live-orchestration-prompt.md` -> `handoffs/platform/platform-agent-live-orchestration-prompt.md`
- `platform-runtime-lifecycle.md` -> `architecture/platform-runtime-lifecycle.md`

New documents should link to the structured location.

## Documentation Control

1. Add or update a row in `platform-workitems.md` before adding new Platform
   scope, UI/product work, operator workflow, or agent context.
2. Put durable design in `architecture/`, proof in `evidence/`, runbooks in
   `operator-sop/`, and cross-team prompts in `handoffs/`.
3. Keep secrets out of docs: no kubeconfig contents, tokens, passwords,
   Kubernetes Secret values, DB passwords, private keys, pod logs, raw backups,
   raw `site_config.json`, or full environment dumps.
4. If a compatibility stub exists, update new references to the structured path.
5. `.agents` is operational agent context, not a docs backlog. Its governance is
   documented in `.agents/README.md` and `docs/agents/agent-context-cleanup-20260629.md`.
