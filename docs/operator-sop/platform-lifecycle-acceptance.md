# Platform Lifecycle Acceptance SOP

## Purpose

Use this SOP to manually validate the LensCloud lifecycle features currently wired into the Platform and customer workspaces:

- Python Kubernetes API preflight;
- ownership-labelled MariaDB, FrappeBench, and FrappeSite reconciliation;
- secret-safe runtime inspection;
- status and HTTPS/static-asset synchronization;
- Site, Bench, and platform-managed Database Server deletion;
- dependency, privacy, ownership, namespace, confirmation, and protected-resource rejection;
- deletion progress and retry;
- customer Free Plan Site creation;
- sequential Private Shared and Private acceptance.

This is an acceptance procedure, not a production provisioning guide.

## Safety Rules

1. Use a unique prefix: `run-YYYYMMDD-HHMM`.
2. Create temporary resources only in `lenscloud-runtime-eu`.
3. Never modify or delete `MariaDB/default/frappe-mariadb`.
4. Never delete a namespace, operator, Traefik, wildcard TLS, Headlamp, RBAC, StorageClass, Node, CRD, or pre-existing resource.
5. Do not read or record kubeconfig content, tokens, passwords, private keys, or Kubernetes Secret values.
6. Run Private Shared and Private sequentially. Finish Platform cleanup before starting the next scenario.
7. Keep Kubernetes apply disabled except during an explicit controlled live window.
8. Standard Sites use `{subdomain}.cloud.lmnaslens.com`. Do not create DNS-provider records or per-Site certificates.
9. Stop immediately if runtime identity, namespace, customer boundary, or ownership is unexpected.

## Required Access

- LensCloud user with `System Manager` for Platform actions.
- A Website User linked to a Customer for the customer test.
- The restricted kubeconfig mounted at `file:/run/secrets/lenscloud-eu.kubeconfig`.
- Host-side API authorization watcher running when the laptop network requires it:

```sh
cd /Users/arunkumar.ganesan/lensk8s/lenscloud-infra
./scripts/52-authorize-platform-api.sh --watch
```

- Release Group `lens-pure` and submitted Release `v16.14.1` using:
  `ghcr.io/lmnaslimited/lensdocker/lens-pure:v16.14.1`
  with digest `sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2`.
- Active EU Region mapped to Cluster `lenscloud-eu-dev`.
- Free Plan active and configured as default/free.
- Enough cluster capacity for one scenario at a time.

Platform URL examples below assume the local base URL `http://dev.localhost:8000/lenscloud`.

## Test Record

Record these before starting:

| Item | Value |
|---|---|
| Date/time | |
| Operator | |
| Run prefix | `run-____________` |
| Platform revision | |
| Infra revision | |
| Region | |
| Cluster | `lenscloud-eu-dev` |
| Runtime namespace | `lenscloud-runtime-eu` |
| Apply initially disabled | Yes / No |

Use two Customers for rejection tests:

- Customer A: owns the Private Shared and Private resources.
- Customer B: must be rejected from Customer A capacity.

## 1. Local Application Preflight

From `/workspace/frappe-bench`:

```sh
bench --site dev.localhost migrate
bench --site dev.localhost run-tests --app lenscloud
```

From `/workspace/frappe-bench/apps/lenscloud/frontend`:

```sh
npm run build
```

Expected:

- migration succeeds;
- all LensCloud backend tests pass;
- frontend production build succeeds.

Do not enable apply if any check fails.

## 2. Kubernetes API Permission Preflight

This is a Platform backend API check. It uses Python and the server-side kubeconfig; it does not use `kubectl`.

From `/workspace/frappe-bench`:

```sh
bench --site dev.localhost execute lenscloud.api.orchestration.check_cluster_permissions \
  --kwargs '{"cluster":"lenscloud-eu-dev"}'
```

Required result:

- `all_required_allowed: true`
- `all_denied_blocked: true`
- `client: python-kubernetes-api-wrapper`
- `kubectl_required: false`

Stop if the API times out. Start or check the host authorization watcher, then retry. Stop if a required permission is denied or a prohibited permission is allowed.

## 3. Confirm Platform Settings

Open `/lenscloud/platform/settings`.

Verify:

- root domain is `cloud.lmnaslens.com`;
- domain strategy is `Wildcard`;
- default storage class and runtime settings match the EU Cluster;
- `Kubernetes apply enabled` is off.

Do not expose the Cluster kubeconfig reference beyond confirming it is a server-side `file:` reference.

## 4. Dry-Run Ownership Check

Before a live scenario, create or open its Database Server, Bench, and Site documents and run:

- Database Server: `Preview MariaDB manifest`
- Bench: `Dry-run FrappeBench`
- Site: `Dry-run FrappeSite`

For every generated owner manifest, verify these labels are present:

```text
lenscloud.io/managed-by: platform
lenscloud.io/resource-kind: database-server | bench | site
lenscloud.io/resource-id: <matching Platform document identity>
lenscloud.io/customer: <Customer A when applicable>
```

Also verify:

- namespace is `lenscloud-runtime-eu` for temporary resources;
- no password, token, Secret value, kubeconfig, or private key is displayed;
- Bench image resolves from `lens-pure` Release `v16.14.1` and the approved digest;
- Site host ends in `.cloud.lmnaslens.com`;
- no per-Site Certificate or DNS-provider resource is generated.

Record the dry-run action-log IDs from `/lenscloud/platform/orchestration-logs`.

## 5. Controlled Apply Window

Open `/lenscloud/platform/settings`, enable `Kubernetes apply enabled`, and save.

Record:

- enable time;
- operator;
- run prefix;
- scenario being executed.

Only one live scenario may exist at a time. Disable apply immediately after the scenario and cleanup are complete, or whenever a stop condition occurs.

## 6. Basic Lifecycle Scenario

Use names derived from the run prefix:

- Database Server: `<prefix>-life-db`
- Bench: `<prefix>-life-bench`
- Site subdomain: `<prefix>-life`

### 6.1 Create Database Server

Open `/lenscloud/platform/database-servers` and select `New Database Server`.

Enter:

- Title: `<prefix>-life-db`
- Database engine: `MariaDB`
- Provisioning type: `Operator Managed`
- Region: active EU Region
- Privacy: `Private`
- Owner Customer: Customer A
- Privacy boundary: Customer A identity
- Kubernetes namespace: `lenscloud-runtime-eu`
- MariaDB resource name: `<prefix>-life-db`
- Storage class: the Cluster default
- Storage size: use the approved acceptance size
- Data retention policy: `Delete` for disposable acceptance data
- Replica count: `1`
- Root Secret reference: `<prefix>-life-db-root`
- Maximum Bench count: `1`

Save, open `Actions`, select `Reconcile Database Server`, leave `Dry run` unchecked, and run.

Repeat `Sync runtime status` until Database status and health are Ready/Healthy. Record action-log IDs.

### 6.2 Inspect Database Server

Run `Inspect runtime`.

Expected:

- exact MariaDB owner CR is present;
- ownership labels match the document and Customer A;
- conditions/finalizers are visible without Secret values;
- related workload, Job, PVC, Service, Ingress, and warning Event sections are present as applicable;
- PVC summary shows name, phase, storage class, and capacity without reading data.

### 6.3 Create Bench

Open `/lenscloud/platform/benches` and select `New Bench`.

Enter:

- Title/operator name: `<prefix>-life-bench`
- Release Group: `lens-pure`
- Current Release: submitted `v16.14.1` Release
- Region: same EU Region
- Privacy: `Private`
- Owner Customer/privacy boundary: Customer A
- Database Server: `<prefix>-life-db`
- Kubernetes namespace: `lenscloud-runtime-eu`
- Storage class: Cluster default

Save and run `Reconcile bench dry-run` with `Dry run` unchecked. Run `Sync runtime status` until Ready, then run `Inspect runtime`.

Expected:

- FrappeBench CR is present and labelled;
- approved image/tag is used;
- database reference points to `<prefix>-life-db`;
- related runtime state contains no Secret values.

### 6.4 Create Site From Platform

Open `/lenscloud/platform/sites` and select `New Site`.

Enter:

- Customer: Customer A
- Bench: `<prefix>-life-bench`
- Region: same EU Region
- Plan: Free Plan or acceptance Plan
- Subdomain: `<prefix>-life`
- Site status: `Requested`
- Provisioning status: `Pending`
- Operator resource name: `<prefix>-life`
- Hostname reservation: `Reserved`

Save and run `Reconcile Site` with `Dry run` unchecked.

Run `Sync provisioning and access` until:

- Site/Provisioning status is Ready;
- Route status is Ready;
- TLS status is Ready;
- Access URL is `https://<prefix>-life.cloud.lmnaslens.com`.

Open the Access URL in a private browser window. Confirm the page loads over HTTPS. From `Sync provisioning and access`, record both page and generated static-asset HTTP success evidence.

Run `Inspect runtime` and record its action-log ID.

## 7. Deletion And Progress Scenario

Deletion order is mandatory: Site, then Bench, then Database Server.

### 7.1 Confirmation Rejection

On the Site, select `Delete site` and enter an incorrect confirmation value.

Expected: deletion is rejected before Kubernetes mutation. The Site remains present.

### 7.2 Dependency Rejection

Before deleting the Site, try `Delete bench` on its Bench using the exact Bench document name.

Expected: rejection lists the dependent Site.

Try `Delete Database Server` while the Bench remains.

Expected: rejection lists the attached Bench.

### 7.3 Delete Site

Run `Delete site` with:

- Confirm document name: the exact Site document name, usually the complete hostname;
- Reason: `Manual lifecycle acceptance <prefix>`.

Expected initial state: `Deletion Requested` or `Deleting`.

Run `Inspect runtime` repeatedly. Do not remove finalizers manually.

Expected completion:

- owner FrappeSite CR becomes absent;
- normal finalizers complete;
- attributable required dependents are absent;
- labelled Platform-created Site Secrets are cleaned by exact name;
- Site status becomes `Deleted`;
- action log records request/progress without Secret values.

If status becomes `Deletion Failed`, correct only the stated safe blocker and use `Retry delete` with the exact document name. Never force-remove a finalizer.

### 7.4 Delete Bench

After the Site is `Deleted`, run `Delete bench` with the exact Bench document name. Poll `Inspect runtime` until the owner CR and required dependents are absent and Bench status is `Deleted`.

### 7.5 Delete Database Server

After no active Bench remains, run `Delete Database Server` with the exact Database Server document name. Poll `Inspect runtime`.

For `Data retention policy = Delete`, expected completion requires attributable PVC cleanup before status becomes `Deleted`.

For `Retain`, the MariaDB CR may be gone while attributable data PVCs remain intentionally. Record retained PVC names and policy; do not delete them manually during this SOP.

## 8. Protected And Scope Rejection

### 8.1 Protected Default MariaDB

If a Platform Database Server record represents `MariaDB/default/frappe-mariadb`, attempt its delete action using exact confirmation.

Expected: Platform rejects it as protected. Stop if any mutation is accepted.

Do not create or alter this record solely to perform the test.

### 8.2 Cross-Namespace Rejection

Create a disposable Database Server document with namespace `default` or another non-runtime namespace, but do not reconcile it. Attempt its delete action.

Expected: Platform rejects deletion because owner CR lifecycle mutation is restricted to `lenscloud-runtime-eu`.

Leave the rejected document as evidence or remove it later through an approved Frappe document-administration procedure. Do not use the runtime delete action as document cleanup.

### 8.3 Unlabelled And Cluster-Scoped Rejection

The Platform UI does not create unlabelled or cluster-scoped resources. These cases are covered by backend tests and Infra admission/RBAC evidence.

Do not create an unlabelled Kubernetes fixture manually unless Infra supplies a dedicated acceptance fixture and cleanup procedure. Never test by attempting to delete a real unrelated resource.

## 9. Private Shared Scenario

Run only after the basic lifecycle resources are cleaned.

Create:

- Database Server: `<prefix>-ps-db`
- Quality Bench: `<prefix>-ps-quality`
- Production Bench: `<prefix>-ps-production`
- Quality Site: `<prefix>-ps-quality.cloud.lmnaslens.com`
- Production Site: `<prefix>-ps-production.cloud.lmnaslens.com`

Database Server settings:

- Privacy: `Private Shared`
- Owner Customer/privacy boundary: Customer A
- Namespace: `lenscloud-runtime-eu`
- Data retention policy: `Delete`
- Maximum Bench count: at least `2`

Both Benches must use:

- Customer A and the same privacy boundary;
- Privacy `Private Shared`;
- the same `<prefix>-ps-db`;
- the approved Release.

Create one Site on each Bench. Reconcile sequentially, sync to Ready, inspect runtime, and verify both HTTPS pages and generated static assets.

### Cross-Customer Rejection

Create a third Bench document using Customer B but attach `<prefix>-ps-db`.

Expected: save/validation or reconcile is rejected before Kubernetes apply because the owner/privacy boundary differs. Record the safe error and any validation action log. No third FrappeBench CR should exist.

### Cleanup

Delete both Sites, then both Benches, then the Database Server through Platform. Poll `Inspect runtime` after each delete. Confirm no required `<prefix>-ps-*` runtime resources remain.

## 10. Private Scenario

Run only after Private Shared cleanup.

Create:

- Database Server: `<prefix>-private-db`
- Bench: `<prefix>-private`
- Site: `<prefix>-private.cloud.lmnaslens.com`

Use Customer A, Privacy `Private`, matching privacy boundary, maximum Bench count `1`, and data retention policy `Delete`.

Reconcile Database Server, Bench, and Site. Sync each to Ready. Verify Site HTTPS and static asset success. Inspect all three runtime owners.

### Second-Bench Rejection

Attempt a second Bench against `<prefix>-private-db`:

1. once with Customer A;
2. optionally with Customer B if the first rejection does not already prove the exclusivity rule.

Expected: every second Bench is rejected before Kubernetes apply. No second FrappeBench CR should exist.

### Cleanup

Delete Site, Bench, and Database Server through Platform in that order. Confirm required `<prefix>-private*` runtime resources are absent.

## 11. Customer Free Plan Scenario

This flow requires ready Public Bench capacity. It does not use the Private Shared or Private Bench.

Log in as the Website User linked to the test Customer and open `/lenscloud/customer/create-site`.

Enter:

- Site name/company: acceptance-safe values;
- Preferred subdomain: `<prefix>-free`;
- Region: EU;
- Plan: Free Plan.

Submit once.

Expected:

- `Site request captured` appears;
- a Customer record is reused or created for the authenticated user;
- the Site is placed only on ready Public capacity;
- the customer sees product-level status and URL, not namespace, CR, database, kubeconfig, or Secret internals;
- with apply enabled, the request uses the same backend Site reconcile path;
- after Platform sync, `https://<prefix>-free.cloud.lmnaslens.com` and a generated asset return success.

Clean this Site from the Platform Site page using the normal delete flow. Do not delete the shared Public Bench or `default/frappe-mariadb`.

## 12. Disable Apply

Open `/lenscloud/platform/settings`, switch `Kubernetes apply enabled` off, and save.

Confirm it remains off after refresh.

## 13. Final Inventory And Evidence

From Platform pages, verify:

- all temporary Sites are `Deleted`;
- all temporary Benches are `Deleted` or explicitly retired only after runtime absence;
- temporary Database Servers are `Deleted`;
- retained PVCs, if any, exactly match an explicit `Retain` policy;
- `default/frappe-mariadb` remains present and unchanged;
- no standard Site created a DNS Record or per-Site certificate;
- apply is disabled.

Capture:

| Evidence | Record |
|---|---|
| Run prefix | |
| Preflight required allowed | |
| Preflight prohibited blocked | |
| Database Server action logs | |
| Bench action logs | |
| Site action logs | |
| Inventory action logs | |
| Rejection messages/logs | |
| HTTPS page results | |
| Static asset results | |
| Deletion/finalizer completion | |
| Secret cleanup by name only | |
| PVC delete/retain result | |
| Apply disabled time | |
| Remaining gaps | |

Do not paste Secret values, passwords, tokens, kubeconfig content, or private keys into evidence.


## Currently Out Of Scope

The following controls may be visible but do not have a completed orchestration backend in this milestone:

- Site suspend;
- Site backup and restore;
- Site or Bench upgrade execution;
- Bench retirement execution;
- the Site page's separate `Create site` action card.

For Platform Site creation, use `New Site`, save the document, then run `Reconcile Site` as described here. Do not report the UI-only controls above as passed lifecycle actions.

## Stop Conditions

Disable apply and stop when any of these occurs:

- Python Kubernetes API preflight fails or times out;
- a required permission is denied or a prohibited permission is allowed;
- a resource resolves outside `lenscloud-runtime-eu` unexpectedly;
- ownership labels do not match the Platform document/customer;
- `default/frappe-mariadb` appears mutable;
- another scenario or unknown workload consumes the sequential capacity;
- deletion requires manual finalizer removal;
- an API/UI response exposes credential or Secret values;
- HTTPS or generated static assets fail after the operator reports Ready.

Record the failure in a dated evidence document and leave apply disabled.
