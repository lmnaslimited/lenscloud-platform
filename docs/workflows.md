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

## Workspace Model

LensCloud uses a control-plane workspace model, not a literal CRM copy.

- Left navigation keeps the current scope and session context.
- The main workspace carries dashboards, lists, timelines, action flows, and other operational content.
- The right contextual inspector carries record summary, editable fields, lifecycle status, related objects, and history.
- The AI assistant is an optional drawer attached to the inspector, not a permanent competing pane.
- Read-only status surfaces must remain visually distinct from editable document fields.
- CRM shell patterns may be used as a reference for split-workspace behavior, but the LensCloud layout must remain control-plane oriented.

## Workspace Behavior by Surface

- Platform console pages should favor dense operational context and fast record access.
- Customer pages should favor guided lifecycle flows and clear status surfaces.
- Platform-facing inspector views may expose more fields and actions than customer-facing views.
- Customer-facing inspector views should be curated and lighter weight.
- Missing backend behavior must be surfaced as a gap rather than assumed.

## Frontend Execution Order

The frontend work for LensCloud Platform follows the handover objects in `docs/agent-handoff.md`.

1. Complete Handover Object 1 before writing any frontend implementation.
2. Complete Handover Object 2 before wiring doctype-specific inspector behavior.
3. Complete Handover Object 3 before adding the assistant drawer and broader validation.
4. Complete Handover Object 4 last.
5. Every phase must end at its stop point and wait for explicit confirmation before the next phase begins.

## Frontend Guardrails

- Keep the first pass scoped to the workspace shell, inspector, and action entry points.
- Use native Frappe authentication and permissions for access control.
- Keep the platform-console and customer-portal surfaces separate by role.
- Mark missing backend behavior as a gap instead of assuming it exists.
- Keep the platform/infrastructure boundary explicit at all times.
