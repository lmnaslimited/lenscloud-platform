# LensCloud Platform Workitems

This is the canonical tracker for the current live-orchestration milestone.
Keep detailed design in domain documents and completed proof in dated evidence.

Status: `Complete`, `In Progress`, `Pending`, or `Blocked`.

| Work Item | Outcome | Status |
|---|---|---|
| EU cluster, operators, Traefik, wildcard TLS, restricted access | Infra runtime is ready for Platform reconciliation | Complete |
| Database Server model and privacy validation | Public, Private Shared, and Private placement rules exist | Complete |
| Structured MariaDB, Bench, and Site manifests | Secret-safe manifests map platform records to operator resources | Complete |
| Idempotent Kubernetes apply and status sync | Server-side apply, sync, and action logs exist | Complete |
| Wildcard Site workflow | Standard Sites require no DNS-provider or per-Site certificate action | Complete |
| Operator-compatible release image | `lens-pure:v16.14.1` passes live Site and asset acceptance | Complete |
| Create Release Group `lens-pure` and Release `v16.14.1` | Bench deployment resolves the approved image and digest from Release data | Complete |
| Inventory and retire obsolete Bench/Site records | Old platform and matched operator resources are removed safely | In Progress |
| Public live acceptance | Two unrelated customers share `default/frappe-mariadb`; both Sites pass HTTPS | Complete |
| Private Shared live acceptance | Same-customer Quality/Production sharing passes; cross-customer attachment fails | Blocked |
| Private live acceptance | One Bench/Site passes; every second Bench attachment fails | Blocked |
| Platform operator workflow | Operator creates Bench and Site and sees real progress, URL, and history | In Progress |
| Customer Free Plan workflow | Customer creates one real Site through the shared orchestration service | Complete |
| Authenticated Playwright and evidence | Platform/customer desktop and mobile tests pass; evidence is recorded | Complete |
| Safe cleanup and final status | Temporary resources are removed; shared MariaDB and infra remain healthy | Blocked |
| Infra runtime lifecycle RBAC contract | Host-side Infra evidence supplies lifecycle RBAC; Platform consumes it through Python Kubernetes API only | Complete |
| Runtime ownership metadata | MariaDB, FrappeBench, and FrappeSite manifests carry stable Platform/document/customer ownership labels | Complete |
| First-class runtime visibility | Platform pages show CR conditions, workloads, Jobs, PVCs, routes, warning events, and finalizer state without secrets | In Progress |
| Platform deletion orchestration | Site, Bench, and platform-managed Database Server deletion APIs enforce ownership, dependencies, protected-resource rules, audit, and retry | In Progress |
| Platform lifecycle UI | Platform operators can inspect, confirm, delete, monitor, and retry from resource pages | Complete |
| Lifecycle create/inspect/delete acceptance | Platform completes owned resource lifecycle without manager or Infra intervention | Blocked |
| Runtime namespace registry | Cluster-approved runtime namespaces are synced into Runtime Namespace records and selected on Database Server and Bench records | In Progress |

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
