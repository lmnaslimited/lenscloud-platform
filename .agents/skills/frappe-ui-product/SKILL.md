---
name: frappe-ui-product
description: Build or review LensCloud Vue interfaces using Frappe UI components and established Frappe CRM patterns. Use for pages, forms, dialogs, lists, navigation, status views, responsive behavior, accessibility, and UI polish where the result should remain recognizably Frappe-native instead of becoming a bespoke design system.
---

# Frappe UI Product

Use this workflow for every LensCloud frontend change.

## Before Editing

1. Read `references/lenscloud-ui-contract.md`.
2. Read `references/frappe-ui-patterns.md` for the relevant interaction.
3. Inspect the current page, neighboring LensCloud components, and installed
   `frappe-ui` APIs before adding a component or wrapper.
4. Identify the real backend state and permissions. Do not design a successful
   state that the backend cannot produce.

## Implementation Rules

- Prefer Frappe UI components, variants, tokens, and resource APIs.
- Reuse existing LensCloud layout and interaction components before creating
  another abstraction.
- Use Frappe CRM `main` only as a structural reference compatible with Frappe
  v16. Do not copy `develop`/future-v17 behavior without verifying compatibility.
- Keep platform screens compact, operational, and easy to scan.
- Keep customer screens simpler and task-oriented; do not expose infrastructure
  terminology or platform-only controls.
- Put primary commands in page action surfaces. Use the inspector for context,
  editable details, status, related records, and history.
- Use icons from the existing icon library and add tooltips for unfamiliar
  icon-only actions.
- Implement loading, empty, permission-denied, error, disabled, confirmation,
  progress, success, and retry states where the workflow can reach them.
- Display backend and operator status as authoritative. Never fake completion
  with client-only state.
- Avoid decorative dashboards, nested cards, oversized headings, custom control
  primitives, and one-off CSS when a Frappe UI pattern already exists.

## Validation

- Build the frontend.
- Test keyboard focus, labels, disabled controls, and destructive confirmations.
- Check desktop and mobile widths for overlap, truncation, and horizontal scroll.
- Run Playwright through the actual platform or customer workflow.
- Confirm browser console errors are absent.
- Confirm customer users cannot see platform-only fields, actions, or secrets.
- Summarize reused Frappe UI patterns and any justified custom component.
