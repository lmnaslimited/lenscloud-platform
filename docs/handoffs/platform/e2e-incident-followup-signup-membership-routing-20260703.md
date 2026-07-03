# Platform Follow-Up Prompt - LC-E2E-20260703-001

Work inside `/workspace/frappe-bench/apps/lenscloud`. Start by reading `AGENTS.md`, `docs/incidents/e2e-incident-tracker.md`, and `docs/architecture/customer-identity-access.md`.

Incident: additional customer signup/member assignment and landing route are inconsistent. A user reported signing up `user2@example.com`; UI displayed approval guidance, but the created Customer Member was Active Owner and primary owner. Login then landed at `/me` instead of LensCloud Customer portal. Platform sidebar also did not show Customer Members.

Required fix path:

1. Reproduce or inspect the affected Customer/User/Customer Member records without exposing credentials.
2. Decide whether this is a documented requirement gap or implementation defect; update architecture/workitems/SOP accordingly.
3. Fix signup assignment so:
   - legacy Customers without `primary_domain` do not produce contradictory approval messaging;
   - same-domain matching uses a deliberate domain ownership record, not accidental public/test domains;
   - additional company-domain users become Pending members only when a Customer has a matching primary domain;
   - new independent signups become Active Owner/primary owner of their own Customer;
   - pending members land in Customer Account pending state and cannot provision;
   - post-login never leaves customer-only users stranded at `/me`;
   - Platform operators can access Customer Members from sidebar/navigation after build/migration.
4. Add or update backend tests for legacy Customer without domain, same-domain pending, independent public-domain signup, and native signup redirect expectations.
5. Run migration if metadata changed, backend tests, frontend build, and authenticated desktop/mobile route smoke.
6. Update `docs/incidents/e2e-incident-tracker.md`, `docs/evidence/customer-launch/e2e-acceptance-20260702.md`, and handoff docs with fix/retest evidence.

Do not mutate cluster/runtime resources for this incident. Do not expose passwords or reset tokens.
