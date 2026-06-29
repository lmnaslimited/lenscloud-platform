# Agent Context Cleanup - 2026-06-29

## Scope

Clean up the repository-local `.agents` context so it is either clearly used or
clearly absent. The immediate concern was that skills and MCP-like context could
exist without being used by agents.

## Outcome 1: Audit

Current `.agents` files:

| Path | Finding |
| --- | --- |
| `.agents/skills/frappe-ui-product/SKILL.md` | Useful and now explicitly required for UI work. |
| `.agents/skills/frappe-ui-product/references/lenscloud-ui-contract.md` | Useful UI product contract. |
| `.agents/skills/frappe-ui-product/references/frappe-ui-patterns.md` | Useful Frappe UI pattern reference. |
| `.agents/skills/frappe-ui-product/agents/openai.yaml` | Metadata only; retained as optional skill metadata, not a runtime dependency. |

No active MCP server configuration was found in `.agents`.

## Outcome 2: Promote Or Archive

Promoted:

- `.agents/README.md` now explains the folder purpose, usage rules, inventory,
  and governance.
- `AGENTS.md` now makes the Frappe UI skill conditional and explicit: read it
  before Platform/customer frontend changes, not for every backend or docs-only
  task.

Archived/deleted:

- Nothing was archived in this pass because every existing `.agents` file has a
  current use after the governance update.

## Outcome 3: Document Governance

Rules now documented:

- `docs/platform-workitems.md` remains the only canonical Platform backlog.
- `.agents` is operational agent context, not a status tracker.
- New skills, MCP references, and prompts must start as a Platform workitem.
- Files that are not read by an actual workflow must be promoted into
  `AGENTS.md` or archived/deleted in the same cleanup pass.

## Remaining Guidance

Future UI work should name the Frappe UI skill in the implementation summary
and state which existing LensCloud/Frappe pattern was reused. Future non-UI
work should not load UI skill context unless it touches visible Platform or
customer UX.
