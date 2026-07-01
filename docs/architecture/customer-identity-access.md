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
