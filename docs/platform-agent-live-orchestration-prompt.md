# Platform Agent Prompt: Complete Live EU Orchestration

Use this prompt inside the LensCloud Platform devcontainer.

```text
Work inside:

/workspace/frappe-bench/apps/lenscloud

Use the adjacent lenscloud-infra repository as read-only runtime truth. Its
required revision will be supplied in the handoff message. Do not modify Infra.

Read in order:

1. AGENTS.md
2. requirements.md
3. docs/agent-handoff.md
4. docs/platform-workitems.md
5. docs/release-model.md
6. docs/database-server-model.md
7. docs/wildcard-domain-model.md
8. docs/state-model.md
9. docs/workflows.md
10. .agents/skills/frappe-ui-product/SKILL.md
11. lenscloud-infra/docs/platform-handoff-contract.md
12. lenscloud-infra/docs/platform-live-orchestration-readiness.md
13. lenscloud-infra/docs/platform-restricted-access-contract.md
14. lenscloud-infra/docs/database-server-runtime-contract.md
15. lenscloud-infra/docs/wildcard-edge-contract.md

GOAL

Complete live EU orchestration for Public, Private Shared, and Private database
policies. Both a platform operator and a customer using the Free Plan must
create real HTTPS Sites through the same server-side orchestration service.

FIRST RESPONSE

Inspect the actual DocTypes, Python orchestration code, Vue frontend, tests,
current records, and live Infra contracts. Return a decision-complete plan that
names:

- records and resources to retain or retire;
- migrations or code changes still required;
- exact live scenario sequence;
- validation and cleanup steps;
- any genuine external blocker.

Update docs/platform-workitems.md to In Progress, then implement without another
planning loop unless a real external blocker is found.

APPROVED RELEASE

Create or update:

- Release Group: lens-pure
- repository: ghcr.io/lmnaslimited/lensdocker/lens-pure
- Release tag: v16.14.1
- digest:
  sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2
- Frappe: 16.14.0
- ERPNext: 16.13.1
- included app: ERPNext

Use this Release for every acceptance Bench. Do not use lenscx:v15.91.2.

PRECHECK

- run bench migrate;
- run focused backend tests;
- build the frontend;
- verify /run/secrets/lenscloud-eu.kubeconfig is readable server-side;
- run positive and negative permission preflight;
- verify nodes, operators, default/frappe-mariadb, Traefik, storage, wildcard
  TLS, and capacity;
- keep credential content out of logs and APIs.

CLEANUP BEFORE ACCEPTANCE

Inventory current LensCloud Bench and Site records and their exact Kubernetes
resources. Old Benches and Sites may be retired because they are no longer
required.

Preserve:

- MariaDB/default/frappe-mariadb;
- EU Cluster, Region, Database Server, and Platform Settings needed for
  placement;
- operators, namespaces, RBAC, Traefik, wildcard TLS, Certbot, and Headlamp;
- anything not demonstrably owned by a retired LensCloud Bench or Site.

Never delete a namespace or use broad cleanup. Record the inventory and outcome.

LIVE SCENARIOS

Run sequentially with unique run-* operator names.

PUBLIC
- reuse default/frappe-mariadb as Public capacity;
- create Benches for two unrelated customers;
- create one Site for each customer;
- prove both Benches reference the same MariaDB CR;
- prove distinct logical database and credential Secret references;
- verify both Sites and generated assets over HTTPS.

PRIVATE SHARED
- create one customer-owned MariaDB CR;
- attach Quality and Production Benches for that customer;
- create one Site under each Bench;
- reject another customer before apply;
- verify both Sites over HTTPS;
- clean temporary resources after evidence.

PRIVATE
- create one MariaDB CR exclusive to one Bench;
- create one Site and verify HTTPS;
- reject every second Bench, including the same customer;
- clean temporary resources after evidence.

PLATFORM AND CUSTOMER FLOWS

- Platform operator creates/reconciles Database Server, Bench, and Site and sees
  real progress, route/TLS state, URL, errors, and action history.
- Customer Free Plan flow chooses subdomain and eligible Region only.
- Customer never sees Cluster credentials, Database Server internals, or raw
  operator fields.
- Both flows call the same policy and orchestration service.

RUNTIME RULES

- Region selects Cluster; do not use a single global active cluster context.
- Bench uses Release Group plus current Release to resolve the image.
- FrappeBench uses spec.dbConfig.mariadbRef.
- FrappeSite inherits database placement from Bench.
- Standard hostname is {subdomain}.cloud.lmnaslens.com.
- Do not call a DNS provider or create DNS Record, Certificate, or per-Site TLS
  Secret resources.
- Route health requires a successful HTTPS response and static asset response,
  not only operator Ready.
- Reconcile must be idempotent and all actions must be audited without secrets.

UI AND TESTING

Use the repo-local Frappe UI skill. Reuse current LensCloud components and
Frappe UI patterns; do not redesign the product.

Run authenticated Playwright for platform and customer workflows on desktop and
mobile. Verify loading, progress, error, retry, success, permissions, and no
unexpected console errors.

RETURN

- implemented changes;
- migration, test, build, and Playwright results;
- Release Group and Release records;
- retired records/resources;
- each privacy scenario and rejection evidence;
- created Sites and HTTPS/static-asset results;
- action-log references;
- cleanup results;
- remaining production gaps.

Update docs/platform-workitems.md and add a new dated evidence document. Do not
claim completion from CR Ready alone.
```
