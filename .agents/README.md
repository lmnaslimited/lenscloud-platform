# LensCloud Agent Context

This folder contains small, operational instructions for agents working in the
LensCloud Platform repository. It is not a second backlog and it is not a place
for stale prompts.

## Current Inventory

| Path | Status | Purpose |
| --- | --- | --- |
| `skills/frappe-ui-product/SKILL.md` | Used | Required workflow for LensCloud frontend/UI changes. |
| `skills/frappe-ui-product/references/lenscloud-ui-contract.md` | Used | Product boundaries and UX rules for Platform and customer screens. |
| `skills/frappe-ui-product/references/frappe-ui-patterns.md` | Used | Frappe UI and Frappe CRM-compatible interaction patterns. |
| `skills/frappe-ui-product/agents/openai.yaml` | Used | Optional metadata for skill-aware agent surfaces. Not a runtime dependency. |

No MCP server configuration is active from this folder.

## Usage Rules

- Backend, orchestration, docs-only, and Infra-handoff work does not need the
  Frappe UI skill.
- Before changing Platform or customer UI, read:
  1. `skills/frappe-ui-product/SKILL.md`
  2. `skills/frappe-ui-product/references/lenscloud-ui-contract.md`
  3. `skills/frappe-ui-product/references/frappe-ui-patterns.md`
- Do not add new skills, MCP references, or agent prompts unless a matching row
  exists first in `docs/platform-workitems.md`.
- If a file here is not read by an actual workflow, either promote it into
  `AGENTS.md` or move it to an archive/delete it in the same change.

## Governance

The canonical Platform backlog remains `docs/platform-workitems.md`. This
folder can support agent behavior, but it must not track status independently.
