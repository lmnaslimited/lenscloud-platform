# LensCloud Platform Agent Guide

This repository owns the `lenscloud` Frappe app and its product workflows.

## Own This Repo

- Customer identity and access
- Subscription and plan logic
- Customer site requests
- Database Server, Bench, and Site lifecycle after Cluster handoff
- First-class runtime inventory, ownership policy, deletion, finalizer tracking, and lifecycle audit
- wildcard hostname reservation and infrastructure edge-readiness integration
- Backup, restore, and upgrade UX
- Customer portal and platform console

## Do Not Put Here

- Cluster provisioning
- Hcloud bootstrap
- Kubernetes substrate setup
- Operator installation scripts
- Raw operator reconciliation implementation; Platform invokes and observes operator APIs through the documented contract

## Read First

- [README.md](./README.md)
- [requirements.md](./requirements.md)
- [docs/handoffs/platform/agent-handoff.md](./docs/handoffs/platform/agent-handoff.md)
- [docs/architecture/platform-runtime-lifecycle.md](./docs/architecture/platform-runtime-lifecycle.md)
- [docs/handoffs/platform/platform-agent-live-orchestration-prompt.md](./docs/handoffs/platform/platform-agent-live-orchestration-prompt.md)

## UI Work

Before changing Platform or customer frontend code, read:

- [.agents/README.md](./.agents/README.md)
- [.agents/skills/frappe-ui-product/SKILL.md](./.agents/skills/frappe-ui-product/SKILL.md)
- [.agents/skills/frappe-ui-product/references/lenscloud-ui-contract.md](./.agents/skills/frappe-ui-product/references/lenscloud-ui-contract.md)
- [.agents/skills/frappe-ui-product/references/frappe-ui-patterns.md](./.agents/skills/frappe-ui-product/references/frappe-ui-patterns.md)

Do not treat `.agents` as a backlog. New agent context starts in
`docs/platform-workitems.md` first.


## Token And Tool Hygiene

- Prefer narrow reads (`rg`, small `sed` ranges) over dumping whole files.
- Use targeted browser probes for a single UI defect before running full Playwright.
- Run full desktop/mobile Playwright only when the touched flow or release gate needs it.
- When testing dialogs/forms, assert the actual interaction, such as typing into inputs and reading values, not just that the dialog opens.
- Keep updates and evidence concise; link files instead of repeating long logs.
