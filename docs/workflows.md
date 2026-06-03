# LensCloud Platform Workflows

## Allowed Now

- site create
- site suspend, platform-facing by default
- site delete, platform-facing by default
- backup, platform-facing or qualified-customer only
- restore, platform-facing or qualified-customer only
- release create/promote/block, platform-facing only
- bench upgrade planning, platform-facing only
- upgrade, platform-facing or qualified-customer only
- DNS automation, platform-facing or qualified-customer only

## Later

- multi-cluster migration
- advanced approval chains
- richer `SiteJob` UX unless the operator implementation matures first
- cross-region tenancy mobility

## Operational Rules

- Keep lifecycle operations idempotent where possible.
- Treat operator resources as the source of truth.
- Do not reimplement Kubernetes reconciliation logic in the app.
- Do not treat Release Group as a deployable version; Bench must deploy a specific Release.

## Release And Bench Upgrade Workflow

Release Group is the stable release family. Release is the deployable transaction. Bench tracks current and next release state.

Release Group actions:

- view Releases
- view Benches grouped by current Release
- view Benches behind latest eligible Release
- create Release
- promote Release
- schedule rollout
- compare Release adoption

Release actions:

- mark build ready
- promote to Quality
- promote to Production eligible
- block Release
- view affected Benches
- schedule Bench upgrades

Bench actions:

- create Bench from Release Group and Release
- schedule upgrade to next Release
- run pre-upgrade checklist
- start upgrade
- verify upgrade
- rollback to previous Release
- mark upgrade complete

Bench upgrade SOP states:

- Draft
- Scheduled
- Precheck
- Ready
- Running
- Verifying
- Completed
- Rolled Back
- Failed

Frontend expectations:

- Release Group pages must summarize release adoption across Benches.
- Release pages must show build/promotion status and affected Benches.
- Bench pages must show current Release, next Release, schedule, and SOP progress.
- Missing backend/operator behavior must be marked as a gap until connected.

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
- Sites: customer-friendly site cards/table with create/open/support actions; advanced operations are locked by default.
- Create Site: dedicated guided flow for site creation requests.
- Account: customer identity, region preference, subscription/billing placeholders, and linked account context.

Customer action placement:

- `Create Site` must be a first-class route and prominent CTA.
- Customer create/support actions must appear in the main page body or site detail surface, not only in the inspector. Advanced operations must appear as locked/qualified features, not normal customer actions.
- The inspector may provide context, assistant help, technical metadata, and request history.
- Missing backend behavior must be shown as pending/unavailable/captured-as-request; locked advanced operations must be labeled as qualification/platform-managed features. Do not implement backend business logic in this pass.

Create Site state model references:

- Customer: signed-in account and customer identity.
- Subscription: plan/product placeholder until backend subscription behavior is wired through the configured billing system.
- Site: requested tenant instance and eventual provisioned site.
- Region: preferred placement source, displayed customer-friendly even though Region is a platform tree doctype.
- Bench: platform placement target with current Release and next Release context, not directly editable by the customer in the first pass.
- Platform Settings: `root_domain` is mandatory for customer domain previews; customers enter subdomains only.

## Commercial And Integration Workflow

Commercial and relationship information is surfaced in LensCloud but sourced from external systems configured in `Platform Settings`.

- `billing_system` is the primary source for invoicing, finance status, plan, renewal, and payment-state summaries.
- `crm_system` is the primary source for account relationship, onboarding, and lifecycle/customer-stage summaries.
- `support_system` is the primary source for support tickets, escalation state, and support redirects.
- Customers see summaries and support redirects only; they do not get direct billing-system or CRM-system access from LensCloud.
- Platform agents see extended billing, CRM, and support context and may use Frappe SSO links to external systems when configured.
- Frappe SSO setup is handled outside this frontend implementation and must not be implemented here.

## Customer Domain Workflow

Customer-created sites use the platform root domain in this pass.

- Customers enter a preferred subdomain/name only.
- The final domain preview is `{preferred_subdomain}.{Platform Settings.root_domain}`.
- If `root_domain` is missing, Create Site must clearly show a Platform Settings gap and prevent normal submission.
- Subdomain validation is frontend-only in this pass and must not imply backend reservation has happened.

## Locked Advanced Operations

Backup, restore, upgrade, advanced DNS, suspend, and delete are not first-class customer features by default.

- Show these as locked features that require LensCloud qualification/certification or platform-team handling.
- Do not label locked features merely as backend gaps.
- Platform console may expose these actions as operator entry points while still marking missing backend/orchestration behavior as gaps.

## Region Tree Workflow

Region is a native Frappe tree doctype. Platform-facing Region views must support both tree and list modes.

- Tree mode uses `parent_region` as the parent field.
- Group nodes use `is_group`.
- Ordering should follow nested-set fields such as `lft`/`rgt` where available.
- List mode remains available for filtering, scanning, and standard record work.

## Document Lifecycle Workflow

Frappe document lifecycle actions are first-class UI actions in the platform console.

- Master data such as `App` and `Release Group` can be created through the platform resource workspace.
- `Release` is a submittable transaction and should move through Draft, Submitted, Cancelled, and Amended states using native Frappe document APIs.
- Document lifecycle actions must not be confused with infrastructure lifecycle actions. Submit/cancel a `Release` records the platform transaction; it does not deploy infrastructure.

## Frontend Execution Order

The canonical frontend work-item list and status tracker is the `Frontend Handover Tracker` table in `docs/agent-handoff.md`.

1. Work on the row marked `Next` before starting later pending rows.
2. Update that tracker table as work changes status.
3. Do not duplicate the frontend tracker in this file.
4. Every phase must end at its stop point and wait for explicit confirmation before scope expansion.

## Frontend Guardrails

- Keep the first pass scoped to the workspace shell, platform inspector, customer dashboard/sites/create-site/account pages, and action entry points.
- Use native Frappe authentication and permissions for access control.
- Keep the platform-console and customer-portal surfaces separate by role.
- Mark missing backend behavior as a gap instead of assuming it exists.
- Keep the platform/infrastructure boundary explicit at all times.
