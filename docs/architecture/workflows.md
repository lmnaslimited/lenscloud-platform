# LensCloud Platform Workflows

## Allowed Now

- site create
- site suspend, platform-facing by default
- site delete, platform-facing by default
- backup, platform-facing or qualified-customer only
- restore, platform-facing or qualified-customer only
- release create/promote/block, platform-facing only
- bench upgrade planning, platform-facing only
- upgrade, platform-facing or qualified-customer only
- wildcard hostname reservation and route reconciliation
- database server create/register/attach, platform-facing only

## Later

- multi-cluster migration
- advanced approval chains
- richer `SiteJob` UX unless the operator implementation matures first
- cross-region tenancy mobility

## Operational Rules

- Once Infra provisions and registers a Cluster, Platform owns routine lifecycle management of the tenant resources it creates.
- Runtime mutation and deletion require exact ownership metadata and protected-resource checks; name prefixes alone are insufficient.

- Keep lifecycle operations idempotent where possible.
- Treat operator resources as the source of truth.
- Do not reimplement Kubernetes reconciliation logic in the app.
- Do not treat Release Group as a deployable version; Bench must deploy a specific Release.
- Do not treat MariaDB as an implicit side effect of Site creation; Database Server is selected and managed explicitly.

## Release And Bench Upgrade Workflow

Release Group is the stable release family. Release is the deployable transaction. Bench tracks current and next release state.

Release Group actions:

- view Releases
- view Benches grouped by current Release
- view Benches behind latest eligible Release
- create Release
- promote Release
- schedule rollout
- compare Release adoption

Release actions:

- mark build ready
- promote to Quality
- promote to Production eligible
- block Release
- view affected Benches
- schedule Bench upgrades

Bench actions:

- create Bench from Release Group and Release
- schedule upgrade to next Release
- set next Release from a released Release in the same Release Group
- schedule Site upgrades manually after the Site upgrade-tested gate passes
- run pre-upgrade checklist
- start upgrade
- verify upgrade
- rollback to previous Release
- mark upgrade complete
- refresh available apps from the Release Group app catalog
- install an eligible app to an existing Site through a Platform/customer action

Bench upgrade SOP states:

- Draft
- Scheduled
- Precheck
- Ready
- Running
- Verifying
- Completed
- Rolled Back
- Failed

Frontend expectations:

- Release Group pages must summarize release adoption across Benches.
- Release pages must show build/promotion status and affected Benches.
- Bench pages must show current Release, next Release, schedule, and SOP progress.
- Site upgrade scheduling must be blocked until `upgrade_tested`, `tested_on`, and `tested_by` are filled.
- Bench update must be blocked until every Site on that Bench is in `upgrade_state = Scheduled` for the intended next Release.
- Platform and customer portal app install controls must only offer apps present in the Release Group catalog and eligible for the target Site.
- Missing backend/operator behavior must be marked as a gap until connected.

## Workspace Model

LensCloud uses a control-plane workspace model, not a literal CRM copy.

- Left navigation keeps the current scope and session context.
- The main workspace carries dashboards, lists, timelines, action flows, and other operational content.
- The right contextual inspector carries record summary, editable fields, lifecycle status, related objects, and history.
- The AI assistant is an optional drawer attached to the inspector, not a permanent competing pane.
- Read-only status surfaces must remain visually distinct from editable document fields.
- CRM shell patterns may be used as a reference for split-workspace behavior, but the LensCloud layout must remain control-plane oriented.


## Mobile Workspace Inspector

The right contextual inspector is part of the LensCloud workspace contract, so it must remain reachable below desktop widths. Desktop and wide tablet layouts keep the fixed right rail. Mobile and narrow tablet layouts expose the same inspector slot through a bottom-sheet drawer opened by a persistent `Details` action in the main workspace.

Rules:

- Inspector content must not be desktop-only. Any field, status, progress, related record, or action placed in the inspector must be reachable on mobile.
- The mobile drawer reuses the same inspector slot as desktop so pages do not fork customer/platform logic.
- The trigger uses Frappe UI `Button`, LensCloud blue for primary access, and the Stitch service-portal token contract for white surfaces, subtle borders, compact typography, and restrained color.
- Customer pages may use friendlier labels such as `Details`, `Progress`, or `Service details`, but the drawer must not expose platform-only terms or secrets.
- Platform pages may expose operational inspector content according to role and DocType permissions.
- Authenticated mobile Playwright must open the drawer and assert representative inspector-only content. Route-load checks alone are insufficient.

## Workspace Behavior by Surface

- Platform console pages should favor dense operational context and fast record access.
- Customer pages should favor guided lifecycle flows, clear status surfaces, and prominent site creation entry points.
- Platform-facing inspector views may expose more fields and actions than customer-facing views.
- Customer-facing inspector views should be curated and lighter weight.
- Missing backend behavior must be surfaced as a gap rather than assumed.


## Customer Plan-First Workflow

The customer portal must optimize for converting signed-in or lmnas.com-origin users into active LensCloud customers who can choose a Plan, create a Subscription, and receive a provisioned Site without seeing runtime internals.

Customer navigation:

- Dashboard: conversion-oriented overview with a primary `Browse Plans` CTA, usage summaries, lifecycle status, and next steps.
- Plans: customer-friendly Plan cards, Free Plan setup, and approval requests for non-Free Plans.
- Subscriptions: customer-friendly service cards, Landscape progress, renewal/payment summary, and Site access when ready.
- Sites: no standalone customer menu item; Sites are contextual outcomes of Subscription Landscapes.
- Create Site: legacy compatibility route only, omitted from customer navigation.
- Account: customer identity, organization, Central User Access, support/billing contact placeholders, and read-only service references. Account is the customer identity/access surface, not a service command center.

Customer action placement:

- `Browse Plans`/`Add New Subscription` must be the first-class launch CTA. Free Plan setup creates the Subscription and Site together.
- Customer create/support actions must appear in the main page body or site detail surface, not only in the inspector. Advanced operations must appear as locked/qualified features, not normal customer actions.
- Plan entitlement limits are enforced server-side and rendered in the Plan catalog as disabled customer CTAs when exhausted.
- The inspector may provide context, assistant help, technical metadata, and request history.
- Missing backend behavior must be shown as pending/unavailable/captured-as-request; locked advanced operations must be labeled as qualification/platform-managed features. Do not implement backend business logic in this pass.

Create Site state model references:

- Customer: signed-in account and customer identity.
- Subscription: durable customer service boundary. Free Plan self-approves; paid/beta Plans stay approval-gated until billing/workflow contracts are implemented.
- Site: requested tenant instance and eventual provisioned site.
- Region: preferred placement source, displayed customer-friendly even though Region is a platform tree doctype.
- Bench: platform placement target with current Release and next Release context, not directly editable by the customer in the first pass.
- Platform Settings: `root_domain` is mandatory for customer domain previews; customers enter subdomains only.


## Customer Site Access And SSO Workflow

Customer Site access is Subscription-led. A Site becomes customer-openable only after runtime Ready, setup wizard completion, OAuth/Social Login configuration, and an Active Site Access Grant for the signed-in Customer Member. The shared sequence is `docs/architecture/cua-site-bootstrap-sso-sequence.md`.

Customer flow:

1. Customer signs in to Platform.
2. Customer opens Subscriptions.
3. Platform shows each Landscape environment with Site status and access status.
4. If access is ready, customer clicks `Open Site`.
5. Target Site redirects to Platform OAuth when no Site session exists.
6. Platform authenticates and returns the customer to the Site without asking for a Site password.
7. If access is pending, Platform shows setup/OAuth/user-sync progress and recovery guidance.

Platform operator flow:

1. Inspect Site Bootstrap State and Site Access Grants from Platform.
2. Retry setup/OAuth/user sync through secret-safe runner actions.
3. Review action logs without credentials or pod logs.
4. Revoke or resync access when Customer Member status changes.

## Commercial And Integration Workflow

Commercial and relationship information is surfaced in LensCloud but sourced from external systems configured in `Platform Settings`.

- `billing_system` is the primary source for invoicing, finance status, plan, renewal, and payment-state summaries.
- `crm_system` is the primary source for account relationship, onboarding, and lifecycle/customer-stage summaries.
- `support_system` is the primary source for support tickets, escalation state, and support redirects.
- Customers see summaries and support redirects only; they do not get direct billing-system or CRM-system access from LensCloud.
- Platform agents see extended billing, CRM, and support context and may use Frappe SSO links to external systems when configured.
- Frappe SSO setup is handled outside this frontend implementation and must not be implemented here.

## Customer Domain Workflow

Customer-created sites use the platform root domain in this pass.

- Customers enter a preferred subdomain/name only.
- The final domain preview is `{preferred_subdomain}.{Platform Settings.root_domain}`.
- The Site `domain` field stores the root or approved domain, defaults from Platform Settings, and is read-only in this pass.
- If `root_domain` is missing, Create Site must clearly show a Platform Settings gap and prevent normal submission.
- Subdomain validation is frontend-only in this pass and must not imply backend reservation has happened.
- Customer custom-domain whitelisting is out of scope until approved-domain support is designed.

## Platform Runtime Lifecycle Workflow

The canonical contract is `docs/architecture/platform-runtime-lifecycle.md`.

Platform operators must be able to inspect and manage Platform-owned Database Servers, Benches, and Sites without manager access. Resource pages expose secret-safe CR conditions, related workloads, Jobs, PVCs, routes, warning events, finalizer state, and orchestration history.

Deletion sequence:

1. Validate role, Cluster, namespace, exact runtime identity, ownership labels, customer/privacy boundary, dependencies, and protected-resource denylist.
2. Record `Deletion Requested` and an Orchestration Action Log.
3. Quiesce or reject when dependent resources prevent safe deletion.
4. Delete the owner CR and observe operator finalizers.
5. Clean only explicitly owned dependents when required by the operator contract.
6. Mark the platform document Deleted or Retired only after exact runtime absence is confirmed.
7. Surface `Deletion Failed` with safe error details and retry.

Infra owns cluster provisioning and protected infrastructure. Platform owns routine tenant lifecycle after handoff. Customers see friendly Site lifecycle state only; they never receive raw runtime or credential details.

## Locked Advanced Operations

Backup, restore, upgrade, advanced DNS, suspend, and delete are not first-class customer features by default.

- Show these as locked features that require LensCloud qualification/certification or platform-team handling.
- Do not label locked features merely as backend gaps.
- Platform console may expose these actions as operator entry points while still marking missing backend/orchestration behavior as gaps.

## Region Tree Workflow

Region is a native Frappe tree doctype. Platform-facing Region views must support both tree and list modes.

- Tree mode uses `parent_region` as the parent field.
- Group nodes use `is_group`.
- Ordering should follow nested-set fields such as `lft`/`rgt` where available.
- List mode remains available for filtering, scanning, and standard record work.

## Document Lifecycle Workflow

Frappe document lifecycle actions are first-class UI actions in the platform console.

- Master data such as `App` and `Release Group` can be created through the platform resource workspace.
- `Release` is a submittable transaction and should move through Draft, Submitted, Cancelled, and Amended states using native Frappe document APIs.
- Document lifecycle actions must not be confused with infrastructure lifecycle actions. Submit/cancel a `Release` records the platform transaction; it does not deploy infrastructure.

## Frontend Execution Order

The canonical frontend work-item list and status tracker is the `Frontend Handover Tracker` table in `docs/handoffs/platform/agent-handoff.md`.

1. Work on the row marked `Next` before starting later pending rows.
2. Update that tracker table as work changes status.
3. Do not duplicate the frontend tracker in this file.
4. Every phase must end at its stop point and wait for explicit confirmation before scope expansion.

## Frontend Guardrails

- Keep the first pass scoped to the workspace shell, platform inspector, customer dashboard/sites/create-site/account pages, and action entry points.
- Use native Frappe authentication and permissions for access control.
- Keep the platform-console and customer-portal surfaces separate by role.
- Mark missing backend behavior as a gap instead of assuming it exists.
- Keep the platform/infrastructure boundary explicit at all times.

## Region-Driven Cluster Placement Workflow

LensCloud supports more than one active runtime cluster.

- Platform Settings stores global defaults only.
- Region determines the deployment Cluster.
- Bench creation selects Region and derives Cluster from `Region.cluster`.
- Site creation selects Region and derives Cluster from `Region.cluster`.
- Customers never see kubeconfig, SSH, or credential details.
- Platform agents may see Cluster summaries, manager host, Headlamp URL, credential reference names, and health state.

Current live EU dev target from `lenscloud-infra`:

- Cluster: `lenscloud-eu-dev`
- Region: `EU`
- Provider: `Hcloud`
- Manager: `lenscloud-eu-manager-1`
- Manager public IP: `116.203.22.81`
- Manager private IP: `10.20.1.1`
- current Headlamp URL: `https://headlamp.cloud.lmnaslens.com`
- Kubernetes access model: SSH to manager VM and run `kubectl` there
- Kubeconfig reference: manager VM `/etc/rancher/k3s/k3s.yaml`
- Operator namespace: `frappe-operator-system`
- Default storage class: `local-path`

## Bench And Site Orchestration Workflow

Backend orchestration methods are server-side only.

- `dry_run_bench_manifest(bench)` generates a `FrappeBench` manifest.
- `reconcile_bench(bench, dry_run=True)` records a safe dry-run unless real apply is explicitly wired later.
- `request_customer_site(...)` creates a LensCloud Site request under a Plan, defaults to Free plan when selected.
- `dry_run_site_manifest(site)` generates a `FrappeSite` manifest.
- `reconcile_site(site, dry_run=True)` records a safe dry-run unless real apply is explicitly wired later.
- The existing `queue_or_apply_dns_record(site)` path must be retired or bypassed for standard wildcard Sites.

Real Kubernetes apply remains gated behind backend credential/reference work and Platform Settings apply flags. The frontend must not call Kubernetes or any DNS provider.

## Database Server And Bench Attachment Workflow

Database Server is a platform-only runtime resource. Customers select Region and Plan; placement policy selects the Bench and Database Server.

Platform flow:

1. Create or register a Database Server.
2. Select Region; derive Cluster from `Region.cluster`.
3. Select privacy: Public, Private, or Private Shared.
4. For private modes, set the owner Customer/privacy boundary.
5. Generate and review the MariaDB CR dry-run.
6. Reconcile the MariaDB CR when Kubernetes apply is enabled.
7. Attach an eligible Bench.
8. Generate the `FrappeBench` manifest with `spec.dbConfig.mariadbRef`.
9. Sync MariaDB and Bench status into LensCloud.

Placement validation:

- Database Server and Bench must resolve to the same Region and Cluster for operator-managed MariaDB.
- Private permits one Bench.
- Private Shared permits multiple Benches only in the same owner/privacy boundary.
- Public permits multiple eligible Benches.
- A Site inherits the Database Server attached to its Bench.
- Customers never receive database host, CR, namespace, or secret-reference details.

The detailed contract is in `database-server-model.md`.

## Wildcard Domain And TLS Workflow

Standard Site onboarding uses shared infrastructure:

- root domain: `cloud.lmnaslens.com`
- wildcard DNS: `*.cloud.lmnaslens.com`
- wildcard TLS: `*.cloud.lmnaslens.com`
- DNS provider is not part of the platform contract
- wildcard certificate lifecycle is owned by `lenscloud-infra`
- Traefik is the preferred target ingress

Customer and platform Site creation derive the FQDN from `subdomain + root_domain`, validate uniqueness, and create only runtime/routing resources. They do not create DNS records, call a DNS provider, wait for propagation, or request certificates.

Site availability requires both runtime readiness and hostname route readiness. The detailed platform contract is in `wildcard-domain-model.md`.

### Site Hostname And Operator Manifest

Site creation treats the full hostname as the Site identity. Operators and customers should not type the Site title directly. The backend derives read-only `Site.domain` from Platform Settings `root_domain` in this pass, then derives `Site.title` and the document name from `subdomain + domain`.

The generated `FrappeSite` manifest must set `spec.siteName` to the complete hostname such as `customer.cloud.lmnaslens.com`. It must not use only the subdomain.

## Live Orchestration Implementation Status

Implemented in the LensCloud control plane:

- MariaDB, FrappeBench, and FrappeSite manifests are generated as structured data and recorded in Orchestration Action Log.
- Database Server enforces Region, Cluster, privacy boundary, ownership, readiness, and Bench-capacity policy.
- Bench manifests reference Database Server through `spec.dbConfig.mariadbRef`.
- Standard Site manifests use the full hostname, Traefik `websecure`, inherited wildcard TLS, and no per-Site DNS Record.
- Reconcile operations are idempotent server-side apply calls and remain gated by `Platform Settings.kubernetes_apply_enabled`.
- Cluster access uses a server-side `file:` kubeconfig reference only. Credential contents are never stored in a LensCloud document or returned to the frontend.

The restricted EU kubeconfig is mounted read-only at
`/run/secrets/lenscloud-eu.kubeconfig`. Host-side positive and negative RBAC
checks pass, and LensCloud's cluster permission preflight returns
`all_required_allowed: true` after setting the Cluster default runtime namespace
to `lenscloud-runtime-eu`.

The remaining work is controlled live apply, status synchronization,
two-Bench shared-MariaDB validation, the three privacy acceptance scenarios,
and end-to-end HTTPS Site creation.

## Launch Subscription Workflow

1. Native Frappe authentication creates or identifies the user.
2. Customer onboarding creates or links one Customer.
3. Public onboarding presents the active Free Plan and its customer-friendly isolation summary.
4. Customer chooses Region and Site/subdomain; Platform resolves the Subscription, Prod Environment, and the Region's unique Ready Free Bench.
5. Site creation records the immutable policy hash and enters the existing orchestration lifecycle.
6. Customer sees product-level progress and recovery guidance only.
7. A non-Free Beta selection creates Pending Approval and provisions nothing until a Platform operator approves it.

## Policy Promotion Workflow

1. Create a new Landscape, Privacy, or Site Control Profile version.
2. Assign it to a Plan for new Subscriptions.
3. Existing Subscriptions retain their policy snapshot.
4. An audited upgrade resolves a new snapshot.
5. Run required Bench Test and LATP evidence for the target Release and policy hash.
6. Reject promotion when evidence is missing or when a Prod LATP run is destructive.

## Launch Reset Workflow

Use `docs/operator-sop/launch-reset-and-acceptance.md`. Runtime is retired Site, Bench, then managed Database Server through Platform. Tenant records are removed only after runtime absence. Protected and unlabelled resources remain untouched.
