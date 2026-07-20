# Platform Handoff - `site_setup.status` Mount Failure - 2026-07-20

## Incident

Tracker row: `LC-E2E-20260720-002`.

Reported by: testing team via Arun.

Affected test-cluster command:

```text
Test VM: 167.235.138.49
Command: site_setup.status
Command ID: BCMD-2026-00356
Job: bcmd-2026-00356-job
Site: ubuntu.testcloud.lmnaslens.com
Bench: eu-shared-bench-two
Namespace: lenscloud-runtime-eu
Bench runtime reported by team: lens-pure v16.14.1
Runner image: ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:0ba81c0f4031d452eab71a463a562d5f07ace308ae87967725dd807e00c97570
```

## Symptom

The pod failed before the runner started:

```text
failed to create containerd task
OCI runtime create failed
error mounting ... to rootfs at "/home/frappe/frappe-bench/sites/assets"
create mountpoint for /home/frappe/frappe-...
```

Platform cleanup then removed three resources.

The impacted Site was later deleted because customer provisioning entered a
never-ending loop around `site_setup.status`. Retest must therefore use a fresh
Site on the same test cluster, not the deleted `ubuntu.testcloud.lmnaslens.com`
record.

Platform state fix in this pass: failed `site_setup.status` results now set
`Site.setup_status = Failed` with the sanitized command/Kubernetes message.
They must not be treated as `Required`, because that causes the customer retry
poller to keep scheduling setup status work. Background/status refreshes do not
reset a failed setup state; only an explicit retry may force the next attempt.

## Important Contract Boundary

`site_setup.status` is a generic runner command. It should mount:

```yaml
volumeMounts:
  - name: request
    mountPath: /lenscloud/request
    readOnly: true
  - name: sites
    mountPath: /home/frappe/frappe-bench/sites
    readOnly: true
```

It must not mount `/home/frappe/frappe-bench/sites/assets`.

The nested assets mount is for app-aware runtime-image jobs only, such as:

```text
site_bootstrap.install_apps
site_app.install
bench.update
site_setup.complete
```

Even for app-aware jobs, Platform must mirror the actual Bench pod mount shape:
if the Bench pod uses `subPath: frappe-sites` and a separate
`subPath: frappe-sites/assets` mount, the Job may use that shape. If the Bench
pod mounts only the sites path, omit `sites-assets`.

## Current Code Inspection

Current Platform code in `lenscloud.api.bench_command.job_manifest` mounts only
the `sites` PVC for `site_setup.status`, read-only, with `subPath: frappe-sites`.
The `/sites/assets` mount appears only in `run_app_aware_job`.

Therefore the failing test-cluster evidence must be resolved as one of:

- the failing cluster is running stale Platform code;
- the failing manifest pasted to the team was hand-edited or malformed;
- the real Job YAML differs from the pasted manifest;
- the Bench pod mount shape on the v16.14.1 test Bench requires a different
  `subPath` than the generated generic runner Job.

Live dev Bench mount shape for `run-20260702-free-prod-bench-gunicorn` on
2026-07-20:

```yaml
volumeMounts:
  - mountPath: /home/frappe/frappe-bench/sites
    name: sites
    subPath: frappe-sites
  - mountPath: /home/frappe/frappe-bench/sites/assets
    name: sites
    subPath: frappe-sites/assets
```

That shape is valid for app-aware runtime-image Jobs. For generic
`site_setup.status`, Platform must use only the first mount, read-only, with
`subPath: frappe-sites`.

## Required Evidence From Failing Cluster

Before changing code again, capture the actual live manifests from the failing
cluster:

```bash
kubectl --kubeconfig "$MANAGER_KUBECONFIG" \
  -n lenscloud-runtime-eu get job bcmd-2026-00356-job -o yaml

kubectl --kubeconfig "$MANAGER_KUBECONFIG" \
  -n lenscloud-runtime-eu get pod \
  -l job-name=bcmd-2026-00356-job -o yaml

kubectl --kubeconfig "$MANAGER_KUBECONFIG" \
  -n lenscloud-runtime-eu get deploy \
  -l app.kubernetes.io/instance=eu-shared-bench-two -o yaml
```

If the Job has already been cleaned up, reproduce with a new
`site_setup.status` action and capture the Action Log manifest before cleanup
or from Platform's stored orchestration manifest.

Use the test VM reported for this incident:

```bash
ssh root@167.235.138.49
```

## Platform Fix Criteria

Platform must prove:

1. Generated `site_setup.status`, `oauth.status`, and other generic runner
   status-style Jobs never include `sites-assets`.
2. Generic runner status Jobs include the same `sites` PVC `subPath: frappe-sites`
   as the target Bench pod first mount.
3. App-aware runtime-image Jobs keep mirroring the Bench pod's sites/assets
   layout.
4. A stale generic runner digest denial is surfaced as admission/digest
   configuration, while a container startup failure is surfaced as a pod/runtime
   mount failure with the sanitized message from Kubernetes.
5. Failed `site_setup.status` marks the Site setup state `Failed` and stops
   automatic customer polling retries until the customer/operator explicitly
   retries after remediation.

## Infra Coordination

Infra SOP has been updated to make this mount split explicit.

The team's v16.14.1 cluster should not be judged only against the v16.14.3 dev
cluster. Compare the Bench deployment volume mounts directly. The version
difference is relevant only if the image filesystem shape makes a nested assets
mount fail earlier on v16.14.1.

## Acceptance

- A fresh `site_setup.status` against a new disposable Site on
  `167.235.138.49` starts the runner and returns `Succeeded` or a normal
  runner-level setup status.
- If it fails, the failure must be after runner start and must include a
  sanitized termination summary, not a containerd mountpoint error.
- If container startup fails again, the customer portal must show a terminal
  failed setup state and stop the never-ending `site_setup.status` loop.
