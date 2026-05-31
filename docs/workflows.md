# LensCloud Platform Workflows

## Allowed Now

- site create
- site suspend
- site delete
- backup
- restore
- upgrade
- DNS automation

## Later

- multi-cluster migration
- advanced approval chains
- richer `SiteJob` UX unless the operator implementation matures first
- cross-region tenancy mobility

## Operational Rules

- Keep lifecycle operations idempotent where possible.
- Treat operator resources as the source of truth.
- Do not reimplement Kubernetes reconciliation logic in the app.

