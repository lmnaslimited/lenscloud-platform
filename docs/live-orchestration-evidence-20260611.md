# LensCloud Runtime Lifecycle Evidence - 2026-06-11

## Revisions And Boundary

- Platform implementation base: `818c262` on `version-16`, with the lifecycle changes in the current worktree.
- Infra runtime truth: compatible newer revision `19dd00e` (minimum required `1f57682`).
- Infra checkout was read only during Platform implementation.
- Runtime namespace: `lenscloud-runtime-eu`.
- Restricted kubeconfig reference: `file:/run/secrets/lenscloud-eu.kubeconfig`.
- Platform uses its Python Kubernetes API wrapper only. It does not invoke or require `kubectl`.
- Kubernetes apply remained disabled. No live resources were created or deleted in this pass.

## Implemented

- Stable ownership labels on generated MariaDB, FrappeBench, and FrappeSite manifests:
  `managed-by`, `resource-kind`, `resource-id`, and customer where applicable.
- Platform-created Site and Database Server Secrets receive the same ownership labels; values are never returned or logged.
- Secret-safe runtime inventory for owner CR conditions/finalizers and related Pods, Jobs, PVCs, Services, Ingresses, and warning Events.
- Python API permission preflight covering required runtime access and prohibited default/cluster-scoped access.
- Exact Site, Bench, and Database Server deletion APIs with System Manager role, document-name confirmation, namespace/name identity, ownership-label, protected-resource, dependency, and audit checks.
- Asynchronous deletion states, retry, normal operator-finalizer handling, exact Secret cleanup, and explicit MariaDB PVC `Retain`/`Delete` policy.
- Platform inspect/delete/progress/retry actions. Customer pages continue to expose product-level Site state only.

## Verification

- Migration: passed on `dev.localhost` after both DocType updates.
- Backend tests: 15/15 passed.
- Python compilation: passed.
- Frontend production build: passed.
- Authenticated desktop Playwright: passed.
- Authenticated mobile Playwright at 390x844: passed.
- Disposable Playwright users, Customer record, and mode-600 credential file were removed after testing.
- `ruff` was unavailable in the devcontainer and was not installed.

## Positive And Negative Test Evidence

Covered by focused backend tests:

- ownership labels for all three owner CR manifests;
- customer ownership label propagation;
- warning Event credential redaction;
- unlabelled runtime owner rejection;
- Bench deletion rejection while Sites remain;
- permanent rejection of `MariaDB/default/frappe-mariadb` deletion;
- Private Shared cross-boundary rejection;
- Private second-Bench rejection;
- Python API preflight contract with required allows and prohibited denies.

## Live Gate

The restricted kubeconfig file is readable, but the Python preflight timed out connecting to the Kubernetes API endpoint on port 6443. This is the documented host network authorization condition, not a Kubernetes RBAC denial. Because preflight could not reach the API, the controlled apply window was not opened and no `run-*` acceptance resources or live action logs were created.

The operator should keep the following running on the host, then rerun Platform preflight:

```sh
cd /Users/arunkumar.ganesan/lensk8s/lenscloud-infra
./scripts/52-authorize-platform-api.sh --watch
```

## Remaining Acceptance

After API reachability is restored:

1. Run `check_cluster_permissions` and require both `all_required_allowed=true` and `all_denied_blocked=true`.
2. Inventory existing runtime resources before enabling apply.
3. Open a controlled apply window and run one uniquely prefixed lifecycle create/inspect/delete scenario.
4. Run Private Shared sequentially, verify two HTTPS Sites and cross-customer rejection, then clean through Platform.
5. Run Private sequentially, verify HTTPS and every second-Bench rejection, then clean through Platform.
6. Confirm owner CRs and required dependents are absent, retained PVCs match explicit policy, and `default/frappe-mariadb` remains unchanged.
7. Disable apply and record action-log IDs and HTTPS/static-asset evidence.
