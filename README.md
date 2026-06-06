# LensCloud Platform

LensCloud Platform is the Frappe-based control plane for managing customer self-service and platform operations.

This repository is intentionally focused on the product layer:
- native Frappe authentication and role-based access
- customer onboarding and subscription flows
- release group selection and promotion
- bench and site lifecycle workflows
- backup and restore workflows
- upgrade orchestration
- Wildcard hostname reservation and route readiness
- customer portal and platform console UI
- audit, policy, and permissions

The runtime infrastructure is managed elsewhere by Kubernetes and the Frappe Operator.

## Responsibilities

- Provide a modern Frappe UI for the platform team.
- Provide a customer-facing self-service portal in the same app.
- Expose API endpoints for safe automation.
- Track customers, subscriptions, environments, release groups, benches, sites, DNS state, backups, and upgrades.
- Enforce policy around region, environment, and tenant placement.
- Orchestrate operator resources instead of reimplementing runtime mechanics.

## Non-Goals

- Cluster provisioning
- Cloud account bootstrapping
- Node pool creation
- DNS/firewall bootstrap
- Direct runtime reconciliation of Frappe pods

## Runtime Model

- The app itself runs as a containerized Frappe application.
- It talks to Kubernetes and Frappe Operator through an internal integration layer.
- It should remain usable for customers and platform operators without requiring CLI access.

## Initial Requirements

See [requirements.md](./requirements.md).

## Devcontainer

Open this repo in the local devcontainer defined under [`.devcontainer/`](./.devcontainer).

The platform workspace follows the Frappe CRM / Frappe Docker development pattern:
- `docker-compose.yml` for the local workspace services
- `init.sh` for bench and site bootstrap
- `devcontainer.json` for the VS Code container entrypoint
- `backend` as the active Frappe workspace container

The workspace is pinned to Frappe v16 for now so we stay on a stable product line while the platform foundation takes shape.
The `lenscloud` app scaffold and its platform/customer frontend now live in this
repository.

## Agent Handoff

Repo-local agent guidance lives in [AGENTS.md](./AGENTS.md) and [docs/agent-handoff.md](./docs/agent-handoff.md).
The current devcontainer implementation handoff is
[docs/platform-agent-live-orchestration-prompt.md](./docs/platform-agent-live-orchestration-prompt.md).
Frontend agents must use the repo-local
[Frappe UI product skill](./.agents/skills/frappe-ui-product/SKILL.md).
The broader operating model is documented in:
- [docs/agent-matrix.md](./docs/agent-matrix.md)
- [docs/skills.md](./docs/skills.md)
- [docs/mcps.md](./docs/mcps.md)
- [docs/state-model.md](./docs/state-model.md)
- [docs/release-model.md](./docs/release-model.md)
- [docs/platform-gap-backlog.md](./docs/platform-gap-backlog.md)
- [docs/workflows.md](./docs/workflows.md)

## Suggested Stack

- Frappe app for the UI and workflows
- Kubernetes API integration for operator resources
- PostgreSQL or MariaDB for platform metadata
- S3-compatible object storage for backups and exports
- Redis for queues and background jobs

## Early Milestones

1. Define the data model.
2. Define the API contract.
3. Build the first UI screens for customer, bench, and site lifecycle.
4. Add backup and restore operations.
5. Add region-aware policy and audit logging.
