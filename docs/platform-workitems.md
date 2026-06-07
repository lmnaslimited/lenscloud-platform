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
| Create Release Group `lens-pure` and Release `v16.14.1` | Bench deployment resolves the approved image and digest from Release data | Pending |
| Inventory and retire obsolete Bench/Site records | Old platform and matched operator resources are removed safely | Pending |
| Public live acceptance | Two unrelated customers share `default/frappe-mariadb`; both Sites pass HTTPS | Pending |
| Private Shared live acceptance | Same-customer Quality/Production sharing passes; cross-customer attachment fails | Pending |
| Private live acceptance | One Bench/Site passes; every second Bench attachment fails | Pending |
| Platform operator workflow | Operator creates Bench and Site and sees real progress, URL, and history | Pending |
| Customer Free Plan workflow | Customer creates one real Site through the shared orchestration service | Pending |
| Authenticated Playwright and evidence | Platform/customer desktop and mobile tests pass; evidence is recorded | Pending |
| Safe cleanup and final status | Temporary resources are removed; shared MariaDB and infra remain healthy | Pending |

## Execution Order

1. Run migrations and focused tests; build the frontend.
2. Verify restricted access and cluster capacity.
3. Create `lens-pure` Release Group and `v16.14.1` Release.
4. Inventory and safely retire obsolete Bench/Site records.
5. Run Public acceptance.
6. Run Private Shared acceptance and cleanup its temporary resources.
7. Run Private acceptance and cleanup its temporary resources.
8. Run authenticated platform and customer Playwright.
9. Update this tracker and create a new dated evidence document.

## Deferred

- database HA and backups
- NetworkPolicy and secret rotation
- US cluster and multi-region edge routing
- local Docker runtime
- custom customer-owned domains
- billing integration and advanced approval workflows
