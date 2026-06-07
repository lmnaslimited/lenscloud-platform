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
- [docs/agent-handoff.md](./docs/agent-handoff.md)
- [docs/platform-runtime-lifecycle.md](./docs/platform-runtime-lifecycle.md)
- [docs/platform-agent-live-orchestration-prompt.md](./docs/platform-agent-live-orchestration-prompt.md)
- [.agents/skills/frappe-ui-product/SKILL.md](./.agents/skills/frappe-ui-product/SKILL.md)
