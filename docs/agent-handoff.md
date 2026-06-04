# LensCloud Platform Agent Handoff

## Purpose

This repository is the product layer for the `lenscloud` app. It is Frappe-first, customer-facing, and role-aware.

## Agent Roles

- Platform Product Agent: owns customer lifecycle, subscriptions, site requests, and platform workflows.
- UI/UX Agent: owns Frappe UI structure and customer/platform navigation.
- Operator Integration Agent: ensures work matches the actual Frappe Operator contract.
- SOP/Docs Agent: keeps the repo handoff-ready and prevents scope drift.

## Skills To Associate

- `lenscloud-platform-sop`
- `frappe-ui-product`
- `frappe-operator-integration`
- `route53-automation`

## MCPs To Use

- Kubernetes MCP for operator and cluster inspection
- Route53 automation layer for DNS lifecycle work
- GitHub tooling for repo handoff and PRs

## Operator Truth

- `FrappeBench`, `FrappeSite`, `SiteBackup`, and `SiteRestore` are the implemented operator workflows to rely on.
- `SiteJob` is scaffolded and should not be treated as a production feature unless the codebase is explicitly updated to prove otherwise.

## Release Strategy

This model supersedes any earlier wording that treated Release Group as the deployable version.

- Release Group is master data for the release family.
- Release Group holds registry URL, image repository, included apps, supported Frappe major version, and release policy.
- Included apps are selected from `App` master data through the `Release Group Apps` table multiselect. Do not change this back to long text.
- Release is the transactional deployable version.
- Release holds image tag, image digest, build status, build/pipeline reference, release status, changelog, compatibility notes, and promotion state.
- Bench links to one Release Group and deploys a current Release from that group.
- Bench also tracks next Release, upgrade window, upgrade policy, and upgrade/SOP status.
- Release Group pages should show number of Benches and their release levels.
- Bench pages should show current release level, next release level, and SOP actions for moving to the next Release.
- Future SOP/control work should use a Bench Upgrade Plan or Release Rollout Plan transactional doctype.

## Gap Backlog

Implementation agents must also read `docs/platform-gap-backlog.md` before starting new frontend, data-model, or operator-integration work.

The backlog captures:

- `/lenscloud/platform` and `/lenscloud/customer` default redirect gaps
- unauthenticated `frappe.auth.get_logged_user` console noise
- Socket.IO warning tolerance
- missing favicon
- operator-readiness fields for Bench, Site, and Platform Settings
- the corrected Release Group vs Release field placement
- the next infra/operator handoff requirements

## Platform-Wide Workitems

Use `platform-workitems.md` for cross-repo LensCloud work tracking. The frontend handover tracker below remains the canonical UI-specific tracker; the platform-wide tracker covers backend integration, infra handoff, local Docker runtime, DNS automation, HA/storage, and multi-cluster operations.

## Repo Boundary

- This repo owns the `lenscloud` app and product workflows only.
- Infra/bootstrap belongs in `lenscloud-infra`.


## Current Frontend Decisions Beyond Original Requirement

These decisions supersede the early generic doctype-first interpretation of the frontend:

- The frontend uses Frappe UI as the native component foundation, with CRM and Press used only as implementation references for structure, resource APIs, routing, and cloud-console patterns.
- The platform console remains an operator workspace with dense lists, dashboards, a contextual inspector, and an optional assistant drawer.
- The customer portal is site-first and conversion-oriented, not a doctype-management console.
- Customer actions must be primary page actions, especially `Create Site`; they must not be hidden only inside the inspector.
- Customer navigation is `Dashboard`, `Sites`, `Create Site`, and `Account`.
- The customer dashboard prioritizes converting signed-in/inbound users into active site creators.
- Customer site management should expose clear first-class actions for create, open/manage, and support/request status. Backup, restore, upgrade, advanced DNS, suspend, and delete are locked features for qualified/certified customers or platform-managed operations, not default customer actions.
- The inspector remains useful for customer context, assistant help, and technical metadata, but it is secondary to the primary site workflow.
- Region is a native Frappe tree doctype and must support both `Tree` and `List` display modes in the platform console, using `parent_region`, `is_group`, and nested-set ordering.
- Redundant shell/header chrome should stay removed: app name and scope live in the left pane; page headers should focus on the active page and actions.
- Platform Settings and Customer Account use tabbed inspector models for consistency. Platform Settings is also the source of truth for `root_domain`, `billing_system`, `crm_system`, and `support_system` UI integration state.

## Customer Portal Product Flow

The customer portal exists to help a signed-in customer create and manage sites quickly.

Primary customer outcomes:

1. Create a new site from a dedicated guided flow.
2. See existing sites and their lifecycle status at a glance.
3. Manage common site actions without understanding platform internals.
4. Understand when a workflow is pending because backend/orchestration support is not yet wired.

Customer `Create Site` first-pass flow:

1. Site Basics: customer enters a preferred subdomain/name only.
2. Domain Preview: the UI derives `{preferred_subdomain}.{Platform Settings.root_domain}`. Customers cannot enter arbitrary primary domains in this pass; the Site `domain` field stores the root/approved domain and remains read-only.
3. Plan/Product: selected product or plan placeholder, explicitly marked as a billing-system integration gap when not wired.
4. Region: customer-friendly region selection sourced from the Region tree/list data, without exposing nested-set internals.
5. Review: summary and clear submission state.
6. Pending Activation: when backend site creation is missing, show a pending request/status surface instead of inventing backend behavior.

## Commercial And External System Model

LensCloud customer surfaces show commercial and relationship context, but do not give customers direct access to the billing or CRM systems.

- Billing, CRM, and support configuration comes from `Platform Settings`.
- Customer dashboard should show billing summary, CRM/account relationship summary, and support summary when integrations are configured.
- When integration APIs are missing, the UI must show configured/missing integration state and placeholder data without inventing records.
- Customers may be redirected to the support system in worst-case support scenarios, but they do not receive direct billing-system or CRM-system access from LensCloud.
- Platform agents see richer billing, CRM, and support context in the platform console and may use Frappe SSO links to external systems when configured.
- Frappe SSO setup is external to this repo and should be treated as a configured dependency, not implemented here.

## Locked Customer Operations

The following customer-visible site operations are locked by default:

- Backup
- Restore
- Upgrade
- Advanced DNS
- Suspend
- Delete

They may be enabled only for qualified/certified LensCloud customers or performed by the platform team. The UI must label them as `Requires LensCloud qualification` or `Managed by platform team`, not as ordinary disabled backend gaps.

## Handover Objects

These handover objects define the ordered frontend work for LensCloud Platform. Agents must complete them in sequence and stop at every phase boundary until the phase owner confirms the next step.
The LensCloud shell is a control-plane workspace, not a literal CRM clone:
- left navigation keeps scope and session context
- the main workspace carries operational lists, timelines, actions, and dashboards
- the right contextual inspector carries record summary, editable fields, status, related objects, and history
- the AI assistant is an optional drawer attached to the inspector, not a permanent competing pane
- read-only status surfaces must stay visually separate from editable document fields

### Frontend Handover Tracker

This table is the single source of truth for frontend handover status. Do not add duplicate frontend work-item lists elsewhere; update this table as work moves.

Status values:

- `Complete`: implemented and validated for the current P0 scope.
- `Next`: next logical work item.
- `Pending`: not started.
- `Blocked`: cannot proceed without new backend, SSO, infra, or user input.

| Phase | Work Item | Owner / Agent | Dependencies | Expected Outcome | Priority | Status | Stop Point |
|---|---|---|---|---|---|---|---|
| Handover Object 1 | Define shared workspace shell structure using Frappe UI patterns adapted for platform-engineer workflows | UI/UX Agent + Platform Product Agent | `README.md`, `requirements.md`, `docs/state-model.md`, `docs/workflows.md`, CRM frontend reference, Press dashboard reference | Confirmed control-plane workspace contract with left navigation, main workspace, inspector, and assistant drawer reservation | P0 | Complete | Workspace contract confirmed before scaffold work |
| Handover Object 1 | Define platform-console vs customer-portal navigation model | UI/UX Agent + Platform Product Agent | Native Frappe auth and permissions, role model | Platform navigation and customer site-first navigation are separated by role | P0 | Complete | Role split confirmed |
| Handover Object 1 | Define main workspace, right contextual inspector, and optional AI assistant drawer contract | UI/UX Agent + Platform Product Agent | CRM split-workspace reference, LensCloud control-plane requirements | Workspace model separates main actions, inspector details, and assistant context | P0 | Complete | Inspector/assistant placement confirmed |
| Handover Object 1 | Specify separation between read-only status, editable fields, and action entry points | Platform Product Agent + UI/UX Agent | `docs/state-model.md`, `docs/workflows.md` | Fields, lifecycle status, external context, and UI action entry points are visibly separated | P0 | Complete | Separation model confirmed |
| Handover Object 1 | Align route map with native Frappe auth and permissions | UI/UX Agent | Native Frappe login/session/roles | Authenticated platform and customer routes use Frappe session state | P0 | Complete | Route map confirmed |
| Handover Object 2 | Create shared workspace shell around existing routes without breaking page URLs | UI/UX Agent | Handover Object 1, existing frontend routes | Frappe UI shell with platform/customer scope navigation and stable route rendering | P0 | Complete | Shell reviewed and route smoke-tested |
| Handover Object 2 | Add reusable page header, action bar, and context strip for main workspace | UI/UX Agent | Shared workspace shell | Compact page framing without redundant chrome | P0 | Complete | Header/action framing reviewed |
| Handover Object 2 | Add right contextual inspector for summary, editable fields, lifecycle status, related objects, and history | UI/UX Agent + Platform Product Agent | `docs/state-model.md`, existing doctypes | Inspector tabs include Summary, Fields, Status, Actions, Related, and platform-only External where relevant | P0 | Complete | Inspector contract validated |
| Handover Object 2 | Keep first pass read-heavy and action-light | Platform Product Agent | Backend gaps, infra boundary | UI shows gaps/locked states instead of inventing backend business logic | P0 | Complete | Gap handling confirmed |
| Handover Object 3 | Add platform-facing inspector views for Customer, Release Group, Bench, Site, Region, and Platform Settings | UI/UX Agent + Platform Product Agent | Existing doctypes, Frappe document APIs | Platform records render list/detail/inspector surfaces; Region supports tree/list; Platform Settings has tabs | P0 | Complete | Platform resource set validated |
| Handover Object 3 | Add customer-facing product pages for dashboard, sites, dedicated create-site flow, and account | UI/UX Agent + Platform Product Agent | Native Frappe auth, Customer/Site doctypes, Platform Settings | Customer portal is site-first with Dashboard, Sites, Create Site, and Account | P0 | Complete | Customer route set validated |
| Handover Object 3 | Keep customer create/support actions in primary page surfaces and keep advanced operations locked unless customer qualification is proven | Platform Product Agent + UI/UX Agent | `docs/workflows.md`, commercial/qualification rules | Create Site and Contact Support are first-class; backup/restore/upgrade/advanced DNS/suspend/delete are locked | P0 | Complete | Customer action model validated |
| Handover Object 3 | Group platform inspector fields into summary, editable fields, lifecycle status, related objects, external systems, and history | UI/UX Agent + Platform Product Agent | `docs/state-model.md`, Platform Settings integrations | Inspector exposes fields, Status tab, Related tab, External tab for Customers/Sites | P0 | Complete | Inspector grouping validated |
| Handover Object 3 | Add lifecycle action entry points for site create and support/customer requests; keep advanced actions platform-facing or locked | Platform Product Agent | Backend lifecycle APIs may be missing; `lenscloud-infra` read-only contract | UI-only action entry points show backend gaps; customer advanced actions show qualification locks | P0 | Complete | Action visibility validated |
| Handover Object 3 | Mark missing backend behavior as a gap instead of assuming it exists | Platform Product Agent + Operator Integration Agent | Backend API availability, operator contract | Missing billing/CRM/support/lifecycle/provisioning data is surfaced as gaps/placeholders | P0 | Complete | Gap labels validated |
| Handover Object 4 | Reserve assistant drawer inside or alongside the inspector | UI/UX Agent | Workspace shell and inspector | Assistant drawer exists as a secondary contextual area in the inspector shell | P0 | Complete | Assistant reservation validated |
| Handover Object 4 | Make assistant context-aware using scope, doctype, record, and action state | UI/UX Agent + Platform Product Agent | Assistant implementation/API not wired yet; current route/record/action context available | Assistant receives meaningful context from current workspace and selected record/action | P1 | Complete | Assistant context contract validated across platform and customer routes |
| Handover Object 4 | Wire permissions, empty states, loading states, and error states | UI/UX Agent + Platform Product Agent | Native Frappe permissions, frontend route guards | Role-aware UX with stable loading/empty/error states across platform and customer routes | P0 | Complete | Full route smoke test passed |
| Handover Object 4 | Add audit/history placeholders and recent-action surfaces | Platform Product Agent + UI/UX Agent | `docs/state-model.md`; backend event/audit source missing | Status tab and dashboard surfaces show audit/recent activity placeholders without inventing data | P0 | Complete | Audit/status placeholder validation passed |
| Handover Object 4 | Validate every action shown maps to a real backend or is explicitly marked unavailable/locked/gap | Platform Product Agent + Operator Integration Agent | Backend support, `lenscloud-infra` read-only reference | UI clearly distinguishes supported, UI-only, backend gap, SSO pending, and qualification-locked actions | P0 | Complete | Full P0 smoke suite passed |
| Handover Object 4 | Ensure frontend stays inside platform/infrastructure boundary | Operator Integration Agent + Platform Product Agent | `lenscloud-infra` read-only reference | Frontend does not mutate infra or implement reconciliation logic | P0 | Complete | Boundary validation passed |
| Handover Object 5 | Fix platform/customer route defaults and runtime polish gaps | UI/UX Agent | `docs/platform-gap-backlog.md`, current Vue router/session code | `/platform` and `/customer` default to dashboards; guest auth/socket/favicon noise is handled cleanly | P0 | Complete | Route/runtime smoke test passed |
| Handover Object 5 | Correct release model by introducing Release as the deployable transactional doctype | Data/Model Agent + Platform Product Agent | `requirements.md`, `docs/state-model.md`, existing Release Group and Bench doctypes | Release Group remains master data; Release holds image tag/build status; Bench links current/next Release | P0 | Complete | Data model migrated and field metadata verified |
| Handover Object 5 | Update platform Release Group, Release, and Bench views for release-level tracking | UI/UX Agent + Platform Product Agent | Release doctype, Bench current/next release fields | Release Group shows Releases and bench adoption; Bench shows current/next Release and upgrade SOP context | P0 | Complete | Release-level routes and views smoke-tested |
| Handover Object 5 | Add operator-readiness fields to Bench, Site, and Platform Settings | Data/Model Agent + Operator Integration Agent | `docs/platform-gap-backlog.md`, Frappe Operator contract, `lenscloud-infra` handoff model | Records can map to namespace, operator resource names, storage class, status, DNS, and cluster/operator defaults | P0 | Complete | Operator-readiness fields migrated and surfaced in UI |
| Handover Object 5 | Define platform-team upgrade SOP surface for Bench movement to next Release | Automation/Workflow Agent + SOP/Docs Agent | Bench current/next Release fields; future Bench Upgrade Plan transactional model | Bench exposes upgrade window, upgrade policy, and upgrade/SOP status; transactional execution remains future backend work | P1 | Complete | First SOP status surface validated; backend job wiring remains pending |
| Handover Object 6 | Bring `lenscloud-infra` dev cluster to live handoff state | Infra Bootstrap Agent + Operator Integration Agent | `lenscloud-infra`, Hcloud, kubectl, Frappe Operator, MariaDB Operator | Live cluster exists with operators installed and handoff values ready for Platform Settings/Region | P0 | Pending | Cluster handoff artifact reviewed before platform backend wiring |
| Handover Object 6 | Wire Bench creation to operator-backed `FrappeBench` creation | Platform Product Agent + Operator Integration Agent | live infra handoff, Bench operator-readiness fields, current Release image data | Platform Bench action creates or reconciles a `FrappeBench` resource | P0 | Pending | One bench smoke test passes before Site wiring |
| Handover Object 6 | Track local Docker runtime requirement with infra | Infra Bootstrap Agent + SOP/Docs Agent | `lenscloud-infra/docs/local-docker-runtime.md`, Docker Desktop, k3d/K3s, Headlamp | Standalone local runtime workstream exists for Docker-only developer setups without host CLI installs | P0 | Next | Local runtime design reviewed before implementation |

### Completed P0 Validation

P0 was validated with an authenticated Playwright smoke test covering:

- `/platform/dashboard`
- `/platform/customers`
- `/platform/release-groups`
- `/platform/benches`
- `/platform/sites`
- `/platform/regions`
- `/platform/settings`
- `/customer/dashboard`
- `/customer/sites`
- `/customer/create-site`
- `/customer/account`

Validated outcomes:

- platform Status tab shows lifecycle/audit vocabulary
- platform External tab shows Billing/CRM/Support context for Customers and Sites
- Region supports tree/list mode
- customer advanced operations are locked by qualification/platform handling
- Create Site blocks normal submission when `Platform Settings.root_domain` is missing
- no browser console errors in the P0 smoke suite
- viewport remains contained at `900 / 900`
- assistant drawer receives contextual guidance for platform resources, customer site creation, customer sites, account, dashboard, and platform settings
- `/platform` redirects to `/platform/dashboard`; `/customer` redirects to `/customer/dashboard`
- `Release` route and doctype surfaces are available at `/platform/releases`
- Release Group, Release, Bench, Site, and Platform Settings field metadata migrated and verified
- favicon asset returns `200` from `/assets/lenscloud/frontend/favicon.ico`

### Next Work Item

Handover Object 5 is complete for route/runtime polish, Release data model correction, release-level platform UI, operator-readiness fields, and first Bench upgrade/SOP status surfaces. The next tracked work is Handover Object 6: keep the live `lenscloud-infra` cluster handoff current, define the local Docker runtime workstream, then wire operator-backed `FrappeBench` creation from LensCloud Platform.


## Multi-Cluster Placement Update

This supersedes any wording that implies Platform Settings selects one active deploy cluster. LensCloud supports multiple active clusters. Region determines runtime placement.

- `Cluster` is the registered runtime target.
- `Region.cluster` selects the cluster for deployment.
- `Bench.region` derives `Bench.cluster`.
- `Site.region` derives `Site.cluster`.
- Platform Settings keeps global defaults only: root domain, default plan, default storage class fallback, operator namespace fallback, Route53 defaults, and integration toggles.
- The live EU dev target is `lenscloud-eu-dev`, sourced from `lenscloud-infra` handoff docs.
- Kubernetes and Route53 apply are backend-only and remain gated; frontend never receives kubeconfig or provider credentials.

## Document Lifecycle UI

Platform resource pages now include a standard document lifecycle surface for master and transactional documents.

- `App`, `Release Group`, and `Release` expose `New` document creation from the platform workspace.
- Editable documents use standard Frappe document save APIs from the inspector field surface.
- `Release` is submittable and exposes Submit, Cancel, and Amend controls in the `Document` inspector tab.
- These document lifecycle controls are separate from operator/business lifecycle actions such as promote, rollout, backup, restore, upgrade, DNS, and Bench/Site provisioning. Operator-backed actions remain explicit backend gaps until wired.

## Agent Execution Order

1. Use the `Frontend Handover Tracker` table as the canonical work-item list and status source.
2. Complete the row marked `Next` before moving to later pending work.
3. Do not create duplicate frontend plan tables in other docs; update the tracker row status instead.
4. Every phase boundary still ends at its stop point and requires confirmation before scope expansion.

## Agent Instructions

### UI/UX Agent

- Use Frappe UI patterns as the frontend foundation.
- Use CRM frontend shell patterns as a reference for split-workspace behavior, not as a literal product template.
- Follow Press dashboard conventions for cloud-platform surfaces, status views, and action-oriented pages.
- Keep the platform-console and customer-portal experiences clearly separated by role; customer pages are product flows, not doctype management pages.
- Build the right contextual inspector to hold summaries, editable fields, status, related objects, and history for platform pages; keep it secondary on customer pages.
- Keep the assistant drawer optional and secondary to the inspector.
- Do not build around Desk-only customization unless a specific screen requires it.
- Keep the interface Frappe-native, compact, and workflow-oriented.
- Do not expose platform-only actions to customer roles.
- Stop at every phase boundary and wait for confirmation.

### Platform Product Agent

- Keep LensCloud as the control plane and do not drift into infrastructure implementation.
- Keep the platform/infrastructure boundary explicit at all times.
- Use native Frappe authentication and role-based permissions.
- Make sure lifecycle actions, status views, and audit surfaces match the documented state model.
- Ensure read-only status and editable fields stay visually distinct in the inspector.
- Any missing backend behavior must be marked as a gap, not assumed.
- Confirm whether each action is customer-facing, platform-facing, locked-qualified, or shared before the UI is built.
- Stop at every phase boundary and wait for confirmation.

### Operator Integration Agent

- Treat `lenscloud-infra` as read-only reference context.
- Use it only to understand the operator and lifecycle contract.
- Do not modify `lenscloud-infra`.
- Do not invent lifecycle behavior that the contract does not support.
- Keep the action UI aligned with the implemented operator workflows.
- Flag any dependency on missing operator behavior early.

### SOP / Docs Agent

- Keep the docs handoff-ready and ordered.
- Preserve the phase order and stop points.
- Keep the workspace contract explicit: main workspace, contextual inspector, optional assistant drawer.
- Record assumptions, gaps, and unresolved backend dependencies.
- Make sure work items stay short, testable, and explicitly owned.
- Do not let the handoff drift into vague “build the frontend” language.

## Phase Completion Rule

A phase is complete only when:

- its work items are finished,
- its dependencies are understood,
- any backend gaps are documented,
- and the owner confirms the stop point has been reached.

No later phase may begin until that confirmation is recorded.

### Site Identity Handoff Update

Site title is read-only derived identity. Do not ask users or operators to enter it. In this pass, default read-only `Site.domain` from `Platform Settings.root_domain`, then derive the full hostname as `subdomain + domain` and persist that value as `Site.title` and the Site document name. `FrappeSite.spec.siteName` and DNS Record `domain` must also use the full hostname. Keep `operator_resource_name` Kubernetes-safe and separate from the user-facing hostname. Future approved-domain support can replace the default root domain; customer custom-domain whitelisting is out of scope.
