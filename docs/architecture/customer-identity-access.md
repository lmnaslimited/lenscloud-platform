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

## Customer Access Principles

- Platform owns customer identity, invitation, deactivation, role assignment, and audit.
- Customers never manage Kubernetes namespaces, Benches, Database Servers, Secrets, CR names, or runtime credentials.
- Customers choose Plan, Region, and subdomain; Platform resolves Subscription, Environment, Bench, Database, and Site Control policy.
- Free Plan self-approves and provisions one Prod Site. Paid/beta Plans request approval and do not provision until the approval/payment contract is complete.
- All sign-in to Sites should eventually use Platform-mediated access or SSO; direct Site-local user administration is not the customer-facing model.

## Future CUA Work

- Customer user invitations and acceptance.
- Customer roles and role profiles for owner, admin, developer, tester, and viewer.
- Site access grants per Subscription and Environment.
- SSO/session handoff from Platform to provisioned Sites.
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
