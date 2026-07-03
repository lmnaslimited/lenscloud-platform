# Platform Follow-Up Prompt - LC-E2E-20260703-002

Work inside `/workspace/frappe-bench/apps/lenscloud`. Start with `AGENTS.md` and the Frappe UI skill references before frontend changes.

Incident: customer Account and Subscription pages have incomplete/wonky actions and inconsistent label casing.

Fix requirements:

1. Account page must expose native Sign Out and Change Password actions.
2. Account header must remove noisy `Linked` badge and Refresh action.
3. Account primary actions must be visually coherent; `View Subscriptions` must keep icon/text in one row and not distort mobile/desktop layout.
4. Subscription page `Choose a Plan` / `Add New Subscription` actions must be wired to `/customer/plans` and keep icon/text on one row.
5. Customer and Platform headings/labels should use Pascal Case/normal title case, not forced all-caps tracking styles. Paragraph copy can remain sentence case.
6. Run frontend build and authenticated desktop/mobile smoke.
7. Update `docs/incidents/e2e-incident-tracker.md`, `docs/evidence/customer-launch/e2e-acceptance-20260702.md`, and handoff docs with closure evidence.
