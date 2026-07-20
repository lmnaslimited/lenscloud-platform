# Infra Handoff: Bench Upgrade Assets And Bench Command Runner Digest

Date: 2026-07-19
Owner: Platform is reporting the live failure and desired contract; Infra owns
runtime asset publication, frontend/nginx serving behavior, runner admission,
and the accepted runner image digest.

## Context

During the Release Group app install and Bench upgrade E2E pass, Platform
upgraded:

- Bench: `run-20260702-free-prod-bench`
- Release: `RELEASE-lens-pure-v16.14.3-1`
- Release image digest:
  `sha256:92196b4fb5c016e006c0bddc7ecffd6ba4ad8ce23c6ad290e81840fea0f6bca0`

After the upgrade, Sites served the login/root HTML, but generated assets were
missing from the static path served by nginx/frontend. This matches the known
swarm-era failure mode where restarting containers can temporarily recover
assets because the asset volume is repopulated during startup.

Platform also received a team report that customer Site provisioning can fail
after bootstrap app install because `site_setup.status` /
`site_setup.complete` uses the Bench Command runner image. The team believes
Infra pinned a newer runner digest, while Platform-generated manifests still
contain an older runner digest and are therefore rejected or fail.

## Live Evidence Observed By Platform

HTML route checks returned HTTP 200:

```text
https://tharahub.cloud.lmnaslens.com
https://brandkite2e0717.cloud.lmnaslens.com
```

The HTML preloaded these generated assets:

```text
/assets/frappe/dist/css/website.bundle.D4ZWF75O.css
/assets/erpnext/dist/css/erpnext-web.bundle.QMNL65W2.css
```

Those asset URLs returned HTTP 404 on both checked Sites:

```text
https://tharahub.cloud.lmnaslens.com/assets/frappe/dist/css/website.bundle.D4ZWF75O.css
https://tharahub.cloud.lmnaslens.com/assets/erpnext/dist/css/erpnext-web.bundle.QMNL65W2.css
https://brandkite2e0717.cloud.lmnaslens.com/assets/frappe/dist/css/website.bundle.D4ZWF75O.css
https://brandkite2e0717.cloud.lmnaslens.com/assets/erpnext/dist/css/erpnext-web.bundle.QMNL65W2.css
```

Platform also confirmed the Bench is currently on the new Release:

```text
Bench: run-20260702-free-prod-bench
current_release: RELEASE-lens-pure-v16.14.3-1
next_release: NULL
bench_status: Ready
upgrade_sop_status: Completed
```

Bootstrap app install for the new brandkit-enabled Site succeeded:

```text
Site: brandkite2e0717.cloud.lmnaslens.com
Action Log: ORCH-2026-00545
Operation: site_bootstrap.install_apps
Status: Succeeded
Apps in manifest: erpnext, brandkit
Image in manifest:
ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:92196b4fb5c016e006c0bddc7ecffd6ba4ad8ce23c6ad290e81840fea0f6bca0
```

The later Site setup commands used the Bench Command runner image, not the
Release runtime image:

```text
Action Logs:
- ORCH-2026-00549 site_setup.complete Failed
- ORCH-2026-00555 site_setup.complete Failed

Runner image in Platform manifest:
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:0ba81c0f4031d452eab71a463a562d5f07ace308ae87967725dd807e00c97570
```

## Problem 1: Generated Assets Break After Bench Upgrade

The likely failure mode is:

1. The upgraded image contains new built assets and new asset hashes.
2. Site HTML now references the new hashed assets.
3. The shared assets PVC/static path served by nginx/frontend still contains
   old assets or does not contain the new files.
4. The shared volume masks assets bundled in the image.
5. nginx/frontend returns 404 for the generated assets even though the root
   HTML route returns 200.

Platform should not treat HTML 200 as full UI readiness when generated assets
return 404. Infra should make the Bench upgrade process populate and serve
assets reliably before the Bench/Sites are considered fully upgraded.

## Recommended Permanent Infra Fix

The forum recommendation to add an `assets-init` service is valid in principle,
but LensCloud should implement the Kubernetes/operator equivalent rather than a
docker-compose service.

Implement one of these patterns:

1. Preferred: an `assets-init` initContainer on the frontend/nginx workload.
2. Acceptable: a one-shot post-upgrade asset sync Job followed by a
   frontend/nginx rollout.

Required behavior:

- Use the exact Bench Release image/digest or the exact paired frontend/nginx
  image that contains the built assets. Do not use a generic floating
  `frappe/erpnext-nginx:${FRAPPE_VERSION}` tag.
- Copy or sync bundled assets from the upgraded image into the shared assets PVC
  path served by nginx/frontend.
- Preserve app asset directories for `frappe`, `erpnext`, `brandkit`, and future
  Release Group apps.
- Run before frontend/nginx serves traffic after a Bench upgrade, or run as an
  explicit post-upgrade step before frontend/nginx is rolled.
- Ensure the step is idempotent and safe on retry.
- Do not mark the Bench upgrade complete until generated asset URLs return HTTP
  200 for representative Sites on that Bench.

Example intent only, not a literal compose implementation:

```text
source: assets bundled in the exact upgraded release/frontend image
target: shared assets PVC path served by nginx/frontend
action: copy/sync assets, then start or roll frontend/nginx
verify: root HTML 200 and generated CSS/JS assets 200
```

## Infra Return Expectations For Asset Fix

Please return a dated Platform handoff under:

```text
apps/lenscloud/docs/handoffs/platform/
```

Include:

1. Infra commit revision.
2. Whether the implemented fix is an initContainer, post-upgrade Job, or another
   operator-controlled step.
3. Exact source path inside the image where bundled assets are read from.
4. Exact destination path on the shared assets PVC served by nginx/frontend.
5. Exact image reference/digest used by the asset sync step.
6. Exact copy/sync command or operator code path.
7. Whether stale assets are preserved, overwritten, or pruned.
8. Whether the step covers `frappe`, `erpnext`, `brandkit`, and future app
   assets automatically.
9. Confirmation that the following URLs return HTTP 200 after the fix:

   ```text
   https://tharahub.cloud.lmnaslens.com/assets/frappe/dist/css/website.bundle.D4ZWF75O.css
   https://tharahub.cloud.lmnaslens.com/assets/erpnext/dist/css/erpnext-web.bundle.QMNL65W2.css
   https://brandkite2e0717.cloud.lmnaslens.com/assets/frappe/dist/css/website.bundle.D4ZWF75O.css
   https://brandkite2e0717.cloud.lmnaslens.com/assets/erpnext/dist/css/erpnext-web.bundle.QMNL65W2.css
   ```

10. Confirmation that a fresh generated asset URL from current HTML also returns
    HTTP 200, in case hashes changed during recovery.
11. Any remaining operational command needed for existing upgraded Benches, if
    the permanent fix only applies to future upgrades.

## Problem 2: Bench Command Runner Digest Drift

Platform currently has a hardcoded runner image in
`lenscloud.api.bench_command.RUNNER_IMAGE`:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:0ba81c0f4031d452eab71a463a562d5f07ace308ae87967725dd807e00c97570
```

The failed setup manifests for `brandkite2e0717.cloud.lmnaslens.com` used this
image for `site_setup.complete`.

If Infra has pinned a newer accepted digest, Platform needs that digest as a
configuration value and admission contract. Platform can then make the runner
image configurable and validate that it is digest-pinned before any live Bench
Command job is enqueued.

## Infra Return Expectations For Runner Digest

Please include:

1. The currently accepted full runner image reference with digest.
2. Whether admission currently rejects old runner digests.
3. Exact rejection event/message for stale runner images, if available.
4. Whether runner digest is global, per cluster, per runtime namespace, or per
   Release Group.
5. Whether runner version must match the Bench runtime Release version.
6. Whether Infra expects Platform to source this from:
   - Platform Settings,
   - Cluster,
   - Region,
   - Release Group,
   - Release,
   - or another canonical config surface.
7. Whether multiple runner digests can be accepted during rolling upgrades.
8. Any minimum runner version required for:
   - `site_setup.status`
   - `site_setup.complete`
   - `oauth.status`
   - `oauth.configure`
   - existing Bench Command families

## Expected Platform Follow-Up After Infra Returns

Platform will then:

- Make Bench Command runner image configurable instead of hardcoded.
- Require a digest-pinned runner image for live Bench Commands.
- Surface the configured runner digest in `Orchestration Action Log.message`.
- Keep app-aware bootstrap install on the Release runtime image digest.
- Keep normal Bench Command runner commands on the configured runner digest.
- Treat generated asset 404 as UI/assets-not-ready, not as customer setup
  complete.
- Retry `site_setup.complete` for
  `brandkite2e0717.cloud.lmnaslens.com` after assets and runner digest are
  corrected.

## Acceptance

- Existing upgraded Bench has assets restored without manual container restart.
- Future Bench upgrades publish assets automatically before upgrade is marked
  complete.
- Representative generated CSS/JS asset URLs return HTTP 200 after upgrade.
- Infra returns the accepted Bench Command runner digest contract.
- Platform can update its configurable runner image without guessing.
- A new customer Site with `erpnext` and `brandkit` can complete bootstrap,
  setup, OAuth, and UI asset verification end-to-end.
