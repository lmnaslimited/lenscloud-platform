# E2E Incident Follow-Up Prompt - LC-E2E-20260703-003

Work inside `/workspace/frappe-bench/apps/lenscloud`.

Read first:
- `AGENTS.md`
- `.agents/skills/frappe-ui-product/SKILL.md`
- `.agents/skills/frappe-ui-product/references/lenscloud-ui-contract.md`
- `.agents/skills/frappe-ui-product/references/frappe-ui-patterns.md`
- `docs/incidents/e2e-incident-tracker.md`
- `docs/evidence/customer-launch/e2e-acceptance-20260702.md`

Incident:
- `LC-E2E-20260703-003`
- Reopened on 2026-07-03 after user retest: the Account widget and dialog placement exist, but the Change Password fields are not editable in the operator-visible browser session, so the password cannot be updated.
- Customer Account actions must remain in the account/profile floating widget from the shell account affordance. `Sign Out` belongs in the widget. `Change Password` belongs in the widget and opens a compact dialog inside the Account page without navigating to `/update-password`.

Required fix:
1. Keep Account actions in the shell account widget.
2. Keep Account page focused on identity/access content; no header-level Sign Out or Change Password buttons.
3. Route widget `Change Password` to `/customer/account?changePassword=1` and open an in-page dialog.
4. Make password inputs deterministic and editable. Prefer plain native inputs in a minimal modal if the Frappe UI Dialog focus layer is unreliable in this devcontainer/browser combination.
5. Use the native Frappe password update API from the dialog; do not expose passwords in logs or docs.
6. Keep `Sign Out` in the widget and route to `/login` after logout.
7. Retest with an assertion that types into Current Password, New Password, and Confirm New Password and verifies the values are accepted. Do not accept a test that only verifies the dialog opens.

Retest:
- `npm --prefix frontend run build`
- `LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth`
- `LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth`
- confirm no forced all-caps classes remain in Vue surfaces.
- targeted browser probe: open `/lenscloud/customer/account?changePassword=1`, fill all three password fields, and confirm DOM input values changed without submitting real password data.

Closure:
- Update `docs/incidents/e2e-incident-tracker.md` to Closed.
- Update `docs/evidence/customer-launch/e2e-acceptance-20260702.md` with a new UX scenario row or note.
- Update `docs/handoffs/platform/agent-handoff.md` with the result and remaining risks.
