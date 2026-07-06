# Customer Identity And Access Model

## Purpose

LensCloud Platform is the Central User Access system for LensCloud customers. Customers and invited users authenticate through the Platform, not through individual provisioned Sites. Sites consume access decisions from Platform-mediated identity and access flows.

## Launch Boundary

The immediate Free-first launch supports native LensCloud/Frappe authentication, customer account linkage, Plan browsing, Free subscription, and automatic Site provisioning. User invitation, fine-grained RBAC, SSO into Sites, and deactivation flows are documented here but implemented in later passes.

## lmnas.com Signup Handoff

The intended website handoff is a signed token flow from `lmnas.com` into LensCloud Platform. The external website may collect marketing/signup context and then redirect to LensCloud with a short-lived token.

Minimum token claims for the future contract:

```json
{
  "email": "customer@example.com",
  "full_name": "Customer Name",
  "company": "Example Company",
  "selected_plan": "Free",
  "region_hint": "EU",
  "issued_at": "ISO-8601",
  "expires_at": "ISO-8601",
  "nonce": "unique-value"
}
```

The token receiver is not implemented in this pass. E2E testing uses native LensCloud login/signup and records the token handoff as an integration gap.


## Signup To Customer Assignment

Launch rule: public/native signup is customer-only. Platform users do not self-register; they are created or granted by Platform administrators. After signup, LensCloud must create or link customer identity before the user begins Plan selection.

Signup assignment policy:

- A new Website User created through native Frappe signup is treated as a customer user.
- If the signup email uses a public email domain such as Gmail, Outlook, Yahoo, iCloud, or Proton, LensCloud creates an individual Customer for that user.
- If the signup email uses a company domain and no Customer exists for that domain, LensCloud creates a Customer with that primary domain and makes the signup user the active Owner.
- If a Customer already exists for the same company domain, LensCloud creates a Customer Member in `Pending` state under that Customer. Pending members can sign in, but cannot provision Sites until approved.
- Platform-created System Users and users with Platform roles are never auto-converted into Customers.
- Existing `Customer.user` remains the backward-compatible primary owner link for launch, while `Customer Member` becomes the CUA membership truth.
- Legacy Customers that do not have `primary_domain` are not used for same-domain matching. Platform operators must explicitly set the primary domain before future same-domain signups can be grouped under that Customer.
- Frappe's native signup response `Please ask your administrator to verify your sign-up` means the User account/email could not be auto-verified by email. It is not the LensCloud Customer Member approval state. The authoritative LensCloud access state is `Customer Member.status`.

Customer membership model:

- `Customer Member` links Customer and User.
- Role values: Owner, Admin, Member, Viewer.
- Status values: Active, Pending, Disabled.
- Source values: Signup, Domain Match, Invite, Platform.
- The first signup owner is Active and primary owner. Same-domain self-signups are Pending by default.

Native Role Profile and permission rules:

- Platform Settings may define `default_customer_admin_role_profile` and `default_customer_member_role_profile`. If those fields are blank during launch, LensCloud falls back to conventional Role Profile names `LensCloud Customer Admin` and `LensCloud Customer Member` when they exist.
- Active Owner/Admin memberships receive the admin Role Profile. Pending, Member, and Viewer memberships receive the member Role Profile.
- Customer portal menus and actions are driven by native Frappe DocType permissions, not by hard-coded frontend role names. If a Role Profile grants read access to Plan, the Plans menu appears and Plan records load. If it removes read access, the menu is hidden and direct access shows a permission state.
- Subscription creation is controlled by native `Subscription` create permission. A customer member may browse Plans when Plan read is granted, but cannot create a Subscription unless the assigned Role Profile grants Subscription create.
- LensCloud creates or repairs a Frappe `User Permission` for `Customer` so ORM reads stay customer-scoped. If that User Permission is missing for older records, customer APIs still restrict reads to the active membership or legacy `Customer.user` link before returning data.
- `Customer Member` read/write permission controls the customer Members menu and approval action. Approval is checked again server-side and only applies within the actor's Customer.
- Legacy Customers with `Customer.user` but no `Customer Member` row are treated as active Owner for access repair, Role Profile assignment, and Customer User Permission creation.

Landing and access rules:

- Users with explicit Platform roles land in Platform.
- Frappe website home-page fallback must route LensCloud users to `/lenscloud/customer/dashboard` or `/lenscloud/platform/dashboard`; customer users must not be stranded on `/me`.
- Signup/customer-only users land in Customer Dashboard.
- Customer-only users cannot open Platform routes.
- Pending Customer Members see customer-safe pending approval guidance and cannot subscribe or provision.
- Active Customer Members can browse Plans and subscribe according to Plan policy.

ERPNext boundary:

ERPNext may later become the billing/customer commercial truth. Until that integration is built, LensCloud Platform owns local customer access, membership, role assignment, pending approval, and launch-time RBAC. Future ERPNext sync must not weaken Platform-side access checks.

## Customer Access Principles

- Platform owns customer identity, invitation, deactivation, role assignment, and audit.
- Customers never manage Kubernetes namespaces, Benches, Database Servers, Secrets, CR names, or runtime credentials.
- Customers choose Plan, Region, and subdomain; Platform resolves Subscription, Environment, Bench, Database, and Site Control policy.
- Free Plan self-approves and provisions one Prod Site. Paid/beta Plans request approval and do not provision until the approval/payment contract is complete.
- All sign-in to Sites should eventually use Platform-mediated access or SSO; direct Site-local user administration is not the customer-facing model.


## Site Bootstrap And SSO Automation

CUA moves from account membership into provisioned Site access through `docs/architecture/cua-site-bootstrap-sso-sequence.md`. The approved direction is Kubernetes API Bench Execute, not browser/API calls to target Sites using Administrator passwords.

Platform must automate these Site access responsibilities after a Site is Ready:

- complete the target Site setup wizard using the INF-021 Bench Command runner commands `site_setup.status` and `site_setup.complete`, with Customer, Subscription, Plan, Landscape, Environment, and Site Control defaults as non-secret typed args;
- configure the target Site to trust LensCloud Platform as OAuth/OIDC/Social Login authority;
- create or sync the first Customer Owner/Admin user on the Site without exposing a password;
- create, sync, revoke, and audit Site Access Grants for Customer Members;
- show `Open Site` only when Site Ready, setup complete, OAuth configured, and current member has an Active access grant;
- route users from Platform to assigned Sites without a password prompt;
- revoke target Site access when membership or Site Access Grant is disabled.

Administrator password may exist only as an Infra/operator-side bootstrap implementation detail if absolutely required by the runner. It must never be accepted from the browser, returned by Platform APIs, or written into action logs/evidence.

The setup-wizard slice is implemented before full SSO. Provisioning progress should therefore show `Checking setup status` and `Setting site defaults` as active states, while OAuth/social login and member Site access remain clearly marked as future/unsupported until Infra publishes and verifies those runner contracts.


## Future CUA Work

- Customer user invitations and acceptance.
- Customer roles and role profiles for owner, admin, developer, tester, and viewer.
- Site access grants per Subscription and Environment.
- SSO/session handoff from Platform to provisioned Sites through the Bench Execute runner contract.
- User deactivation and access revocation across Sites.
- Audit trail for access grants, login handoffs, and role changes.
- Platform operator views for customer users and access state.

## Dashboard And Account Responsibility Split

Dashboard is the customer's service command center. It answers: `What should I do next with my LensCloud service?` It owns onboarding state, the next service action, subscription progress, Site readiness, usage cards, support-needed alerts, and quick links to Subscriptions, Plans, and ready Sites.

Account is the customer's identity and trust surface. It answers: `Who am I, what organization do I belong to, and how is access governed?` It owns signed-in identity, Customer/company profile, default region preference, role/status summaries, Central User Access guidance, invite/user-management placeholders, account-level support/billing contact placeholders, and read-only links back to Subscriptions.

Duplication rules:

- Dashboard may show identity snippets only when they help the service journey, such as signed-in customer name or default Region.
- Dashboard must not edit profile, organization, support contact, billing contact, or access preferences.
- Account may show Subscription/Site counts only as references with links to Subscriptions.
- Account must not show provisioning-heavy timelines, Plan comparison, Free checkout, or Site runtime management.
- Account must never expose Bench, Database Server, Runtime Namespace, Kubernetes, CR names, Secrets, action logs, pod logs, kubeconfig, or raw operator resource names.

Navigation rules:

- Customer primary navigation carries Dashboard, Plans, and Subscriptions.
- Account belongs in a bottom/profile-settings navigation area, visually separate from the launch workflow.
- Support may join the bottom area in a later pass.

## Customer Account And Access Page

The Account page should feel personal, steady, and trustworthy. It should reassure customers that LensCloud Platform is their Central User Access home while clearly labeling future functionality.

Main area:

- Hero card: signed-in identity, Customer/company, account status, and one sentence of reassurance.
- Profile card: first name, last name, default Region, and external customer reference when present.
- Organization card: Customer record, company/customer name, preferred Region, and support context.
- Access card: LensCloud Platform is the access home; Site access is managed here, not independently inside Sites.
- Team/Invites card: future CUA user invites and role management, marked coming soon.
- Support/Billing contact card: account-level contacts and external-system placeholders, marked configured/coming soon as appropriate.

Inspector:

- Identity context.
- Customer record and default Region.
- CUA roadmap summary.
- Subscription reference counts with links to Subscriptions.

Tone:

- Use customer-safe language: account, organization, access, team, support, trust, signed in, service subscription.
- Avoid infrastructure or operator language.
- Make every future capability explicit as `Coming soon` or `Platform-managed`, not a fake working control.
