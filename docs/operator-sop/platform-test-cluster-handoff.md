# Platform Test Cluster Handoff And Lifecycle SOP

## Purpose

Use this SOP after Infra completes `lenscloud-infra/docs/test-cluster-build-handoff-sop.md` through Stage 15 and delivers the non-secret handoff record plus the restricted kubeconfig through the approved secret channel.

This is a Platform-team SOP. Do not create Hcloud resources, bootstrap K3s, install operators, configure Traefik, issue wildcard TLS, create DNS records, or generate kubeconfigs from Platform.

## Inputs From Infra

Require the completed Stage 15 handoff record before starting. Record its exact values in Platform evidence.

Expected test-cluster values:

| Item | Value |
| --- | --- |
| Cluster | `lenscloud-eu-test` |
| Provider | `hcloud` |
| Region/environment | `EU Test` / `Test` |
| Headlamp URL | `https://headlamp.testcloud.lmnaslens.com` |
| Operator namespace | `frappe-operator-system` |
| Runtime namespace | `lenscloud-runtime-eu` |
| StorageClass | `local-path` |
| Credential reference | `file:/run/secrets/lenscloud-eu-test.kubeconfig` |
| Root domain | `testcloud.lmnaslens.com` |
| Ingress class | `traefik` |
| Shared Public DB | `MariaDB/default/frappe-mariadb` |

Copy manager host/IPs, Kubernetes version, operator versions, wildcard certificate expiry, capacity snapshot, and RBAC evidence from the handoff record. Do not invent or backfill these values.

Do not hard-code old EU dev values in this test cluster:

- `cloud.lmnaslens.com`
- `headlamp.cloud.lmnaslens.com`
- `file:/run/secrets/lenscloud-eu.kubeconfig`
- a single global active Cluster context

## Safety Rules

1. Store only server-side references. Never paste kubeconfig content, tokens, passwords, Secret values, private keys, or TLS private material into LensCloud fields, logs, screenshots, or evidence.
2. Keep `Platform Settings.kubernetes_apply_enabled` off until every validation gate passes.
3. Standard Sites use `{subdomain}.testcloud.lmnaslens.com` and inherited wildcard TLS. Do not call DNS APIs or create DNS Record, Certificate, or per-Site TLS Secret resources.
4. Preserve `MariaDB/default/frappe-mariadb`; Platform may read it but must never mutate or delete it.
5. Platform manages only exact Platform-owned runtime resources with ownership labels and matching document identity.
6. Use normal operator finalizers. Do not manually remove finalizers as a normal Platform action.

## 1. Mount And Register The Restricted Kubeconfig

Infra delivers `lenscloud-eu-test.kubeconfig` through the approved secret channel. Mount it read-only into the Platform backend at:

```text
/run/secrets/lenscloud-eu-test.kubeconfig
```

Use file mode `0600` where the container runtime supports it. In Platform records, store only:

```text
file:/run/secrets/lenscloud-eu-test.kubeconfig
```

If the Platform backend public IP changes, ask Infra to re-authorize port 6443 for the exact `/32`. Platform does not run Infra host scripts as a runtime dependency.

## 2. Configure Platform Settings

Open `/lenscloud/platform/settings` and set:

| Field | Value |
| --- | --- |
| Default plan | `Free` |
| Root domain | `testcloud.lmnaslens.com` |
| Domain strategy | `Wildcard` |
| Default storage class | `local-path` |
| Kubernetes apply enabled | off |

Set external integration fields only if they are part of the current Platform instance. Save and keep apply disabled.

## 3. Create Or Update Region

Open `/lenscloud/platform/regions`.

Create or update the Region used for this cluster:

| Field | Value |
| --- | --- |
| Title/name | `EU Test` |
| Deployment status | `Active` |
| Cluster | select `lenscloud-eu-test` after the Cluster record exists |
| Is group | off unless this is a parent grouping node |

Region selects Cluster. Bench, Site, and Database Server records must choose Region first and derive Cluster from `Region.cluster`.

## 4. Create Or Update Cluster

Open `/lenscloud/platform/clusters` and create or update the Cluster record.

| Field | Value |
| --- | --- |
| Title | `lenscloud-eu-test` |
| Cluster name | `lenscloud-eu-test` |
| Region | `EU Test` |
| Provider | `Hcloud` |
| Environment | `Test` if available; otherwise use the closest non-production value and record the limitation |
| Status | `Active` only after validation gates pass; use `Draft` or `Maintenance` before then |
| Manager host/public IP | copy from Infra handoff record |
| Headlamp URL | `https://headlamp.testcloud.lmnaslens.com` |
| Operator namespace | `frappe-operator-system` |
| Default runtime namespace | `lenscloud-runtime-eu` |
| Default storage class | `local-path` |
| Default bench namespace pattern | `lenscloud-runtime-eu` |
| Kubeconfig reference | `file:/run/secrets/lenscloud-eu-test.kubeconfig` |
| Credential reference | `file:/run/secrets/lenscloud-eu-test.kubeconfig` |
| Domain strategy | `Wildcard` |
| Wildcard hostname | `*.testcloud.lmnaslens.com` |
| Ingress class | `traefik` |

Then return to the `EU Test` Region and set its Cluster link to this record if it was not available during Region creation.

## 5. Register The Default Public Database Server

Open `/lenscloud/platform/database-servers` and create or update a record for the protected shared MariaDB.

Recommended values:

| Field | Value |
| --- | --- |
| Title | `EU Test Shared MariaDB` |
| Database engine | `MariaDB` |
| Provisioning type | `Operator Managed` for an operator CR registered in Kubernetes |
| Region | `EU Test` |
| Privacy | `Public` |
| Kubernetes namespace | `default` |
| MariaDB resource name | `frappe-mariadb` |
| MariaDB image | from Infra handoff record, or `mariadb:10.11` if the handoff confirms that image |
| Storage class | `local-path` |
| Root Secret reference | reference name only if needed for manifest preview; never enter the value |
| Maximum Bench count | `0` for unlimited shared capacity unless Platform policy sets a cap |
| Database status | set to `Ready` only after sync/validation confirms the CR is Ready |
| Health status | set to `Healthy` only after sync/validation confirms readiness |

This record represents protected capacity. Do not run Delete Database Server against it except as a negative rejection test.

## 6. Create Approved Release Data

Create or update Release Group `lens-pure`:

| Field | Value |
| --- | --- |
| Title/name | `lens-pure` |
| Registry URL | `ghcr.io` |
| Image repository | `lmnaslimited/lensdocker/lens-pure` |
| Supported Frappe major | `16` |
| Status | `Active` |
| Included apps | ERPNext, if the App master exists |

Create or update Release `v16.14.1`:

| Field | Value |
| --- | --- |
| Release Group | `lens-pure` |
| Image tag | `v16.14.1` |
| Image digest | `sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2` |
| Build status | `Succeeded` or equivalent ready state |
| Release status | `Production Eligible` |
| Rollout eligibility | `Production Eligible` |
| Compatibility notes | Frappe `16.14.0`, ERPNext `16.13.1` |

Submit the Release if the instance uses Frappe document lifecycle for approved releases. Do not use `lenscx:v15.91.2`.

## 7. Run Platform Validation Gates

Open the Cluster record and run `Validate cluster gates`.

Use:

| Field | Value |
| --- | --- |
| Expected root domain | `testcloud.lmnaslens.com` |
| Dry-run Database Server | the shared Public DB record, if manifest preview is applicable |
| Dry-run Bench | a prepared test Bench record, when available |
| Dry-run Site | a prepared test Site record, when available |

All gates must pass before live apply is enabled:

1. restricted kubeconfig file exists and is readable server-side;
2. Kubernetes API is reachable from the Platform backend;
3. Region resolves to the selected Cluster;
4. runtime namespace accepts namespace-scoped Platform API reads;
5. Frappe Operator API resources exist;
6. MariaDB Operator API resources exist;
7. `default/frappe-mariadb` is readable and Ready;
8. Cluster ingress class is `traefik` and runtime Ingress API is namespace-readable;
9. Platform Settings root domain is `testcloud.lmnaslens.com`;
10. Headlamp HTTPS endpoint is reachable;
11. positive RBAC checks pass;
12. negative RBAC checks remain denied;
13. selected dry-run manifest validation passes;
14. Cluster is marked Healthy before live apply.

Stop if any gate fails. Keep apply disabled, open the latest action result, and hand off to Infra only when the failing item is outside Platform authority, such as DNS/TLS, Headlamp, RBAC, operators, namespace, node capacity, or protected baseline MariaDB health.

## 8. Enable Live Apply Only For A Controlled Window

After all gates pass:

1. Open `/lenscloud/platform/settings`.
2. Enable `Kubernetes apply enabled`.
3. Save.
4. Record the start time and operator.
5. Run one scenario at a time.

The backend refuses live apply when the selected Cluster is not `Healthy`. Dry-run previews remain available for diagnosis.

Disable apply immediately after the controlled acceptance window unless ongoing test operation is explicitly approved.

## 9. Public Bench And Site Smoke

Create a unique run prefix such as:

```text
run-YYYYMMDD-HHMM
```

Create a Public Bench:

| Field | Value |
| --- | --- |
| Title | `<prefix>-public-bench` |
| Release Group | `lens-pure` |
| Current Release | `v16.14.1` |
| Region | `EU Test` |
| Privacy | `Public` |
| Database Server | shared Public DB record |
| Kubernetes namespace | `lenscloud-runtime-eu` |
| Operator resource name | `<prefix>-public-bench` |
| Storage class | `local-path` |

Run `Dry-run FrappeBench`, then `Reconcile bench dry-run` with Dry run off only after the dry-run is clean and apply is enabled. Run `Sync runtime status` until Ready and `Inspect runtime` for conditions, workloads, PVCs, Services, Ingresses, warning Events, and finalizers.

Create a Site:

| Field | Value |
| --- | --- |
| Customer | selected test customer |
| Bench | `<prefix>-public-bench` |
| Region | `EU Test` |
| Plan | `Free` or selected test plan |
| Subdomain | `<prefix>-site` |
| Operator resource name | `<prefix>-site` |

Run `Dry-run FrappeSite`, then `Reconcile Site` with Dry run off. Run `Sync provisioning and access` until the Site is Ready and route status is Ready.

Verify:

- `https://<prefix>-site.testcloud.lmnaslens.com` returns HTTPS success;
- the HTML references a generated static CSS asset;
- that generated asset returns HTTP 200;
- the Site action log contains no credentials or Secret values;
- no DNS Record, Certificate, or per-Site TLS Secret was created by Platform.

## 10. Customer Free Plan Creation

Use a customer user linked to a Customer record.

1. Open `/lenscloud/customer/create-site`.
2. Select Region `EU Test` and Plan `Free`.
3. Enter a unique subdomain under `testcloud.lmnaslens.com`.
4. Submit.
5. Confirm the backend selects ready Public Bench capacity.
6. In the Platform console, verify the created Site record, action logs, HTTPS route, and static asset.

Customers see product-level progress and access URL only. They must not see kubeconfig references, namespaces, Secret references, database internals, or unrelated runtime resources.

## 11. Daily Lifecycle Operations

For Database Server, Bench, and Site records:

- use Preview/Dry-run before first live reconcile;
- use Reconcile only while apply is enabled and validation gates are green;
- use Sync after reconcile to read operator status;
- use Inspect runtime for secret-safe CR conditions, finalizers, workloads, Jobs, PVCs, Services, Ingresses, routes, and warning Events;
- use Retry only after correcting the exact failure named by the action result;
- use Orchestration Action Logs as the audit source for every operation and failure.

Safe deletion order is always:

1. delete Site;
2. confirm Site runtime absence/finalizers complete;
3. delete Bench;
4. confirm Bench runtime absence/finalizers complete;
5. delete a platform-managed Database Server only after attached Benches are absent.

For Database Server deletion, `Retain` preserves attributable PVCs. `Delete` requires attributable PVC cleanup before the document reaches `Deleted`.

## 12. Negative And Protected Tests

Before broad acceptance, prove the following are rejected and audited:

- Delete Database Server for `MariaDB/default/frappe-mariadb`;
- delete an unlabelled runtime resource;
- delete a resource in another namespace;
- cluster-scoped mutation such as CRD or namespace deletion;
- cross-customer Private Shared database attachment;
- second Bench attachment to a Private database.

If a protected operation is allowed, stop immediately, disable apply, and hand the evidence to Infra and Platform leads.

## 13. Privacy Acceptance After Capacity Gates

Run these sequentially only after Public smoke passes and capacity is green.

Public:

- two unrelated customers may share the protected Public Database Server;
- both Sites must reach HTTPS and static asset success;
- both Benches reference the same `mariadbRef`.

Private Shared:

- create one customer-owned MariaDB in `lenscloud-runtime-eu`;
- attach Quality and Production Benches for the same customer/privacy boundary;
- create one HTTPS Site under each Bench;
- reject another customer before Kubernetes apply;
- clean Sites, Benches, then Database Server through Platform.

Private:

- create one exclusive MariaDB/Bench/Site;
- reject every second Bench, including one for the same customer;
- clean Site, Bench, then Database Server through Platform.

## 14. Evidence

For each run, record:

- handoff ID and Infra Git revision from the Stage 15 record;
- Platform revision;
- Platform Settings screenshot or field summary without secrets;
- Region, Cluster, Database Server, Release Group, and Release record names;
- validation gate result and failed-gate details if any;
- apply enable/disable timestamps;
- action log IDs for dry-run, reconcile, sync, inspect, retry, delete, and failures;
- HTTPS and static asset evidence;
- cleanup result;
- protected rejection evidence;
- remaining gaps and owner.

## 15. Stop And Handoff Conditions

Keep apply disabled and hand the issue back to Infra when:

- Platform backend cannot reach the Kubernetes API after the firewall source is refreshed;
- required RBAC is denied or protected RBAC is allowed;
- runtime namespace, CRDs, operators, Traefik, wildcard TLS, Headlamp, or `default/frappe-mariadb` are unhealthy;
- DNS or wildcard HTTPS for `testcloud.lmnaslens.com` fails;
- node pressure or capacity blocks sequential scenarios;
- operator finalizers are stuck after Platform has used normal lifecycle actions.

Keep the issue in Platform when:

- a Region, Cluster, Platform Settings, Release, Bench, Site, or Database Server field is wrong;
- dry-run manifest validation fails due to document data;
- customer Free Plan placement has no ready Public Bench capacity;
- action results identify a Platform policy or ownership-label mismatch.

## 16. Close The Window

After acceptance or stop:

1. Disable `Kubernetes apply enabled` unless ongoing test operation is explicitly approved.
2. Confirm no temporary `<prefix>` Sites or Benches remain unless intentionally retained.
3. Confirm `MariaDB/default/frappe-mariadb` remains Ready.
4. Update dated evidence and handoff notes.
5. Send Infra only non-secret evidence and exact failure ownership.
