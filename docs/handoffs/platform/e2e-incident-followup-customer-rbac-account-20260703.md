# E2E Incident Follow-Up Prompt - LC-E2E-20260703-004

Work inside `/workspace/frappe-bench/apps/lenscloud`.

Read first:
- `AGENTS.md`
- `.agents/skills/frappe-ui-product/SKILL.md`
- `.agents/skills/frappe-ui-product/references/lenscloud-ui-contract.md`
- `.agents/skills/frappe-ui-product/references/frappe-ui-patterns.md`
- `docs/architecture/customer-identity-access.md`
- `docs/incidents/e2e-incident-tracker.md`

Incident:
Customer Account/RBAC validation found that password input does not accept values, the account widget has hardcoded green/`Go`, Platform password change routes to Customer Account, customer member approval lacks a first-class customer portal menu, and active non-admin members can start subscriptions.

Required fix:
1. Change Password must accept input and update through Frappe's native password API without exposing password values.
2. Account widget must use LensCloud theme colors and show a useful caption such as recent active Plan for customers.
3. Platform users must not be routed to Customer Account for password change.
4. Signup/member activation must assign the Platform Settings default customer admin/member Role Profiles and create Customer User Permission rows.
5. Customer portal Members menu and approval must be visible/allowed by native Frappe permissions, not hardcoded role strings.
6. Customer subscription requests must require native `Subscription` create permission in addition to active membership.
7. Update tests, SOP, architecture, evidence, and close this incident after retest.

Retest:
- customer identity backend tests;
- production frontend build;
- authenticated desktop/mobile Playwright;
- permission evidence for admin vs member subscription/member approval.
