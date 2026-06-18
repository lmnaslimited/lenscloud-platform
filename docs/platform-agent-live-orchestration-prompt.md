# Platform Agent Prompt: Build Platform Cluster Handoff And Lifecycle SOP

Use this prompt inside the LensCloud Platform devcontainer.

```text
Work inside:

/workspace/frappe-bench/apps/lenscloud

The adjacent Infra checkout is already cloned. First refresh it:

cd /workspace/lenscloud-infra
git pull --ff-only

Then return to:

/workspace/frappe-bench/apps/lenscloud

Treat Infra as read-only runtime truth. Do not modify Infra from the Platform
agent.

Read in order:

1. AGENTS.md
2. requirements.md
3. docs/agent-handoff.md
4. docs/platform-workitems.md
5. docs/platform-runtime-lifecycle.md
6. docs/release-model.md
7. docs/database-server-model.md
8. docs/wildcard-domain-model.md
9. docs/state-model.md
10. docs/workflows.md
11. .agents/skills/frappe-ui-product/SKILL.md
12. /workspace/lenscloud-infra/docs/test-cluster-build-handoff-sop.md
13. /workspace/lenscloud-infra/docs/test-cluster-handoff-record-template.md
14. /workspace/lenscloud-infra/docs/platform-restricted-access-contract.md
15. /workspace/lenscloud-infra/docs/platform-runtime-lifecycle-handoff.md

Important: the Infra team owns cluster creation. The Platform team does not
create Hcloud nodes, install K3s, install operators, configure Traefik, issue
wildcard TLS, or generate the restricted kubeconfig. Those steps are covered by
Infra's `test-cluster-build-handoff-sop.md`.

Your job is to create the Platform Team SOP for what happens after Infra
handoff.

Do not use stale actual values from `platform-runtime-lifecycle-handoff.md` as
the current cluster record. The current test-cluster values come from the
completed Infra Stage 15 handoff record in
`test-cluster-build-handoff-sop.md`.

PRIMARY DELIVERABLE

Create or update a concise, operator-readable SOP under:

docs/operator-sop/

The SOP must explain how the Platform team:

1. receives the Infra handoff record and restricted kubeconfig reference;
2. creates or updates Platform Settings;
3. creates or updates Region;
4. creates or updates Cluster;
5. creates or updates the default Public Database Server;
6. creates or updates Release Group `lens-pure`;
7. creates or updates Release `v16.14.1`;
8. runs Platform-side cluster validation gates;
9. enables live apply only after all gates pass;
10. performs daily lifecycle operations for Bench, Site, Database Server, and
    customer Free Plan provisioning;
11. performs safe inspect, retry, suspend/retire/delete workflows;
12. disables or blocks live apply when validation fails;
13. records evidence and hands issues back to Infra when the failure is outside
    Platform authority.

Use these handoff values as the example test cluster:

- Cluster: `lenscloud-eu-test`
- Provider: `hcloud`
- Region/environment: EU Test / Test
- Headlamp URL: `https://headlamp.testcloud.lmnaslens.com`
- Operator namespace: `frappe-operator-system`
- Runtime namespace: `lenscloud-runtime-eu`
- StorageClass: `local-path`
- Credential reference: `file:/run/secrets/lenscloud-eu-test.kubeconfig`
- Root domain: `testcloud.lmnaslens.com`
- Ingress class: `traefik`
- Shared Public DB: `MariaDB/default/frappe-mariadb`

The SOP must clearly say not to hard-code old EU dev values:

- `cloud.lmnaslens.com`
- `headlamp.cloud.lmnaslens.com`
- `file:/run/secrets/lenscloud-eu.kubeconfig`
- single global active cluster context

PLATFORM VALIDATION GATES

Document and, if missing, implement Platform-side validation gates for:

1. restricted kubeconfig file exists and is readable server-side;
2. Kubernetes API is reachable from the Platform backend;
3. Region resolves to the selected Cluster;
4. runtime namespace exists;
5. Frappe Operator CRDs exist;
6. MariaDB Operator CRDs exist;
7. `default/frappe-mariadb` is readable and Ready;
8. Traefik ingress class exists;
9. root domain is configured as `testcloud.lmnaslens.com`;
10. Headlamp HTTPS endpoint is reachable;
11. positive RBAC checks pass;
12. negative RBAC checks remain denied;
13. dry-run manifest validation passes;
14. live apply is refused if any gate fails.

Expose these gates in the Platform UI if the UI does not already provide a
clear operator surface. Never expose kubeconfig contents, tokens, passwords,
Secret values, or raw Secret lists.

APPROVED RELEASE

The SOP should instruct Platform users to create/use:

- Release Group: `lens-pure`
- repository: `ghcr.io/lmnaslimited/lensdocker/lens-pure`
- Release tag: `v16.14.1`
- digest:
  `sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2`
- Frappe: `16.14.0`
- ERPNext: `16.13.1`

Do not use `lenscx:v15.91.2`.

DAY-IN-THE-LIFE SOP SCENARIOS

Document the exact Platform Team operating scenarios after cluster validation:

1. register/validate cluster readiness;
2. create or reconcile a Public Bench using `default/frappe-mariadb`;
3. create a Site and verify HTTPS plus static assets;
4. create a customer Free Plan Site through the same backend service;
5. inspect runtime status without secrets;
6. retry failed reconcile safely;
7. delete Site, then Bench, through audited lifecycle actions;
8. reject protected `default/frappe-mariadb` deletion;
9. run Public, Private Shared, and Private database privacy acceptance only
   after capacity gates are green.

RUNTIME RULES TO INCLUDE

- Region selects Cluster.
- Bench uses Release Group plus Release.
- Bench attaches to Database Server.
- `FrappeBench` uses `spec.dbConfig.mariadbRef`.
- `FrappeSite` inherits database placement from Bench.
- Standard test hostname is `{subdomain}.testcloud.lmnaslens.com`.
- Do not call DNS APIs for standard Sites.
- Do not create DNS Record, Certificate, or per-Site TLS Secret resources.
- Route health requires HTTPS success and static asset success, not only
  operator Ready.
- Every validation, reconcile, inspect, retry, delete, and failure must be
  audited without secrets.

CODE CHANGES

If the current Platform code cannot support this SOP, make only the minimal
code/UI changes required for:

- Cluster/Region/Platform Settings setup;
- cluster validation gates;
- operator-readable readiness status;
- safe live-apply enablement/disablement;
- lifecycle actions already defined in `docs/platform-runtime-lifecycle.md`.

Do not start broad redesign work.

RETURN

- SOP file path;
- any Platform code/UI changes made to support the SOP;
- tests/build/migration results;
- validation-gate behavior;
- remaining gaps before the Platform team can run the SOP end to end.
```
