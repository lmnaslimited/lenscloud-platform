# LensCloud Platform Agent Handoff

## Purpose

This is the canonical handoff for active LensCloud Platform implementation.
Keep it short. Product rules belong in the linked domain documents; completed
evidence belongs in dated evidence records.

## Current Objective

Complete live EU orchestration for three database privacy policies:

1. Public
2. Private Shared
3. Private

Both platform operators and customers using the Free Plan must create real
Sites through the same server-side orchestration service.

## Runtime Truth

- cluster: `lenscloud-eu-dev`
- region: EU
- runtime namespace: `lenscloud-runtime-eu`
- shared Public MariaDB: `MariaDB/default/frappe-mariadb`
- Frappe Operator: `ghcr.io/vyogotech/frappe-operator:4.0.0`
- operator API: `vyogo.tech/v1`
- ingress class: `traefik`
- root domain: `cloud.lmnaslens.com`
- Headlamp: `https://headlamp.cloud.lmnaslens.com`
- restricted kubeconfig:
  `file:/run/secrets/lenscloud-eu.kubeconfig`
- wildcard DNS, TLS, routing, operators, nodes, storage, and restricted RBAC:
  Ready

Authoritative runtime details are in the adjacent `lenscloud-infra` repo:

- `docs/platform-handoff-contract.md`
- `docs/platform-live-orchestration-readiness.md`
- `docs/platform-restricted-access-contract.md`
- `docs/database-server-runtime-contract.md`
- `docs/wildcard-edge-contract.md`

## Approved Release

Create or update this platform data:

- Release Group: `lens-pure`
- registry/repository:
  `ghcr.io/lmnaslimited/lensdocker/lens-pure`
- Release tag: `v16.14.1`
- digest:
  `sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2`
- Frappe: `16.14.0`
- ERPNext: `16.13.1`
- included app: ERPNext
- build/release status: deployable after platform-side validation

This image passed live Frappe Operator acceptance:

- operator asset cache and PVC synchronization passed;
- Bench and Site reached Ready;
- login and generated CSS returned HTTPS 200;
- Administrator authentication passed.

Do not deploy `lenscx:v15.91.2`; it lacks the operator asset cache.

## Existing Implementation

The current code already includes:

- Database Server model and UI;
- Bench-to-Database Server attachment;
- Public, Private Shared, and Private policy validation;
- MariaDB, FrappeBench, and FrappeSite manifest generation;
- gated, idempotent Kubernetes apply;
- status synchronization and orchestration action logging;
- wildcard hostname and inherited TLS handling;
- platform and customer Site workflows;
- focused backend tests and frontend build coverage.

Inspect and reuse this implementation. Do not rebuild it from scratch.

## Cleanup Authority

Old LensCloud Bench and Site records are no longer required for this milestone.
The Platform agent may retire them and their matched FrappeBench/FrappeSite
resources after producing an inventory.

Preserve:

- `MariaDB/default/frappe-mariadb`;
- Database Server and Cluster records needed for EU placement;
- operators, namespaces, RBAC, Traefik, wildcard TLS, Certbot, and Headlamp;
- resources not demonstrably owned by a retired LensCloud Bench or Site.

Never delete a namespace or use a broad label/name pattern without first
showing the exact matched resources.

## Acceptance Scenarios

Run sequentially with unique `run-*` resource names.

### Public

- Register or reuse `default/frappe-mariadb`.
- Create Benches for two unrelated customers.
- Create one Site for each customer.
- Prove both Benches reference the same MariaDB CR.
- Prove distinct logical databases and credential Secret references.
- Verify both Sites over HTTPS.

### Private Shared

- Create one customer-owned MariaDB CR.
- Attach Quality and Production Benches for the same customer.
- Create one Site under each Bench.
- Reject attachment by another customer before Kubernetes apply.
- Verify both Sites over HTTPS.

### Private

- Create one MariaDB CR exclusive to one Bench.
- Create one Site and verify it over HTTPS.
- Reject every second Bench, including one for the same customer.

## Completion Contract

The milestone is complete only when:

- Release Group `lens-pure` and Release `v16.14.1` drive the Bench image;
- all three privacy scenarios pass;
- platform and customer Free Plan creation use the same backend;
- route health requires real HTTPS success, not only operator Ready;
- no standard Site creates DNS or Certificate resources;
- repeated reconcile is idempotent;
- all actions and failures are audited without secrets;
- authenticated Playwright covers platform and customer flows;
- temporary Private Shared and Private resources are cleaned safely;
- workitems and dated evidence are updated.

## Reading Order

1. `AGENTS.md`
2. `requirements.md`
3. this file
4. `docs/platform-workitems.md`
5. `docs/release-model.md`
6. `docs/database-server-model.md`
7. `docs/wildcard-domain-model.md`
8. `docs/state-model.md`
9. `docs/workflows.md`
10. `.agents/skills/frappe-ui-product/SKILL.md`
11. the Infra contracts listed under Runtime Truth

Use `docs/platform-agent-live-orchestration-prompt.md` as the executable agent
prompt.
