# Frappe UI Patterns

## Source Order

1. Installed `frappe-ui` package and its local component APIs.
2. Existing LensCloud components and page conventions.
3. Frappe CRM `main` frontend patterns compatible with Frappe v16.
4. Official Frappe Framework and Frappe UI documentation.

Do not introduce another UI framework.

## Components

- Use Frappe UI buttons, inputs, textareas, dialogs, alerts, tabs, badges,
  dropdowns, tooltips, list/resource helpers, and toast patterns when available.
- Use native controls for links, selects, checkboxes, and dates through the
  matching Frappe UI component or established LensCloud field renderer.
- Prefer one shared component only when it removes meaningful duplication across
  workflows. Do not wrap every Frappe UI component.
- Keep status badges semantic and consistent. Status is not an editable field
  unless the workflow explicitly allows a transition.

## Data And Actions

- Use Frappe document/resource APIs for DocType CRUD and whitelisted server
  methods for orchestration.
- Keep mutations server-authoritative and refresh the resource after success.
- Show a spinner or progress state while a command is running.
- Disable duplicate submission and provide a useful retry after failure.
- Require confirmation for destructive or externally consequential actions.
- Render permission failures distinctly from network or validation failures.

## Layout

- Platform console: dense list or dashboard in the main workspace, contextual
  inspector on the right, optional assistant drawer secondary to both.
- Customer portal: focused page flow with one obvious primary action and minimal
  infrastructure detail.
- Keep cards for repeated records, dialogs, or genuinely framed tools. Do not
  place cards inside cards.
- Use compact headings inside work surfaces. Reserve large display type for a
  true product entry screen.
- Preserve stable dimensions for toolbars, icon buttons, tables, tabs, and status
  strips so dynamic text does not shift the layout.

## Accessibility And Responsive Behavior

- Every input has a visible label.
- Every icon-only action has an accessible name and tooltip.
- Keyboard users can reach and operate dialogs, menus, tabs, and actions.
- Focus remains visible and returns sensibly after dialogs close.
- Text wraps or truncates deliberately; it must not overlap adjacent controls.
- Validate customer and platform routes at desktop and mobile widths.
