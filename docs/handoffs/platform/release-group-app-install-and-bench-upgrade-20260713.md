# Platform Handoff: Release Group App Install And Bench Upgrade

Date: 2026-07-16
Infra workitem: `INF-027`

## Live Infra Status

Infra applied the updated admission policy on the manager cluster on
2026-07-16.

Live manager verification passed:

- existing `bench_test.status` Platform smoke Job still succeeds;
- digest-pinned current launch Release Group runtime images are admitted for app-aware `bench.update`; live evidence used `ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:<digest>`;
- old `ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:<digest>`
  images are denied for app-aware `bench.update`;
- mutable `ghcr.io/lmnaslimited/lensdocker/lens-pure:<tag>` images are denied;
- unlabelled Jobs are denied;
- Secret-volume Jobs are denied;
- Platform still cannot list/read Secrets or read pod logs;
- default and unapproved namespace creation remains denied.

E2E runtime-image verification also passed on a disposable Bench/Site:

- created Bench `run-20260716-e2e-update-132858-bench` with
  `ghcr.io/lmnaslimited/lensdocker/lens-pure:v16.14.2`;
- created Site `run-20260716-e2e-update-132858-site.cloud.lmnaslens.com`;
- ran `site_bootstrap.install_apps` through the Platform kubeconfig using
  `lens-pure@sha256:fb788e482326f49e93bf7aee96f606a8f6f347d55ba6412943da7d8ea6afa276`;
- installed `erpnext` successfully on the v16.14.2 Site;
- ran `bench.update` through the Platform kubeconfig using
  `lens-pure@sha256:92196b4fb5c016e006c0bddc7ecffd6ba4ad8ce23c6ad290e81840fea0f6bca0`;
- bench-wide migration completed successfully;
- maintenance flags were restored to `maintenance_mode=0` and
  `pause_scheduler=0`;
- patched the disposable Bench runtime to `v16.14.3` and verified all runtime
  deployments rolled to `lens-pure:v16.14.3`;
- verified mounted assets matched the v16.14.3 image cache and contained
  `brandkit` assets;
- fetched `/assets/brandkit/js/demo_banner.js` through the Site URL and got
  HTTP 200 after redirect;
- ran `site_app.install` through the Platform kubeconfig using the v16.14.3
  runtime digest and installed `brandkit` successfully.

Verifier run:

```bash
scripts/58-verify-platform-bench-command.sh
```

## Required Platform Change

For app-aware Bench Commands, Platform must stop using
`ghcr.io/lmnaslimited/lenscloud-bench-command-runner` as the execution image.

The canonical model is:

> `site_bootstrap`, `site_app`, and `bench.update` Jobs run inside the target
> Release Group runtime image, digest-pinned, with the Bench sites PVC mounted
> exactly like the Bench runtime pods.

This matches the current Swarm migration pattern: the one-shot migration
service uses the same Release Group image as the stack.

Existing non-app-aware Bench Commands continue to use the generic runner path.
Do not change existing Platform behavior for maintenance mode, developer mode,
site config, CORS, site setup, OAuth, backup/restore status-style commands,
LATP, or `bench_test.status`.

## Image Selection

For these app-aware families:

| Family | Command | Image Platform must use |
| --- | --- | --- |
| `site_bootstrap` | `site_bootstrap.install_apps` | Release Group runtime image containing selected apps |
| `site_app` | `site_app.install` | Release Group runtime image containing requested app |
| `bench` | `bench.update` | Bench `next_release` runtime image |

Use only immutable digests. Platform derives the runtime image from Release Group and Release metadata:

```text
{Release Group.registry_url}/{Release Group.image_repository}@sha256:{Release.image_digest}
```

`lens-pure` is the current launch Release Group used by Infra acceptance evidence, not a Platform constant. Do not submit mutable tags such as `lens-pure:v16.14.3` in Kubernetes Jobs.

## Implementation Tasks

Implement these as three separate Platform paths.

1. New Site bootstrap app install

   This is part of first-time Site provisioning. After the operator-created base
   Frappe Site exists and before customer handoff, Platform must create a
   `site_bootstrap.install_apps` Job for apps selected on the Release Group
   with `install_at_site_creation`.

   Required behavior:

   - command family: `site_bootstrap`;
   - command: `site_bootstrap.install_apps`;
   - image: Site creation Release Group runtime digest;
   - app source: Release Group child rows where `install_at_site_creation` is
     checked;
   - sorting: ascending `install_sequence`, empty values last;
   - exclude `frappe`;
   - reject duplicates and apps outside the Release Group;
   - retry must be idempotent and treat already-installed apps as skipped.

2. Existing Site app install

   This is a later Capability fulfillment or Platform recovery action on an already Ready Site. Customers request or subscribe to Capabilities; they do not install raw apps. It must not be used as a substitute for first-time bootstrap install.

   Required behavior:

   - command family: `site_app`;
   - command: `site_app.install`;
   - image: current Bench Release Group runtime digest, or the new runtime
     digest after a successful Bench upgrade rollout;
   - app source: requested app must belong to the Site's Bench Release Group;
   - reject `frappe`, duplicates, unknown apps, and apps absent from the
     selected runtime image;
   - retry must be idempotent and treat already-installed apps as skipped.

3. Bench update

   This is a Bench-level action and must not target individual Sites.

   Required behavior:

   - command family: `bench`;
   - command: `bench.update`;
   - image: Bench `next_release` runtime digest;
   - target: Bench only, no Site;
   - require all active Sites on the Bench to be scheduled and tested before
     creating the Job;
   - after migration succeeds, update the target `FrappeBench` runtime image to
     the next Release, wait for rollout, verify assets are fresh, then move
     release pointers.

## Required Job Metadata

Every app-aware Job must include:

```yaml
metadata:
  labels:
    lenscloud.io/managed-by: platform
    lenscloud.io/resource-kind: bench-command
  annotations:
    lenscloud.io/bench-command-family: <site_bootstrap|site_app|bench>
    lenscloud.io/bench-command: <site_bootstrap.install_apps|site_app.install|bench.update>
```

Every app-aware Job must also have:

- `restartPolicy: Never`
- `automountServiceAccountToken: false`
- `backoffLimit <= 1`
- exactly one container
- non-privileged container
- no `envFrom`
- no Secret volumes

## Sites Volume Mount

Platform must mirror the target Bench pod's actual sites mount.

If the Bench pod uses:

```yaml
mountPath: /home/frappe/frappe-bench/sites
subPath: frappe-sites
```

then the Job must use the same mount and subPath.

If the Bench pod mounts the PVC root directly, the Job must mount the root
directly. Do not guess. Derive this from the Bench/operator convention or from
the target Bench pod spec.

When the Bench pod has a separate assets mount, mirror it too:

```yaml
volumeMounts:
  - name: sites
    mountPath: /home/frappe/frappe-bench/sites
    subPath: frappe-sites
    readOnly: false
  - name: sites-assets
    mountPath: /home/frappe/frappe-bench/sites/assets
    subPath: frappe-sites/assets
    readOnly: false
volumes:
  - name: sites
    persistentVolumeClaim:
      claimName: <bench-sites-pvc>
  - name: sites-assets
    persistentVolumeClaim:
      claimName: <bench-sites-pvc>
```

## Bench Update Rendering

Platform should render `bench.update` as the Kubernetes equivalent of the
Swarm `migration` service.

Container image:

```text
Bench next_release runtime image digest
```

Container command:

```yaml
command: ["bash", "-lc"]
args:
  - |
    set -euo pipefail
    bench --site all set-config -p maintenance_mode 1
    bench --site all set-config -p pause_scheduler 1
    bench --site all migrate
    bench --site all set-config -p maintenance_mode 0
    bench --site all set-config -p pause_scheduler 0
```

Target rules:

- target is Bench only;
- no Site target;
- use `next_release`, not `current_release`;
- move `current_release = next_release` only after the Job succeeds;
- after the Job succeeds, update the target `FrappeBench` runtime image to the
  `next_release` runtime tag/digest according to the operator CR schema and
  wait for gunicorn, nginx, scheduler, socketio, and worker deployments to roll
  to the new image before installing newly available apps.

Platform must require all active Sites on the Bench to be scheduled and tested
before creating this Job. Required fields:

- `upgrade_state = Scheduled`
- `upgrade_tested`
- `tested_on`
- `tested_by`

## New Site App Install Rendering

Platform derives `site_bootstrap.install_apps` from Release Group child rows
where `install_at_site_creation` is checked.

Rules:

- exclude `frappe`;
- sort by ascending `install_sequence`, empty values last;
- use stable app identifiers, not labels;
- reject duplicate apps in one payload;
- reject apps not present in the Release Group;
- use the Release Group runtime image containing the selected apps.

Example command body:

```bash
set -euo pipefail
bench --site customer.example.com install-app erpnext
bench --site customer.example.com install-app hrms
```

## Existing Site App Install Rendering

Platform may create `site_app.install` only for apps that are:

- included in the Site's Bench Release Group;
- available in the selected runtime image;
- not already installed, or safe to treat as skipped on retry.

Example command body:

```bash
set -euo pipefail
bench --site customer.example.com install-app payments
```

## Admission Behavior Platform Should Expect

Infra admission allows app-aware families only with:

```text
ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:<64-hex-digest>
```

Admission denies:

- mutable image tags;
- old `lenscloud-bench-command-runner` image for `site_bootstrap`,
  `site_app`, and `bench`;
- unlabelled Jobs;
- unsafe Job shape;
- Secret volumes;
- service-account token mounts;
- privileged containers;
- `envFrom`.

## Infra Templates

Use these infra templates as the canonical Kubernetes Job shapes:

```text
lenscloud-infra/docs/testing/bench-command-runner/site_bootstrap_install_apps_template.yaml
lenscloud-infra/docs/testing/bench-command-runner/site_app_install_template.yaml
lenscloud-infra/docs/testing/bench-command-runner/bench_update_runtime_image_template.yaml
```

The templates default to the current operator layout:

```text
/home/frappe/frappe-bench/sites        -> subPath frappe-sites
/home/frappe/frappe-bench/sites/assets -> subPath frappe-sites/assets
```

If a target Bench pod uses a different sites PVC mount shape, Platform must
mirror the target Bench pod instead of blindly using the default subPath values.

## Result Mapping

For these direct runtime-image Jobs, Platform should map Kubernetes Job/Pod
terminal state into the existing action result model.

Minimum success result:

```json
{
  "phase": "Succeeded",
  "summary": "Bench update completed",
  "details": {
    "target_release": "v16.14.3",
    "operation": "bench --site all maintenance/pause/migrate",
    "exit_code": 0
  },
  "redacted": true
}
```

Minimum failure result:

```json
{
  "phase": "Failed",
  "summary": "Bench update failed",
  "details": {
    "target_release": "v16.14.3",
    "operation": "bench --site all maintenance/pause/migrate",
    "exit_code": 1,
    "error_excerpt": "<sanitized tail>"
  },
  "redacted": true
}
```

Never expose Secret values, kubeconfig material, raw `site_config.json`, DB
passwords, private keys, access tokens, environment dumps, or full logs.


## Capability-Led Fulfillment Revision

The customer-facing construct is now Capability, not App. Platform must model:

- `Capability` as catalogue/master data;
- `Capability App`, `Capability Tool`, and `Capability Skill` bundle rows; Tool and Skill are first-class Link DocTypes, not free-text codes;
- `Subscription Capability` as the durable customer entitlement/progression record;
- `Capability Landscape Policy` as the per-Landscape/Environment progression gate;
- `Site Capability State` as a read-only observed child table on Site.

`Site Capability State` must not be edited directly. It is updated only by customer/platform actions, app-aware command results, or sync. Raw app installation is an implementation detail of fulfilling a Capability.

## Platform Acceptance Checklist

- New Site bootstrap installs Release Group apps selected for site creation.
- Retrying the same app install is idempotent and shows already-installed apps
  as skipped/success.
- Existing Site Capability fulfillment installs only Capability-bundled apps that are present in the Bench Release Group.
- `bench.update` uses the Bench `next_release` runtime image digest.
- `bench.update` runs the bench-wide migration sequence, not per-site
  migrations.
- After `bench.update` succeeds, Platform updates the Bench runtime image and
  waits for rollout before allowing new app installs from the new Release.
- Asset freshness is verified after runtime rollout. At minimum, mounted
  `sites/assets` must contain the assets from the new runtime image; the E2E
  check proved `brandkit` assets served with HTTP 200 after the v16.14.3
  rollout.
- Bench release pointers move only after the Job succeeds.
- A mutable tag image is rejected by admission.
- The old runner image is rejected for `bench.update`.
- Existing non-app-aware Bench Commands still work through the generic runner.
