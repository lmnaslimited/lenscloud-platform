# LensCloud Platform Cleanup Evidence - 2026-06-25

## Scope

Reset the Platform test tenant/runtime records before a full lifecycle acceptance run.

Protected infrastructure was intentionally preserved:

- `MariaDB/default/frappe-mariadb`
- `Database Server/EU Shared MariaDB 01`
- Cluster, Region, Runtime Namespace, Platform Settings, Release Group, Release, App, Plan, Landscape, Environment, Site Control Profile, Privacy, and Privacy Profile configuration records
- Operators, namespaces, Traefik, wildcard TLS, RBAC, and cluster infrastructure

No kubeconfig, token, password, private key, or Kubernetes Secret value was printed or stored in this evidence.

## Pre-Cleanup Inventory

Platform records found before reset:

- Sites: 13
- Benches: 9
- Database Servers: 4
- Customers: 4
- Subscriptions: 1
- Orchestration Action Logs: 101

Runtime objects visible through the restricted Platform kubeconfig:

- `lenscloud-runtime-eu/FrappeSite`: none
- `lenscloud-runtime-eu/FrappeBench`: none
- `lenscloud-runtime-eu/MariaDB`: none
- `default/MariaDB`: `frappe-mariadb`

The legacy namespace `bench-lenscx-eu-public` was not approved for Platform lifecycle operations and RBAC denied inspection. Any remaining runtime objects in that namespace require Infra-side matched cleanup.

## Cleanup Actions

Kubernetes apply was disabled before cleanup:

- `Platform Settings.kubernetes_apply_enabled = 0`

Lifecycle deletion was attempted for records in the approved runtime namespace. Runtime owners were already absent, so Platform marked them deleted before record cleanup.

Skipped from Platform runtime mutation:

- `default/frappe-mariadb`, protected shared MariaDB
- Records pointing at `bench-lenscx-eu-public`, because that namespace is outside the Platform runtime delete scope

Control-plane test records were then deleted in dependency order:

1. Orchestration Action Logs
2. Sites
3. Benches
4. Platform-managed Database Servers
5. Subscriptions
6. Customers

## Post-Cleanup Verification

Final Platform counts:

- Sites: 0
- Benches: 0
- Database Servers: 1
- Customers: 0
- Subscriptions: 0
- Orchestration Action Logs: 0

Preserved Database Server:

- `EU Shared MariaDB 01`
  - namespace: `default`
  - runtime name: `frappe-mariadb`
  - status: `Ready`
  - retention: `Retain`

Runtime verification:

- `lenscloud-runtime-eu/FrappeSite`: none
- `lenscloud-runtime-eu/FrappeBench`: none
- `lenscloud-runtime-eu/MariaDB`: none
- `default/MariaDB`: `frappe-mariadb`

Runtime namespaces retained:

- `lenscloud-runtime-eu`
  - approved for Platform: yes
  - default runtime namespace: yes
  - status: Active
  - verification: Verified
- `default`
  - approved for Platform: no
  - status: Active
  - verification: Verified

## Infra Follow-Up

Ask Infra to verify whether `bench-lenscx-eu-public` exists and whether any old FrappeBench/FrappeSite resources remain there. Platform did not mutate that namespace because it is outside the approved runtime namespace contract.

