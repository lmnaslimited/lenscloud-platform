# LensCloud Platform Workitems

This is the canonical tracker for the current live-orchestration milestone.
Keep detailed design in domain documents and completed proof in dated evidence.

Status: `Complete`, `In Progress`, `Pending`, or `Blocked`.

## Backlog Control

All Platform product, UI, and operator-workflow scope starts in this file first. Supporting design docs, SOPs, and evidence may be linked from a row here, but they are not independent backlog trackers.

| Work Item | Outcome | Status | Date Created | Date Completed |
|---|---|---|---|---|
| EU cluster, operators, Traefik, wildcard TLS, restricted access | Infra runtime is ready for Platform reconciliation | Complete | 2026-06-25 | 2026-06-25 |
| Database Server model and privacy validation | Public, Private Shared, and Private placement rules exist | Complete | 2026-06-25 | 2026-06-25 |
| Structured MariaDB, Bench, and Site manifests | Secret-safe manifests map platform records to operator resources | Complete | 2026-06-25 | 2026-06-25 |
| Idempotent Kubernetes apply and status sync | Server-side apply, sync, and action logs exist | Complete | 2026-06-25 | 2026-06-25 |
| Wildcard Site workflow | Standard Sites require no DNS-provider or per-Site certificate action | Complete | 2026-06-25 | 2026-06-25 |
| Operator-compatible release image | `lens-pure:v16.14.1` passes live Site and asset acceptance | Complete | 2026-06-25 | 2026-06-25 |
| Create Release Group `lens-pure` and Release `v16.14.1` | Bench deployment resolves the approved image and digest from Release data | Complete | 2026-06-25 | 2026-06-25 |
| Inventory and retire obsolete Bench/Site records | Old platform and matched operator resources are removed safely | In Progress | 2026-06-25 |  |
| Public live acceptance | Two unrelated customers share `default/frappe-mariadb`; both Sites pass HTTPS | Complete | 2026-06-25 | 2026-06-25 |
| Private Shared live acceptance | Same-customer Quality/Production sharing passes; cross-customer attachment fails | Blocked | 2026-06-25 |  |
| Private live acceptance | One Bench/Site passes; every second Bench attachment fails | Blocked | 2026-06-25 |  |
| Platform Customer and Site visibility | LensCloud Platform User can list/create/update Customer and Site records while raw delete remains denied | Complete | 2026-06-25 | 2026-06-25 |
| Platform operator workflow | Operator creates Bench and Site and sees real progress, URL, and history | In Progress | 2026-06-25 |  |
| Customer Free Plan workflow | Customer creates one real Site through the shared orchestration service | Complete | 2026-06-25 | 2026-06-25 |
| Authenticated Playwright and evidence | Platform/customer desktop and mobile tests pass; evidence is recorded | Complete | 2026-06-25 | 2026-06-25 |
| Safe cleanup and final status | Temporary resources are removed; shared MariaDB and infra remain healthy | Blocked | 2026-06-25 |  |
| Infra runtime lifecycle RBAC contract | Host-side Infra evidence supplies lifecycle RBAC; Platform consumes it through Python Kubernetes API only | Complete | 2026-06-25 | 2026-06-25 |
| Runtime ownership metadata | MariaDB, FrappeBench, and FrappeSite manifests carry stable Platform/document/customer ownership labels | Complete | 2026-06-25 | 2026-06-25 |
| First-class runtime visibility | Platform pages show CR conditions, workloads, Jobs, PVCs, routes, warning events, and finalizer state without secrets | In Progress | 2026-06-25 |  |
| Platform deletion orchestration | Site, Bench, and platform-managed Database Server deletion APIs enforce ownership, dependencies, protected-resource rules, audit, and retry | In Progress | 2026-06-25 |  |
| Platform lifecycle UI | Platform operators can inspect, confirm, delete, monitor, and retry from resource pages | Complete | 2026-06-25 | 2026-06-25 |
| Lifecycle create/inspect/delete acceptance | Platform completes owned resource lifecycle without manager or Infra intervention | Blocked | 2026-06-25 |  |
| Runtime namespace registry | Infra-approved namespaces are synced with customer/purpose metadata and filtered for Database Server and Bench placement | In Progress | 2026-06-25 |  |
| Platform list and inspector UX | Operators can filter by fields, see the selected record clearly, use status/cell click filters, sort columns, filter by related documents, and edit from a simplified inspector rail | In Progress | 2026-06-25 |  |
| Launch tenant and runtime reset | Test tenants and exactly owned runtime resources are retired while Cluster handoff data and protected infrastructure remain intact | In Progress | 2026-06-25 |  |
| Metadata-driven permissions and connections | Create/edit rights and related-document summaries come from DocType permissions/links; counts open filtered lists | Complete | 2026-06-25 | 2026-06-25 |
| Metadata-driven document editor | Center editing follows DocType tabs, sections, columns, Table, and Table MultiSelect metadata with compact Frappe-style controls | Complete | 2026-06-25 | 2026-06-25 |
| Center document and child-table editor | Selected documents edit below the list or expanded in the center; child grids use fixed columns and horizontal scrolling | Complete | 2026-06-25 | 2026-06-25 |
| Platform topology child-table editing | Operators can configure Plan privacy choices, Landscape environments, Privacy rules, and Site settings with typed value help and safe row operations | Complete | 2026-06-25 | 2026-06-25 |
| Configurable environment and landscape model | Dev, QA, Pre-Prod, and Prod compose versioned Single through Four Tier landscapes with safe Site controls | In Progress | 2026-06-25 |  |
| Configurable privacy profiles | Plans resolve independent Bench and Database sharing policies through submitted Privacy Profile records linked to first-class Privacy master data | Complete | 2026-06-25 | 2026-06-25 |
| Submitted policy/profile documents | Site Control Profile and Privacy are submittable policy versions with environment/family anchors, active/default selection, submitted-only consumption, and snapshot-safe subscription resolution | Complete | 2026-06-25 | 2026-06-25 |
| Bench Command Job/API for Site Controls | Platform consumes INF-010/INF-011 via Python Kubernetes API, validates policy/target/args, runs live `bench_test.status`, uses the pinned runner for supported Site Controls, records action logs, cleans Job/ConfigMap, and reports runner-pending commands as Unsupported | Complete | 2026-06-25 | 2026-06-28 |
| Production Bench Command runner/API handoff | Infra built and verified the pinned production runner; Platform integrates runner-backed maintenance mode, developer mode, approved site_config, and CORS while backup, restore, Bench Test trigger, and LATP remain Unsupported | Complete | 2026-06-27 | 2026-06-28 |
| Live real Bench Command runner acceptance | Free Plan public Prod Bench/Site, HTTPS/static assets, `bench_test.status`, and runner-backed `maintenance_mode.status` passed with Infra `328846b`; cleanup verified no command Job/ConfigMap remains; operator retest SOP: `docs/operator-sop/bench-command-real-site-runner-verification.md` | Complete | 2026-06-29 | 2026-06-29 |
| Bench Command backup status | Infra `ac86bdc` metadata-only `backup.status` runner contract is consumed; Platform runs it through the Python Kubernetes API, renders `Backups: 0 available`, records action logs, and cleans command Job/ConfigMap | Complete | 2026-06-30 | 2026-06-30 |
| Remaining Bench Command runner families handoff | Backup create, restore, Bench Test trigger, and LATP runner contracts are intentionally deferred until after Free-first customer E2E; Platform keeps these commands Unsupported while `backup.status` remains supported | Pending | 2026-06-29 |  |
| Customer Free Plan E2E launch flow | Customer signs in from the launch path, browses Plans, subscribes to Free, and Platform automatically provisions the Prod Site through the existing orchestration service | In Progress | 2026-06-30 |  |
| Central User Access model | LensCloud Platform is documented as the Central User Access system for customer users, invites, site access, SSO handoff, deactivation, and audit in a later implementation pass | Pending | 2026-06-30 |  |
| Customer dashboard and plan browsing UX | Customer portal is a guided launch home with Plan cards, friendly usage summaries, provisioning progress, and no runtime internals; implementation follows non-legacy Stitch artifacts under `docs/design/stitch_lenscloud_designs` | Complete | 2026-06-30 | 2026-06-30 |
| Stitch customer portal UI rehaul | Free-first customer portal implements non-legacy Stitch flow: dashboard, Plan selection, Free checkout, provisioning states, ready/open Site, Sites, Account, desktop/mobile validation | Complete | 2026-06-30 | 2026-06-30 |
| Customer guided activity correction | Replaced stacked Plan/setup/checkout sections with a true one-screen-at-a-time guided activity from Plan choice through Free checkout, provisioning, and Open Site | Complete | 2026-06-30 | 2026-06-30 |
| Customer dashboard journey entry state | Dashboard default route shows a Stitch-token welcome/start screen when no Subscription exists, and a subscribed service dashboard when Subscription exists; primary CTA uses supplied blue theme and aligned icons | Complete | 2026-06-30 | 2026-06-30 |
| Customer dashboard visual parity evidence | Captured Playwright dashboard screenshots at Stitch reference viewports, compared current no-subscription welcome state against non-legacy welcome reference, and recorded screenshot/report artifacts | Complete | 2026-06-30 | 2026-06-30 |
| Customer dashboard token polish | Dashboard welcome state applies Stitch token contract more directly: stronger white canvas, supplied blue primary CTA, aligned icon/text, compact onboarding checklist, and reduced legacy/pale surfaces | Complete | 2026-06-30 | 2026-06-30 |
| Customer self-service Plan catalog | Plan selection uses first-class submitted Platform Plans with portal flags, feature JSON, default centering, request-access/experimental controls, and desktop/mobile Stitch evidence for `choose_your_plan` and `choose_plan_mobile` | Complete | 2026-06-30 | 2026-06-30 |
| Customer Plan selection UI refinement | Removed redundant legacy Plan page elements, made card click/select expose the Plan CTA on-card, compacted Sites/Environment details, added customer-facing placement filter, highlighted default card like Stitch, and ordered default Plan first on mobile | Complete | 2026-06-30 | 2026-06-30 |
| Customer Plan page chrome cleanup | Removed redundant Free-first guided launch header/title/subtitle and top-right Refresh/Dashboard actions from customer Plans; right pane now carries launch progress steps, current selection, and the setup/checkout step titles match the guided activity | Complete | 2026-07-01 | 2026-07-01 |
| Customer setup and review Stitch mapping | Mapped `/customer/plans` setup directly from `setup_your_site/code.html` and review directly from `review_subscription/code.html`; completed progress steps show green checkmarks; Region uses active Cluster-backed Regions and domain suffix uses Platform Settings root domain; documented Frappe UI reuse and native/custom deviations with visual evidence | Complete | 2026-07-01 | 2026-07-01 |
| Customer subscription summary screen | Added customer sidebar Subscriptions entry and card-led, customer-safe subscription screen using real portal context; avoids platform list/detail UX and hides runtime internals | Complete | 2026-07-01 | 2026-07-01 |
| Customer subscription lifecycle detail | Removed customer Sites from the sidebar; Subscription detail now shows start/end dates, billing frequency, next renewal, plan-specific payment copy, and Landscape environment progression with Site status/version instead of a flat linked-Sites list | Complete | 2026-07-01 | 2026-07-01 |
| Mobile inspector access | Workspace inspector content is reachable on mobile/tablet through a shared bottom-sheet drawer with authenticated Playwright assertions; desktop right rail behavior remains unchanged | Complete | 2026-07-01 | 2026-07-01 |
| Customer subscription-led navigation cleanup | Removed customer Create Site menu, routed dashboard progress and Subscription count to Subscriptions, renamed Browse Plans to Add New Subscription, and disabled customer Plan CTAs when Plan entitlement limits are exhausted | Complete | 2026-07-01 | 2026-07-01 |
| Bench Command result display contract | Infra `405e0c1` display schema is consumed; Platform returns and renders safe `display`/`display_text`, action logs include readable results, and live `maintenance_mode.status` showed `Maintenance mode: Off` | Complete | 2026-06-29 | 2026-06-29 |
| Subscription and beta enrollment | Customer, Plan, Region, Landscape, policy snapshot, approval, and environment Sites are tracked as one service lifecycle | In Progress | 2026-06-25 |  |
| Subscription workflow approval | Subscription remains a regular DocType initially, then uses native Frappe Workflow for Free self-approval, paid/beta approval levels, rejection, cancellation, and audited state transitions | Pending | 2026-06-25 |  |
| Free Plan launch topology | Each Release Group has at most one active Free Plan and each Region has one eligible shared Free Bench | In Progress | 2026-06-25 |  |
| Truthful launch dashboard | Platform launch readiness, accurate aggregates, action-required queues, capacity, and recent actions replace capped-list counts | In Progress | 2026-06-25 |  |
| Configurable grouped navigation | LensCloud consumes permission-filtered Frappe Workspace Sidebar groups with compact desktop and mobile behavior | In Progress | 2026-06-25 |  |
| Customer launch experience | Signup leads to guided Free Site onboarding, visible provisioning progress, friendly Sites, Account, and beta enrollment | In Progress | 2026-06-25 |  |
| Customer portal design track | Stitch brief and Frappe UI implementation contract cover responsive launch, failure, retry, and approval states | In Progress | 2026-06-25 |  |
| Agent context and skill hygiene | `.agents` inventory is documented, Frappe UI skill is explicitly required only for UI work, stale MCP/skill claims are absent, and governance is linked from `AGENTS.md` | Complete | 2026-06-29 | 2026-06-29 |
| Platform documentation structure | Docs are organized by purpose with root backlog, architecture, handoffs, evidence, SOPs, design, agents, decisions, archive, and compatibility stubs for legacy high-traffic paths | Complete | 2026-06-29 | 2026-06-29 |

## Execution Order

1. Infra publishes the namespace-scoped lifecycle RBAC and protected-resource contract with host-side evidence.
2. Platform adds ownership metadata to generated runtime manifests.
3. Platform adds secret-safe runtime inventory and related-resource APIs.
4. Platform implements asynchronous Site, Bench, and Database Server deletion with dependency checks, audit, and retry.
5. Platform exposes inspect/delete/progress/retry actions in the platform workspace.
6. Run migrations, backend tests, frontend build, authenticated Playwright, and positive/negative Python Kubernetes API permission preflight.
7. Complete create, inspect, and delete acceptance without manager intervention.
8. Resume sequential Private Shared and Private live acceptance and cleanup through Platform.
9. Disable apply and update evidence, tracker, and handoff.

## Deferred

- database HA and backups
- NetworkPolicy and secret rotation
- US cluster and multi-region edge routing
- local Docker runtime
- custom customer-owned domains
- billing integration and advanced approval workflows
