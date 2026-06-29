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

## 4. Release Groups, Releases, and Benches

- The platform must represent Release Group as master data for a release family, not as a deployable version.
- Release Group must hold stable product/image-family configuration such as registry URL, image repository, included apps, supported Frappe major version, and release policy.
- The platform must introduce Release as the transactional deployable version for a Release Group.
- Release must hold image tag, image digest when available, build status, pipeline/build reference, release status, changelog, compatibility notes, and promotion state.
- Bench must link to a Release Group and deploy a specific current Release of that group.
- Bench must support current release, next release, upgrade schedule/window, upgrade policy, and upgrade status.
- Release Group views must summarize number of benches and their release levels.
- Bench views must show current release level, next release level, and platform-team SOPs for moving to the next release.
- The platform must support bench creation, release upgrade, rollback, retirement, and site-to-bench placement rules.

## 5. DNS and Domain Automation

- The platform must automate customer subdomain creation.
- Standard Sites must not create, update, or delete DNS records.
- `cloud.lmnaslens.com` and its wildcard are infrastructure-owned GoDaddy DNS records.
- The platform consumes only non-secret wildcard DNS/TLS/ingress readiness from the Cluster handoff.
- The platform must surface DNS provisioning status and failures in the UI.
- The platform must keep DNS operations auditable and retryable.

## 6. Backup, Restore, and Upgrades

- The platform must support scheduled and on-demand backups.
- The platform must support restore workflows.
- The platform must support upgrade orchestration by Release and scheduled Bench upgrade plans.
- The platform must keep an audit trail of backup, restore, and upgrade actions.
- The platform must provide SOP-oriented upgrade flows for platform teams, including pre-check, schedule, execute, verify, rollback, and complete states.

## 7. Platform Operations

- The platform must support customer directory management.
- The platform must support environment management.
- The platform must support policy enforcement.
- The platform must support approval and exception handling for managed customers.

## 8. Observability and Audit

- Platform resource pages must expose secret-safe runtime inventory: CR conditions, related workloads and Jobs, PVC summaries, routes, warning events, and deletion/finalizer progress.

- The platform must surface action history.
- The platform must surface job and provisioning status.
- The platform must surface operational logs and traceability.
- The platform must maintain an auditable history of all lifecycle actions.

## 9. Operator Integration

- After Infra registers a Cluster, the platform must own normal lifecycle management for Platform-created Database Servers, Benches, and Sites.
- Platform-created runtime resources must carry stable ownership labels linking them to the Platform document and customer boundary.
- Platform deletion must verify exact Cluster, namespace, kind, resource name, ownership labels, dependency state, protected-resource denylist, user permission, confirmation, and audit.
- Site, Bench, and platform-managed Database Server deletion must be asynchronous, observable, retryable, and confirmed against runtime absence before documents are marked Deleted or Retired.
- `default/frappe-mariadb`, unlabelled resources, namespaces, Nodes, CRDs, operators, Traefik, wildcard TLS, RBAC, and infrastructure Secrets must remain protected.

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
- How customer-owned custom domains will be verified and automated in a later phase.

## 11. Product Topology And Launch

- Plans must select a versioned Landscape and default/allowed versioned Privacy Profiles.
- Landscapes compose ordered Dev, QA, Pre-Prod, and Prod Environments with versioned Site Control Profiles.
- Privacy rules must resolve Bench and Database sharing independently per Environment.
- A Subscription must freeze Customer, Plan, Region, Landscape version, Privacy version, policy JSON, and policy hash.
- A Site must belong to one Subscription and Environment; only one active Site is allowed for each pair.
- Policy changes must not silently alter active Subscriptions.
- Enabled Bench Test and LATP runs are promotion gates. Production LATP must be non-destructive.
- Exactly one active Free Plan is allowed per Release Group. It must use Single Tier, Prod, and Public.
- Each Free Plan and Region must have exactly one Ready shared Free Bench before customer creation is offered.
- Customers choose Plan, Region, and Site identity only. Runtime placement is Platform-owned.
- Non-Free Beta enrollment requires Platform approval before provisioning.
- Platform dashboard aggregates must use authoritative counts rather than capped list results.
- Platform navigation must come from permission-protected Frappe Workspace Sidebar configuration.
- Customer UX must hide Kubernetes and runtime implementation details.

Detailed rules: `docs/architecture/product-topology-model.md`.
