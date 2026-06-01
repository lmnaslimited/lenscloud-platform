# LensCloud Platform Agent Handoff

## Purpose

This repository is the product layer for the `lenscloud` app. It is Frappe-first, customer-facing, and role-aware.

## Agent Roles

- Platform Product Agent: owns customer lifecycle, subscriptions, site requests, and platform workflows.
- UI/UX Agent: owns Frappe UI structure and customer/platform navigation.
- Operator Integration Agent: ensures work matches the actual Frappe Operator contract.
- SOP/Docs Agent: keeps the repo handoff-ready and prevents scope drift.

## Skills To Associate

- `lenscloud-platform-sop`
- `frappe-ui-product`
- `frappe-operator-integration`
- `route53-automation`

## MCPs To Use

- Kubernetes MCP for operator and cluster inspection
- Route53 automation layer for DNS lifecycle work
- GitHub tooling for repo handoff and PRs

## Operator Truth

- `FrappeBench`, `FrappeSite`, `SiteBackup`, and `SiteRestore` are the implemented operator workflows to rely on.
- `SiteJob` is scaffolded and should not be treated as a production feature unless the codebase is explicitly updated to prove otherwise.

## Repo Boundary

- This repo owns the `lenscloud` app and product workflows only.
- Infra/bootstrap belongs in `lenscloud-infra`.

## Handover Objects

These handover objects define the ordered frontend work for LensCloud Platform. Agents must complete them in sequence and stop at every phase boundary until the phase owner confirms the next step.
The LensCloud shell is a control-plane workspace, not a literal CRM clone:
- left navigation keeps scope and session context
- the main workspace carries operational lists, timelines, actions, and dashboards
- the right contextual inspector carries record summary, editable fields, status, related objects, and history
- the AI assistant is an optional drawer attached to the inspector, not a permanent competing pane
- read-only status surfaces must stay visually separate from editable document fields

### Handover Object 1: Workspace Contract and Role Map

- Owner: UI/UX Agent + Platform Product Agent
- Goal: Define the LensCloud workspace contract, route map, and role split for platform-console and customer-portal surfaces.
- Work items:
  1. Define the shared workspace shell structure using Frappe UI patterns adapted for platform-engineer workflows.
  2. Define the platform-console vs customer-portal navigation model.
  3. Define the main workspace, right contextual inspector, and optional AI assistant drawer contract.
  4. Specify how read-only status, editable fields, and action entry points are separated in the inspector.
  5. Align the route map with native Frappe auth and permissions.
- Dependencies:
  - `README.md`
  - `requirements.md`
  - `docs/state-model.md`
  - `docs/workflows.md`
  - CRM frontend shell patterns as a reference for split-workspace behavior
  - Press dashboard patterns as a reference for cloud-control workflows
- Expected outcome:
  - A confirmed workspace contract and role map that can be implemented without further ambiguity.
- Stop point:
  - Stop after the workspace contract, route map, and role split are confirmed.

### Handover Object 2: Shared Workspace Shell

- Owner: UI/UX Agent
- Goal: Build the shared workspace shell and page framing for the platform console and customer portal.
- Work items:
  1. Create the shared workspace shell around the existing routes without breaking page URLs.
  2. Add a reusable page header, action bar, and context strip for the main workspace.
  3. Add a right contextual inspector that can render read-only summary, editable fields, lifecycle status, related objects, and history.
  4. Keep the first pass read-heavy and action-light.
- Dependencies:
  - Handover Object 1
  - Existing doctypes
  - Native Frappe auth and permissions
  - `docs/state-model.md`
- Expected outcome:
  - A usable shared workspace with consistent page framing and an inspector rail.
- Stop point:
  - Stop after the shared shell and inspector contract are confirmed.

### Handover Object 3: Inspector-Driven Doctype Management

- Owner: Platform Product Agent + UI/UX Agent
- Goal: Build doctype-specific inspector behavior for platform and customer records.
- Work items:
  1. Add platform-facing inspector views for Customer, Release Group, Bench, Site, Region, and Platform Settings.
  2. Add customer-facing inspector views for account and site lifecycle surfaces.
  3. Group fields clearly into summary, editable fields, lifecycle status, related objects, and history.
  4. Add lifecycle action entry points for site create, suspend, delete, backup, restore, upgrade, and DNS automation.
  5. Mark any missing backend behavior as a gap instead of assuming it exists.
- Dependencies:
  - Handover Object 1
  - Handover Object 2
  - Native Frappe login and role checks
  - `docs/workflows.md`
  - `docs/state-model.md`
  - `lenscloud-infra` operator contract, read-only reference only
- Expected outcome:
  - A control-plane inspector that supports platform engineers first and customer workflows second.
- Stop point:
  - Stop after the inspector behavior for at least one doctype is confirmed.

### Handover Object 4: Assistant Drawer and Validation

- Owner: Platform Product Agent + UI/UX Agent
- Goal: Add the assistant drawer and validate that the workspace matches the documented state model.
- Work items:
  1. Reserve and wire the assistant drawer inside or alongside the inspector.
  2. Make the assistant context-aware using scope, doctype, record, and action state.
  3. Wire permissions, empty states, loading states, and error states.
  4. Add audit/history placeholders and recent-action surfaces.
  5. Validate that every action shown in the UI maps to a real backend or is explicitly marked unavailable.
  6. Ensure the frontend stays inside the platform/infrastructure boundary.
- Dependencies:
  - Handover Objects 1-3
  - Native Frappe permissions
  - `docs/state-model.md`
  - `docs/workflows.md`
- Expected outcome:
  - A role-aware, auditable frontend with an assistant drawer that feels native to the workspace.
- Stop point:
  - Stop after the validation pass is confirmed and before any expansion beyond the first frontend pass.

## Agent Execution Order

1. The UI/UX Agent and Platform Product Agent must complete Handover Object 1 first.
2. No frontend implementation may begin until Handover Object 1 is confirmed.
3. The UI/UX Agent completes Handover Object 2 next, using the approved workspace contract.
4. The Inspector-Driven Doctype Management work in Handover Object 3 may begin only after the shared shell is in place.
5. Handover Object 4 is the final pass and must not start until the earlier objects are complete.
6. Every phase ends with a stop point that requires confirmation before the next phase begins.

## Agent Instructions

### UI/UX Agent

- Use Frappe UI patterns as the frontend foundation.
- Use CRM frontend shell patterns as a reference for split-workspace behavior, not as a literal product template.
- Follow Press dashboard conventions for cloud-platform surfaces, status views, and action-oriented pages.
- Keep the platform-console and customer-portal experiences clearly separated by role.
- Build the right contextual inspector to hold summaries, editable fields, status, related objects, and history.
- Keep the assistant drawer optional and secondary to the inspector.
- Do not build around Desk-only customization unless a specific screen requires it.
- Keep the interface Frappe-native, compact, and workflow-oriented.
- Do not expose platform-only actions to customer roles.
- Stop at every phase boundary and wait for confirmation.

### Platform Product Agent

- Keep LensCloud as the control plane and do not drift into infrastructure implementation.
- Keep the platform/infrastructure boundary explicit at all times.
- Use native Frappe authentication and role-based permissions.
- Make sure lifecycle actions, status views, and audit surfaces match the documented state model.
- Ensure read-only status and editable fields stay visually distinct in the inspector.
- Any missing backend behavior must be marked as a gap, not assumed.
- Confirm whether each action is customer-facing, platform-facing, or shared before the UI is built.
- Stop at every phase boundary and wait for confirmation.

### Operator Integration Agent

- Treat `lenscloud-infra` as read-only reference context.
- Use it only to understand the operator and lifecycle contract.
- Do not modify `lenscloud-infra`.
- Do not invent lifecycle behavior that the contract does not support.
- Keep the action UI aligned with the implemented operator workflows.
- Flag any dependency on missing operator behavior early.

### SOP / Docs Agent

- Keep the docs handoff-ready and ordered.
- Preserve the phase order and stop points.
- Keep the workspace contract explicit: main workspace, contextual inspector, optional assistant drawer.
- Record assumptions, gaps, and unresolved backend dependencies.
- Make sure work items stay short, testable, and explicitly owned.
- Do not let the handoff drift into vague “build the frontend” language.

## Phase Completion Rule

A phase is complete only when:

- its work items are finished,
- its dependencies are understood,
- any backend gaps are documented,
- and the owner confirms the stop point has been reached.

No later phase may begin until that confirmation is recorded.
