# E2E Incident Follow-Up: Document Actions

Date: 2026-07-07  
Incident: `LC-E2E-20260707-009`  
Owner: Platform

## Problem

Platform users cannot reliably manage native Frappe document lifecycle actions from the shared ResourcePage editor. Submittable LensCloud documents such as Plan, Privacy Profile, and Site Control Profile need visible Submit, Cancel, and Amend actions. Documents with native delete permission need a Delete action. These actions must use Frappe's standard document APIs and DocPerm checks.

## Required Fix

- Expose native DocType permissions in `lenscloud.api.launch.get_doctype_editor_schema`:
  - submit;
  - cancel;
  - amend;
  - delete.
- Render document actions in the main editor header, not only buried in diagnostics.
- Use native Frappe APIs for create, save, submit, cancel, amend, and delete.
- Keep submitted documents read-only unless the field allows update-after-submit through backend rules.
- Require confirmation before delete.
- Let Frappe enforce final authorization server-side.

## Retest

- Backend policy/schema test confirms Plan is submittable and reports submit/cancel/amend/delete permission bits.
- Frontend build passes.
- Focused browser smoke verifies a Plan detail page shows lifecycle actions and delete is not shown unless allowed.
- Update `docs/incidents/e2e-incident-tracker.md`, `docs/evidence/platform-console/platform-document-actions-20260707.md`, and SOP regression checklist.

## Resume Point

After closure, resume Platform/customer E2E from the Platform catalog/admin sanity segment, then continue Free-first customer flow.


## Singleton Correction

The same Platform metadata/admin surface also covers singleton doctypes. Singleton resources such as Platform Settings must not show list view chrome, row counts, Refresh, or New actions. They should load the singleton document directly in the main detail editor and use the existing full-screen editor affordance for focus.
