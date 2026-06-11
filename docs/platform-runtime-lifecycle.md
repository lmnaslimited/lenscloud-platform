# Platform Runtime Lifecycle Management

## Purpose

After Infra provisions and registers a Cluster, LensCloud Platform owns the normal lifecycle of tenant runtime resources that LensCloud creates. Routine Site, Bench, and platform-managed Database Server inspection, reconciliation, suspension, retirement, and deletion must not require manager access or an Infra operator.

Infra continues to own the Kubernetes substrate, operators, cluster-level policy, shared edge, and protected baseline resources.

## Ownership Boundary

Platform-owned runtime resources must carry stable metadata:

```yaml
metadata:
  labels:
    lenscloud.io/managed-by: platform
    lenscloud.io/resource-kind: <database-server|bench|site>
    lenscloud.io/resource-id: <platform-document-name>
    lenscloud.io/customer: <customer-id-when-applicable>
```

A generated run prefix may be recorded as an additional label for acceptance cleanup, but it is not the primary ownership check.

Platform may mutate or delete a runtime resource only when all of these match:

- registered Cluster selected through Region placement;
- expected runtime namespace;
- exact Kubernetes kind and operator resource name stored on the platform document;
- `lenscloud.io/managed-by=platform`;
- matching resource kind and platform document identity labels;
- matching customer/privacy boundary where applicable;
- resource is not protected by the denylist;
- authenticated user has the required platform role;
- destructive confirmation and an Orchestration Action Log exist.

## Protected Resources

Platform must never delete or replace:

- `MariaDB/default/frappe-mariadb`;
- any unrelated or unlabelled resource;
- namespaces, Nodes, CRDs, StorageClasses, or cluster-scoped infrastructure;
- MariaDB/Frappe operators and their workloads;
- Traefik, wildcard TLS, Certbot, Headlamp, RBAC, or infrastructure Secrets;
- resources in another Cluster or namespace.

Protected-resource checks belong in both LensCloud policy and Infra RBAC. UI hiding alone is not a security boundary.

## Backend Transport

Platform talks to Kubernetes only from the Frappe backend through the restricted server-side `file:` kubeconfig reference and the Python Kubernetes API wrapper. Browser responses, action logs, and errors must never contain kubeconfig content, bearer tokens, Secret values, client private keys, or certificate private material. `kubectl` and host-side Infra verifier scripts are not Platform runtime dependencies.

## Platform Lifecycle Actions

Platform-facing actions must include:

- inspect runtime state and related resources;
- reconcile and retry;
- suspend/resume where supported by the operator contract;
- delete Site;
- delete Bench after dependent-Site checks;
- delete platform-managed Database Server after attached-Bench checks;
- retry or diagnose failed deletion;
- retire the control-plane document after runtime deletion is confirmed.

Deleting the owner CR is preferred. Operator owner references and finalizers should clean dependent resources. Direct dependent cleanup is allowed only when the installed operator contract requires it and the resource passes the same ownership checks.

Platform-created credential Secrets must carry the owner labels and may be deleted only by exact name after label validation. A platform-managed Database Server must declare an explicit PVC data policy: `Retain` preserves attributable data PVCs after MariaDB deletion, while `Delete` requires attributable PVC cleanup before the document reaches `Deleted`. Unlabelled PVCs or Secrets are a safe deletion failure, not permission to force cleanup.

## Deletion State Model

Deletion is asynchronous and auditable:

1. `Deletion Requested`
2. `Quiescing`
3. `Deleting`
4. `Deleted`

Failure transitions to `Deletion Failed`, retaining the last safe error and a retry action. A document must not be marked Deleted or Retired until the exact runtime resource is absent and required dependent cleanup is confirmed.

## Runtime Visibility

Platform resource pages must expose a secret-safe runtime summary:

- CR phase, observed generation, conditions, and last transition;
- related workload and Job names/status;
- PVC names, phase, storage class, and requested capacity;
- Service and Ingress names plus route status;
- recent warning Event reasons/messages with secret sanitization;
- finalizer/deletion progress;
- last reconciliation, status-sync, and deletion action logs.

Customers receive only product-level Site status, URL, progress, and safe errors. They must not see namespaces, Secret references, database internals, kubeconfig data, or unrelated tenant resources.

## Infra Contract

Infra must grant the dedicated Platform service account the minimum namespace-scoped verbs needed to get/list/watch/create/patch/update/delete Platform-managed MariaDB, FrappeBench, and FrappeSite resources in `lenscloud-runtime-eu`, plus safe read access to related Pods, Services, Jobs, PVCs, Ingresses, and Events.

Delete access for Jobs, PVCs, and Secrets must be limited to the runtime namespace and the ownership model supported by the admission/RBAC design. Infra must publish positive and negative preflight proving managed deletion works while protected, unlabelled, cross-namespace, and cluster-scoped resources remain denied.

## Acceptance

The lifecycle milestone is complete only when an authenticated platform operator can:

1. create a Database Server, Bench, and Site;
2. see their real runtime and related-resource state;
3. delete the Site through Platform and observe finalizer completion;
4. delete the Bench and platform-managed Database Server through Platform;
5. verify owned Jobs, Secrets, and PVCs are cleaned according to the operator contract;
6. prove protected and unowned deletion attempts are rejected;
7. complete the flow without manager or Infra intervention.
