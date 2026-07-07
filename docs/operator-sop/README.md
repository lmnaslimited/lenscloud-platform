# LensCloud Operator SOPs

This folder has one canonical operator sequence. Start here, then open the linked SOPs in order. Older focused SOPs remain as supporting references only.

## Canonical Launch Sequence

1. **Cluster/platform handoff**: [Platform test cluster handoff](./platform-test-cluster-handoff.md)
   - Use when Infra hands over a fresh or rebuilt cluster.
   - Configure Platform Settings, Region, Cluster, Release data, Runtime Namespace, and validation gates.
   - Stop if restricted kubeconfig, runtime namespace, root domain, release, or Free Bench capacity is not ready.

2. **Reset and baseline**: [Launch reset and acceptance](./launch-reset-and-acceptance.md)
   - Use before a full acceptance run or when test data must be cleaned.
   - Capture baseline inventory, retire exactly owned test runtime resources, then reset tenant/test records.
   - Never mutate `default/frappe-mariadb` or unlabelled infrastructure.

3. **Free-first Platform and Customer E2E**: [Platform and Customer E2E acceptance](./platform-customer-e2e-acceptance.md)
   - This is the primary launch SOP.
   - Covers Platform readiness, customer signup, Plan browse, Free Subscription, real Site provisioning, customer-safe progress, Account/RBAC checks, evidence, and incidents.
   - CUA setup/OAuth runner slices are executed from this SOP as gated subsegments.

4. **Bench Command runner spot checks**: [Bench Command real Site runner verification](./bench-command-real-site-runner-verification.md)
   - Supporting SOP for operator retests of runner-backed commands on a real Bench/Site.
   - Use only when validating or diagnosing Bench Command contracts.

5. **Lifecycle deep-dive**: [Platform lifecycle acceptance](./platform-lifecycle-acceptance.md)
   - Supporting SOP for Platform-owned runtime inspect/delete/retry behavior.
   - Use when lifecycle changes are touched; it is not the main Free-first launch SOP.

6. **Legacy broad topology test plan**: [Full Platform lifecycle test plan](./full-platform-lifecycle-test-plan-20260625.md)
   - Historical/broad acceptance matrix for multi-tier topology.
   - Use after Free-first launch gates pass and when paid/beta/multi-tier topology is back in scope.

## Current CUA Slice Order

Inside the primary E2E SOP, run CUA slices in this order:

1. `site_setup.status`.
2. `site_setup.complete`.
3. `oauth.status`.
4. `oauth.configure`.
5. User creation, role sync, Site Access Grants, and passwordless Open Site only after INF-023 handoff is complete.

## Runtime Rules

- Operate LensCloud through Platform/customer workspaces and server-side Python Kubernetes API calls.
- Do not install or depend on `kubectl` inside the Platform devcontainer.
- Keep Kubernetes apply disabled except during an approved live provisioning window.
- Never expose kubeconfig, tokens, passwords, Secret values, private keys, pod logs, or full environment dumps.
- Record evidence in `docs/evidence/...` and incidents in `docs/incidents/e2e-incident-tracker.md` before resuming a blocked pass.
