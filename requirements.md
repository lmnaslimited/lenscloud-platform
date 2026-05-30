# LensCloud Platform Requirements

## Product Goal

Build a Frappe-based platform application that serves both customer self-service and platform operations, with native Frappe authentication and role-based access.

## 1. Identity and Access

- The platform must use native Frappe signup and login.
- The platform must support role-based access for customers and platform users.
- The platform must support account ownership and delegated access.
- The platform must keep `lmnas.com` as the acquisition surface and LensCloud as the authenticated product surface.

## 2. Customer Lifecycle

- The platform must represent customers as first-class entities.
- The platform must support subscription and plan management.
- The platform must allow a customer to request a site using their company name as a subdomain.
- The platform must support account management for the customer lifecycle.
- The platform must enforce plan limits during self-service site creation.

## 3. Site Lifecycle

- The platform must represent sites as tenant instances inside benches.
- The platform must support site creation, status tracking, suspension, and deletion.
- The platform must support region selection for site placement.
- The platform must support quality vs production separation in site placement.

## 4. Bench and Release Groups

- The platform must represent benches as release-group instances.
- The platform must treat a release group as the unit of bench image management.
- The platform must support bench creation, upgrade, rollback, and retirement.
- The platform must enforce site-to-bench placement rules.

## 5. DNS and Domain Automation

- The platform must automate customer subdomain creation.
- The platform must automate Route53 record creation, update, and deletion.
- The platform must surface DNS provisioning status and failures in the UI.
- The platform must keep DNS operations auditable and retryable.

## 6. Backup, Restore, and Upgrades

- The platform must support scheduled and on-demand backups.
- The platform must support restore workflows.
- The platform must support upgrade orchestration by release group or image tag.
- The platform must keep an audit trail of backup, restore, and upgrade actions.

## 7. Platform Operations

- The platform must support customer directory management.
- The platform must support environment management.
- The platform must support policy enforcement.
- The platform must support approval and exception handling for managed customers.

## 8. Observability and Audit

- The platform must surface action history.
- The platform must surface job and provisioning status.
- The platform must surface operational logs and traceability.
- The platform must maintain an auditable history of all lifecycle actions.

## 9. Operator Integration

- The platform must use Frappe Operator resources for bench and site lifecycle.
- The platform must not reimplement Kubernetes runtime reconciliation.
- The platform must treat operator resources as the source of truth.
- The platform must support a controlled allowlist of bench commands when needed.

## 10. UI

- The platform must provide a Frappe-based UI and API.
- The same app must serve customer self-service and platform console, separated by roles.
- The UI must support customer, bench, site, backup, restore, and upgrade workflows.
- The UI must surface status, logs, and recent actions.

## Non-Functional Requirements

- Containerized deployment only.
- Region-aware and multi-cluster friendly.
- Auditable and permissioned by role.
- Safe defaults for destructive operations.
- Suitable for enterprise data-residency workflows.

## Open Decisions

- Primary metadata database choice.
- Whether the first version is single-cluster or multi-cluster aware.
- Whether upgrade orchestration is synchronous or job-based.
- Whether Route53 status is customer-visible or platform-only in the first version.
