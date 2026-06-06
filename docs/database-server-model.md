# Database Server Model

## Purpose

Database Server is a first-class LensCloud runtime resource. It represents a MariaDB service that can be provisioned, registered, monitored, and attached to one or more Benches.

Database Server is separate from Bench:

- a Bench deploys one Frappe release family and runtime workload
- a Database Server provides database capacity
- multiple Benches may use the same Database Server when its privacy policy allows it
- Sites inherit the Database Server selected by their Bench

The first implementation targets MariaDB Operator resources. The model should leave room for an externally managed MariaDB service later without weakening the current operator contract.

## Privacy Levels

The supported values are:

Use the existing `Privacy` master DocType and seed exactly `Public`, `Private`, and `Private Shared`. Do not introduce a second competing privacy field type.

### Public

- Platform-managed shared database capacity.
- May serve Benches belonging to unrelated customers.
- Intended for Free and standard shared plans.
- Each Site still receives separate database credentials and a separate logical database.

### Private Shared

- Dedicated to one customer, account, or approved privacy boundary.
- May serve multiple Benches inside that same boundary, such as Quality and Production Benches when policy permits.
- Must not accept Benches from another customer/privacy boundary.

### Private

- Exclusive database capacity for one Bench.
- Must not be attached to a second Bench.
- Intended for the strongest isolation requirement before a future external/managed database option is introduced.

Privacy is a placement and sharing policy. It does not replace Kubernetes network policy, secret isolation, database users, backups, encryption, or regional residency controls.

## Database Server Fields

The platform agent should add a `Database Server` DocType with at least:

- title
- database engine, initially `MariaDB`
- provisioning type: `Operator Managed` or `External`
- Region
- derived Cluster
- privacy level: `Public`, `Private`, or `Private Shared`
- owner Customer/privacy boundary for private modes
- Kubernetes namespace
- operator resource name
- MariaDB image and tag
- storage class
- storage size
- replica count
- service host
- service port
- root/admin credential reference
- application credential secret policy/reference
- node placement policy
- database status
- provisioning status
- health status
- capacity policy or maximum Bench count
- attached Bench count
- last sync time
- last error
- backup policy/status

Raw passwords, kubeconfig content, and cloud credentials must not be stored in normal fields. Store server-side secret references only.

## Bench Relationship

Bench must link to one Database Server before a deployable `FrappeBench` manifest can be produced.

Validation rules:

- Bench Region and Database Server Region must match.
- Bench Cluster and Database Server Cluster must match for an operator-managed MariaDB CR.
- Bench must carry an owner Customer/privacy boundary when it uses Private or Private Shared capacity.
- Database Server must be active/ready, or explicitly accepted as a pending dependency during dry-run.
- `Private` permits one attached Bench only.
- `Private Shared` permits multiple Benches only inside the same owner Customer/privacy boundary.
- `Public` permits multiple eligible Benches.
- Customers do not directly choose Database Server records.
- Plan and platform placement policy select or validate the Database Server.

Sites inherit their database placement from Bench. A Site-level database override is out of scope unless a later requirement explicitly introduces it.

## Operator Mapping

### Database Server to MariaDB

An operator-managed Database Server maps to:

```yaml
apiVersion: k8s.mariadb.com/v1alpha1
kind: MariaDB
metadata:
  name: <database-server.operator_resource_name>
  namespace: <database-server.kubernetes_namespace>
spec:
  rootPasswordSecretKeyRef:
    name: <database-server.root_credential_secret_reference>
    key: password
  image: <database-server.image>
  storage:
    size: <database-server.storage_size>
    storageClassName: <database-server.storage_class>
  replicas: <database-server.replica_count>
  port: 3306
```

The exact generated manifest must follow the installed MariaDB Operator CRD. The platform must not generate or display the root password.

### Bench to Database Server

The `FrappeBench` manifest must carry the default database configuration:

```yaml
spec:
  dbConfig:
    provider: mariadb
    mode: shared
    mariadbRef:
      name: <database-server.operator_resource_name>
      namespace: <database-server.kubernetes_namespace>
```

Here, operator `mode: shared` means one MariaDB instance can host multiple Site databases. It is not the LensCloud privacy level.

### Site

`FrappeSite` should normally inherit `FrappeBench.spec.dbConfig`. The platform should not duplicate database selection on every Site manifest unless the installed operator requires it or a future Site override is approved.

## Required Backend Actions

The platform agent should implement safe server-side actions:

- `dry_run_database_server_manifest(database_server)`
- `reconcile_database_server(database_server, dry_run=True/False)`
- `attach_database_server_to_bench(bench, database_server)`
- `validate_database_server_placement(bench, database_server)`
- database status synchronization from MariaDB CR status

Every action must create an Orchestration Action Log. Real Kubernetes apply remains gated by the secure Cluster credential/apply integration.

## Platform UI

Add a platform-only Database Servers workspace with:

- inventory and health/status
- Region, Cluster, privacy, owner, capacity, and attached Bench count
- create/edit/dry-run/reconcile actions
- attached Benches
- manifest preview without secret values
- errors and recent orchestration history

Bench create/edit must include Database Server placement. The UI should filter compatible Database Servers by Region, Cluster, privacy, owner, readiness, and capacity.

If Bench does not yet have an owner Customer/privacy-boundary field, add one as part of this work. It is required to enforce Private Shared isolation correctly.

Customers should see only a friendly database isolation description derived from their Plan or service level. They must not see database hosts, secret references, MariaDB CR names, or other customers sharing infrastructure.

## First Acceptance Scenario

1. Register the live EU `frappe-mariadb` MariaDB CR as a Database Server.
2. Set Region to EU and Cluster to `lenscloud-eu-dev`.
3. Set privacy to `Public` for the smoke/shared test.
4. Attach two test Benches to the same Database Server.
5. Generate both `FrappeBench` manifests.
6. Verify both manifests reference the same `mariadbRef`.
7. Create Sites under both Benches.
8. Verify each Site receives its own logical database/credentials while sharing the MariaDB server.

This validates the current operating model without claiming database HA.
