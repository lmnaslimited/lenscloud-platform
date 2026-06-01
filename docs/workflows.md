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
- Customer pages should favor guided lifecycle flows, clear status surfaces, and prominent site creation entry points.
- Platform-facing inspector views may expose more fields and actions than customer-facing views.
- Customer-facing inspector views should be curated and lighter weight.
- Missing backend behavior must be surfaced as a gap rather than assumed.


## Customer Site-First Workflow

The customer portal must optimize for converting signed-in/inbound users into active LensCloud customers who can create and manage sites.

Customer navigation:

- Dashboard: conversion-oriented overview with a primary `Create Site` CTA, site counts, lifecycle status, and pending gaps.
- Sites: customer-friendly site cards/table with direct management actions.
- Create Site: dedicated guided flow for site creation requests.
- Account: customer identity, region preference, subscription/billing placeholders, and linked account context.

Customer action placement:

- `Create Site` must be a first-class route and prominent CTA.
- Customer lifecycle actions must appear in the main page body or site detail surface, not only in the inspector.
- The inspector may provide context, assistant help, technical metadata, and request history.
- Missing backend behavior must be shown as pending/unavailable/captured-as-request; do not implement backend business logic in this pass.

Create Site state model references:

- Customer: signed-in account and customer identity.
- Subscription: plan/product placeholder until backend subscription behavior is wired.
- Site: requested tenant instance and eventual provisioned site.
- Region: preferred placement source, displayed customer-friendly even though Region is a platform tree doctype.
- Bench: platform placement target, not directly editable by the customer in the first pass.

## Region Tree Workflow

Region is a native Frappe tree doctype. Platform-facing Region views must support both tree and list modes.

- Tree mode uses `parent_region` as the parent field.
- Group nodes use `is_group`.
- Ordering should follow nested-set fields such as `lft`/`rgt` where available.
- List mode remains available for filtering, scanning, and standard record work.

## Frontend Execution Order

The frontend work for LensCloud Platform follows the handover objects in `docs/agent-handoff.md`.

1. Complete Handover Object 1 before writing any frontend implementation.
2. Complete Handover Object 2 before wiring doctype-specific inspector behavior.
3. Complete Handover Object 3 before adding the assistant drawer and broader validation.
4. Complete Handover Object 4 last.
5. Every phase must end at its stop point and wait for explicit confirmation before the next phase begins.

## Frontend Guardrails

- Keep the first pass scoped to the workspace shell, platform inspector, customer dashboard/sites/create-site/account pages, and action entry points.
- Use native Frappe authentication and permissions for access control.
- Keep the platform-console and customer-portal surfaces separate by role.
- Mark missing backend behavior as a gap instead of assuming it exists.
- Keep the platform/infrastructure boundary explicit at all times.
