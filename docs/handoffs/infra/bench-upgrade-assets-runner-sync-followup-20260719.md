# Infra Handoff: Bench Upgrade Asset Recovery And Runner Contract Sync Follow-Up

Date: 2026-07-19
Owner: Platform implemented the synced Cluster-side runner contract; Infra owns the remaining cluster RBAC/asset recovery work.

## Context

This follows the broader handoff:

```text
apps/lenscloud/docs/handoffs/infra/bench-upgrade-assets-and-runner-digest-20260719.md
```

Infra returned guidance in:

```text
apps/lenscloud/docs/handoffs/platform/bench-upgrade-assets-and-runner-digest-20260719.md
```

Platform has now changed the runner model based on operator feedback:

- Runner digest is not read from Kubernetes on every Bench Command.
- Cluster has read-only synced fields:
  - `bench_command_runner_image`
  - `bench_command_runner_contract_status`
  - `bench_command_runner_contract_checked_on`
  - `bench_command_runner_contract_error`
- Platform added explicit sync API:

  ```text
  lenscloud.api.bench_command.sync_cluster_bench_command_runner_contract
  ```

- Generic Bench Commands use the synced Cluster field.
- Platform still server-side dry-runs generated Jobs so stale synced digests are caught by admission and surfaced as:

  ```text
  BENCH_COMMAND_RUNNER_IMAGE_REJECTED
  ```

App-aware commands still use the Release runtime digest, not the generic runner:

- `site_bootstrap.install_apps`
- `site_app.install`
- `bench.update`

## Current Live Blocker 1: Platform Cannot Sync Runner Contract

Platform ran:

```bash
bench --site dev.localhost execute lenscloud.api.bench_command.sync_cluster_bench_command_runner_contract --args ["lenscloud-eu-dev"]
```

Live result:

```text
Cluster: lenscloud-eu-dev
bench_command_runner_image: NULL
bench_command_runner_contract_status: Failed
bench_command_runner_contract_checked_on: 2026-07-19 14:39:28.528127
```

Sanitized error:

```text
Kubernetes API 403: configmaps "lenscloud-platform-cluster-contract" is forbidden:
User "system:serviceaccount:lenscloud-platform-system:lenscloud-platform"
cannot get resource "configmaps" in API group "" in namespace "lenscloud-platform-system"
```

## Infra Ask 1: Grant Contract ConfigMap Read

Please grant the Platform service account read access to exactly this contract:

```text
namespace: lenscloud-platform-system
resource: configmaps
name: lenscloud-platform-cluster-contract
verb: get
key used by Platform: bench_command_runner_image
```

Expected Platform sync command after fix:

```bash
bench --site dev.localhost execute lenscloud.api.bench_command.sync_cluster_bench_command_runner_contract --args ["lenscloud-eu-dev"]
```

Expected Platform DB state after sync:

```text
bench_command_runner_contract_status = Synced
bench_command_runner_image = ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:<accepted-digest>
bench_command_runner_contract_error = NULL
```

Please return:

1. Infra commit revision.
2. Exact RBAC object(s) changed.
3. `kubectl auth can-i get configmaps --as system:serviceaccount:lenscloud-platform-system:lenscloud-platform -n lenscloud-platform-system` result, scoped as narrowly as possible.
4. The current ConfigMap value for `bench_command_runner_image`.
5. Confirmation that Platform can sync the Cluster contract successfully, or the exact remaining rejection.

## Current Live Blocker 2: Existing Bench Assets Still Return 404

The upgraded Bench is still serving HTML while generated assets are missing:

```text
Bench: run-20260702-free-prod-bench
current_release: RELEASE-lens-pure-v16.14.3-1
release image digest: sha256:92196b4fb5c016e006c0bddc7ecffd6ba4ad8ce23c6ad290e81840fea0f6bca0
```

Platform rechecked the previously broken asset URL after implementing strict asset readiness:

```text
https://tharahub.cloud.lmnaslens.com/assets/frappe/dist/css/website.bundle.D4ZWF75O.css -> HTTP 404
https://brandkite2e0717.cloud.lmnaslens.com/assets/frappe/dist/css/website.bundle.D4ZWF75O.css -> HTTP 404
```

So the current upgraded Bench has not yet recovered assets from the operator v4.1.1 rollout.

## Infra Ask 2: Recover Current Bench Assets And Verify v4.1.1 Init

Please verify and/or trigger the operator v4.1.1 asset initialization for:

```text
FrappeBench: run-20260702-free-prod-bench
Runtime namespace: lenscloud-runtime-eu
Expected runtime tag from release: ghcr.io/lmnaslimited/lensdocker/lens-pure:v16.14.3
```

Please return:

1. Current `FrappeBench.status.initializedImage` for `run-20260702-free-prod-bench`.
2. Whether it equals the expected immutable runtime tag.
3. Whether the operator recreated/completed the Bench init Job after the image tag change.
4. The relevant init/migration Job name and terminal status.
5. Confirmation that current HTML-generated CSS and JS URLs return HTTP 200 for:
   - `tharahub.cloud.lmnaslens.com`
   - `brandkite2e0717.cloud.lmnaslens.com`
6. If the old hashes changed, include the fresh generated CSS/JS URLs parsed from current HTML and their HTTP statuses.
7. Any one-time recovery command needed for the existing upgraded Bench if v4.1.1 only protects future upgrades.

## Platform Retest After Infra Returns

After Infra returns this handoff, Platform will:

1. Run Cluster runner contract sync.
2. Confirm the read-only Cluster fields are populated.
3. Retry/continue customer provisioning for `brandkite2e0717.cloud.lmnaslens.com`.
4. Verify generic Bench Commands use the synced Cluster runner digest:
   - `site_setup.status`
   - `site_setup.complete`
   - `oauth.status`
   - `oauth.configure`
5. Verify app-aware commands continue using the Release runtime digest.
6. Verify generated CSS and JS assets return HTTP 200.
7. Run a clean customer-side provisioning E2E, preferably on a fresh/disposable Bench if capacity permits.
8. Update/close incidents:
   - `LC-E2E-20260719-001`
   - `LC-E2E-20260719-002`
   - `LC-E2E-20260717-001`

## Acceptance

- Platform can sync `bench_command_runner_image` onto Cluster without Kubernetes 403.
- Generic Bench Commands use the synced Cluster digest and pass admission dry-run.
- Existing upgraded Bench asset URLs recover to HTTP 200.
- Bench upgrade readiness is not marked complete unless current generated CSS and JS assets return HTTP 200.
- Customer provisioning reaches and passes `site_setup.status` using the synced Cluster runner digest.
