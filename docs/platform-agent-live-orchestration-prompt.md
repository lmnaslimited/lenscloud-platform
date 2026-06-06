# Platform Agent Prompt: Live Orchestration Milestone

Use the following prompt inside the `lenscloud-platform` devcontainer.

```text
You are the implementation agent for the next LensCloud Platform milestone.

Work inside:

/workspace/frappe-bench/apps/lenscloud

The same host workspace also contains the authoritative infrastructure repo at:

/Users/arunkumar.ganesan/lensk8s/lenscloud-infra

If that host path is not mounted in the devcontainer, clone or mount
lmnaslimited/lenscloud-infra as read-only reference context. Check if the repo is at the recent commit before referencing it. If not pull the recent changes. Do not modify
lenscloud-infra unless the user explicitly assigns an infra work item.

GOAL

Finish LensCloud's first live EU orchestration slice. The milestone is complete
when both a platform operator and a customer using the Free Plan can create a
real Site through LensCloud, and when Public, Private Shared, and Private
database policies are proven against the live Frappe and MariaDB Operators.

MANDATORY READING ORDER

1. AGENTS.md
2. requirements.md
3. docs/agent-handoff.md
4. docs/platform-workitems.md
5. docs/state-model.md
6. docs/workflows.md
7. docs/database-server-model.md
8. docs/wildcard-domain-model.md
9. docs/platform-gap-backlog.md
10. docs/skills.md
11. docs/mcps.md
12. .agents/skills/frappe-ui-product/SKILL.md
13. .agents/skills/frappe-ui-product/references/frappe-ui-patterns.md
14. .agents/skills/frappe-ui-product/references/lenscloud-ui-contract.md
15. lenscloud-infra/docs/platform-handoff-contract.md
16. lenscloud-infra/docs/platform-restricted-access-contract.md
17. lenscloud-infra/docs/database-server-runtime-contract.md
18. lenscloud-infra/docs/wildcard-edge-contract.md
19. lenscloud-infra/docs/live-eu-cluster-status.md

FIRST RESPONSE AND WORKITEM DISCIPLINE

Inspect the actual DocTypes, Python orchestration code, Vue frontend, tests, and
installed dependencies before proposing changes.

Your first response must contain a decision-complete implementation plan. It
must identify:

- exact model and migration changes;
- backend APIs and credential handling;
- idempotent apply and status-sync design;
- UI changes;
- Public, Private Shared, and Private test fixtures;
- live rollout order and cleanup;
- external blockers, if any.

After the plan, update the canonical rows in docs/agent-handoff.md and
docs/platform-workitems.md to In Progress, then implement without starting
another planning loop. Stop only if the restricted kubeconfig artifact is
genuinely unavailable or a live-cluster safety condition prevents apply.

CURRENT RUNTIME TRUTH

- cluster: lenscloud-eu-dev
- region: EU
- Frappe Operator API: vyogo.tech/v1
- Frappe Operator image: ghcr.io/vyogotech/frappe-operator:4.0.0
- MariaDB API: k8s.mariadb.com/v1alpha1
- existing shared MariaDB: default/frappe-mariadb
- ingress class: traefik
- root domain: cloud.lmnaslens.com
- wildcard hostname: *.cloud.lmnaslens.com
- Headlamp: https://headlamp.cloud.lmnaslens.com
- wildcard DNS, wildcard TLS, public Traefik cutover, and dynamic host routing:
  Ready
- standard Sites require no DNS-provider call, DNS Record, Certificate, ACME
  challenge, or per-Site TLS Secret
- MariaDB is currently one replica on local-path and is not HA

CURRENT IMPLEMENTATION AND REMAINING GAPS

- Database Server, Bench attachment, privacy/capacity policy, structured
  manifests, gated server-side apply, status synchronization, wildcard Site
  routing, UI surfaces, and focused tests are implemented locally.
- The restricted kubeconfig is mounted read-only at
  `/run/secrets/lenscloud-eu.kubeconfig`.
- The Cluster default runtime namespace is `lenscloud-runtime-eu`.
- `lenscloud.api.orchestration.check_cluster_permissions` returns
  `all_required_allowed: true`.
- Real apply remains intentionally disabled until the controlled acceptance
  sequence begins.
- Public, Private Shared, and Private live scenarios, HTTPS acceptance,
  authenticated Playwright, evidence capture, and cleanup remain incomplete.
- Verify the implementation against current code and published infra revision
  `1d5d5f3`; do not rebuild already completed local-control-plane work without
  evidence of a defect.

MODEL AND POLICY REQUIREMENTS

Add Database Server as a platform-only first-class DocType. Reuse the existing
Privacy records exactly:

- Public
- Private Shared
- Private

Do not add another privacy enum that competes with the Privacy master.

Database Server must include the fields needed by
docs/database-server-model.md, including Region, derived Cluster, privacy,
owner Customer/privacy boundary, namespace, MariaDB operator resource name,
image, storage, replica count, root Secret reference, readiness, capacity,
attached Bench count, sync state, and errors.

Bench must link to Database Server and carry the owner Customer/privacy boundary
needed for validation. Sites inherit database placement from Bench. Customers
must never select a Database Server or see its Kubernetes/credential details.

Enforce:

- Region and derived Cluster match between Bench and operator-managed Database
  Server.
- Public may serve eligible Benches from unrelated customers.
- Private Shared may serve multiple Benches only for the same owner Customer or
  approved privacy boundary.
- Private permits exactly one Bench.
- only ready capacity may be used for live apply;
- capacity limits are enforced;
- Frappe Operator dbConfig.mode=shared is topology and does not weaken LensCloud
  privacy rules.

BACKEND AND SECURITY REQUIREMENTS

Implement server-side, idempotent dry-run, apply, and status synchronization for:

- MariaDB
- FrappeBench
- FrappeSite
- Site ingress/route readiness

Use the restricted kubeconfig reference delivered under
lenscloud-infra/docs/platform-restricted-access-contract.md. Recommended
reference:

file:/run/secrets/lenscloud-eu.kubeconfig

Never return or log kubeconfig content, bearer tokens, passwords, Kubernetes
Secret values, GoDaddy credentials, or TLS private keys.

Use structured YAML generation/parsing rather than ad hoc concatenation for new
manifest work. Compare generated resources with the installed live CRDs before
apply.

Reconcile by namespace, kind, and operator resource name. Repeated reconcile
must update the same resource and must not create duplicates.

Every dry-run, validation failure, apply, status transition, and runtime failure
must create or update an Orchestration Action Log with secret-safe details.

Update LensCloud statuses from Kubernetes rather than treating an accepted API
request as successful provisioning.

BENCH AND SITE MANIFEST REQUIREMENTS

FrappeBench must include:

spec:
  dbConfig:
    provider: mariadb
    mode: shared
    mariadbRef:
      name: <database-server operator resource>
      namespace: <database-server namespace>

FrappeSite normally inherits Bench database configuration. Do not add a
Site-level Database Server selector.

Standard Site identity is the full hostname:

{subdomain}.cloud.lmnaslens.com

FrappeSite.spec.siteName and the Traefik host route must use that full hostname.
Do not call Route53, GoDaddy, Cloudflare, or another DNS provider. Do not create
a standard-Site DNS Record, Certificate, or per-Site TLS Secret.

Replace DNS transaction state with hostname reservation, route status, inherited
wildcard TLS status, last route check, and route error. Keep DNS Record only as
a future custom-domain compatibility object.

PLATFORM AND CUSTOMER FLOWS

Platform users must be able to:

- register or create Database Server capacity;
- inspect privacy, owner, capacity, readiness, attached Benches, manifest
  preview, status, and orchestration history;
- create or reconcile a Bench from Release Group plus Release;
- create or reconcile a Site;
- follow progress to Ready and open the HTTPS URL.

Customer users must be able to:

- use native Frappe authentication;
- request one Free Plan Site;
- choose an eligible Region and subdomain;
- never choose Bench, Database Server, Cluster credentials, or operator fields;
- see real provisioning and access status;
- open the Site after it becomes Ready.

Both entry points must call the same server-side orchestration service and policy
engine.

UI RULES

Apply the repo-local $frappe-ui-product skill.

Prefer installed Frappe UI components, existing LensCloud components, and Frappe
CRM main patterns compatible with Frappe v16. Do not introduce another UI
framework or a bespoke design system.

Provide real loading, empty, permission, validation, disabled, confirmation,
progress, success, failure, and retry states. Keep platform screens compact and
operational. Keep customer screens simple and hide infrastructure details.

PRIVACY ACCEPTANCE SCENARIOS

Run sequentially to limit EU cluster usage.

1. Public
   - register default/frappe-mariadb as EU Shared MariaDB 01;
   - attach Benches owned by two unrelated customers;
   - create at least one Site for each customer;
   - prove separate logical databases and credentials.

2. Private Shared
   - create one operator-managed MariaDB owned by Customer A;
   - attach Customer A Quality and Production Benches;
   - create one Site under each Bench;
   - prove Customer B attachment is rejected before apply.

3. Private
   - create one operator-managed MariaDB exclusive to one Bench;
   - create one Site;
   - prove every second Bench is rejected, including one owned by the same
     customer.

Retain the Public baseline. Temporary Private Shared and Private resources may
be removed after evidence is captured if capacity is tight. Document cleanup
commands and never delete pre-existing resources.

VALIDATION AND COMPLETION

Before live apply:

- run bench migrate;
- run focused backend tests;
- build the frontend;
- validate generated manifests against installed CRDs;
- verify restricted positive and negative Kubernetes permissions;
- verify cluster capacity.

Then:

- run all three privacy scenarios;
- verify each created Site over HTTPS;
- verify no standard-Site DNS Record or Certificate was created;
- run authenticated Playwright tests for platform and customer flows on desktop
  and mobile;
- verify no browser console errors;
- update canonical workitems with evidence;
- document created platform records, Kubernetes resources, URLs, failures, and
  cleanup commands.

In the final report distinguish:

- implemented and live-verified behavior;
- implemented but dry-run-only behavior;
- external blockers;
- remaining production-readiness work, especially database HA, backups,
  NetworkPolicy, secret rotation, monitoring, US region, and multi-region edge
  routing.

Do not modify lenscloud-infra during this assignment. Do not claim completion
without live runtime and HTTPS evidence.
```
