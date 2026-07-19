# Infra Handoff: `site_setup.complete` Runner Failed After Runner Sync Recovery

Date: 2026-07-19
Owner: Platform captured the live customer-side failure; Infra owns runner internals/log visibility and should return a sanitized diagnosis.

## Context

Infra fixed the two blockers from `docs/handoffs/infra/bench-upgrade-assets-runner-sync-followup-20260719.md`:

- Platform can now sync the Cluster Bench Command runner contract ConfigMap.
- Existing upgraded Bench assets recover and current generated CSS/JS URLs return HTTP 200.

Platform retested the customer portal retry path for:

```text
Site: brandkite2e0717.cloud.lmnaslens.com
Customer user: brandkit.e2e.20260717@gmail.com
Bench: run-20260702-free-prod-bench
Namespace: lenscloud-runtime-eu
Cluster: lenscloud-eu-dev
```

## What Passed

Cluster runner sync now succeeds:

```text
bench_command_runner_contract_status = Synced
bench_command_runner_image = ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:0ba81c0f4031d452eab71a463a562d5f07ace308ae87967725dd807e00c97570
```

Generated asset checks from fresh HTML now pass:

```text
tharahub.cloud.lmnaslens.com
  CSS: /assets/frappe/dist/css/website.bundle.JTHFRTK2.css -> 200
  JS:  /assets/frappe/dist/js/frappe-web.bundle.Y6GAOBLB.js -> 200

brandkite2e0717.cloud.lmnaslens.com
  CSS: /assets/frappe/dist/css/website.bundle.JTHFRTK2.css -> 200
  JS:  /assets/frappe/dist/js/frappe-web.bundle.Y6GAOBLB.js -> 200
```

Generic setup commands now use the synced Cluster runner image:

```text
ORCH-2026-00564 site_setup.status  Succeeded
image: ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:0ba81c0f4031d452eab71a463a562d5f07ace308ae87967725dd807e00c97570
message: Setup wizard: Pending

ORCH-2026-00568 site_setup.complete Failed
image: ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:0ba81c0f4031d452eab71a463a562d5f07ace308ae87967725dd807e00c97570
```

App-aware commands still use the Release runtime image, not the generic runner:

```text
ORCH-2026-00545 site_bootstrap.install_apps Succeeded
image: ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:92196b4fb5c016e006c0bddc7ecffd6ba4ad8ce23c6ad290e81840fea0f6bca0

ORCH-2026-00523 bench.update Succeeded
image: ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:92196b4fb5c016e006c0bddc7ecffd6ba4ad8ce23c6ad290e81840fea0f6bca0
```

## Current Blocker

`site_setup.complete` is admitted and starts with the correct synced runner digest, but the runner exits failed:

```text
Action log: ORCH-2026-00568
Operation: site_setup.complete
Status: Failed
Message: Bench Command site_setup.complete finished with phase Failed; cleanup removed 3 resource(s). Summary: phase: Failed; code: RUNNER_FAILED; summary: site setup command failed with sanitized error.
```

Platform also retained one debug run before cleanup:

```text
Action log: ORCH-2026-00565
Job: bcmd-2026-00565-job
Pod: bcmd-2026-00565-job-c28zm
Request ConfigMap: bcmd-2026-00565-request
```

The pod terminated with the same sanitized envelope:

```json
{"changed":false,"code":"RUNNER_FAILED","command":"site_setup.complete","commandId":"BCMD-2026-00565","phase":"Failed","redacted":true,"summary":"site setup command failed with sanitized error","target":{"bench":"run-20260702-free-prod-bench","namespace":"lenscloud-runtime-eu","site":"brandkite2e0717.cloud.lmnaslens.com"}}
```

Platform could not read pod logs with the restricted service account:

```text
Kubernetes API 403: pods "bcmd-2026-00565-job-c28zm" is forbidden:
User "system:serviceaccount:lenscloud-platform-system:lenscloud-platform"
cannot get resource "pods/log" in API group "" in namespace "lenscloud-runtime-eu"
```

Platform cleaned the retained debug resources after capturing pod status:

```text
jobs/lenscloud-runtime-eu/bcmd-2026-00565-job
configmaps/lenscloud-runtime-eu/bcmd-2026-00565-request
pods/lenscloud-runtime-eu/bcmd-2026-00565-job-c28zm
```

## Request Payload Shape

The failed `site_setup.complete` request carried non-secret setup defaults:

```json
{
  "language": "English",
  "country": "India",
  "timezone": "Asia/Kolkata",
  "currency": "INR",
  "company_name": "Brandkit E2E",
  "company_abbr": "BKE",
  "chart_of_accounts": "Standard",
  "fiscal_year_start_date": "2026-04-01",
  "email": "brandkit.e2e.20260717@gmail.com",
  "full_name": "Brandkit E2E"
}
```

The current Site remains customer-visible failed, not looping:

```text
setup_status = Failed
setup_error = phase: Failed; code: RUNNER_FAILED; summary: site setup command failed with sanitized error
```

Platform implemented this state fix in `lenscloud.api.orchestration.orchestrate_customer_site_setup` so a failed runner result immediately becomes a customer-safe failed state.

## Infra Ask

Please diagnose the runner-side reason for `site_setup.complete` failure on `brandkite2e0717.cloud.lmnaslens.com`.

Return under:

```text
docs/handoffs/platform/site-setup-complete-runner-failed-20260719.md
```

Please include:

1. Infra commit revision tested.
2. Whether the above payload is valid for the current runner contract.
3. The sanitized root cause from the target Site/runner logs, with no secrets.
4. Whether this is:
   - a Platform payload/defaults issue;
   - a runner idempotency issue after a prior partial setup;
   - an ERPNext/setup-wizard behavior issue;
   - or a release/runtime image issue.
5. If Platform must change payload fields, provide the exact accepted field/value contract.
6. If the runner should surface a safer diagnostic in the termination summary, provide the new sanitized result schema.
7. Whether Platform should be granted read-only `pods/log` for Platform-labelled Bench Command pods, or whether Infra will remain the log-inspection boundary.
8. The exact retest sequence Platform should run after the fix, including whether to reuse `brandkite2e0717.cloud.lmnaslens.com` or create a fresh customer Site.

## Platform Retest After Infra Returns

Platform will rerun:

1. Cluster runner contract sync for `lenscloud-eu-dev`.
2. Customer portal retry as `brandkit.e2e.20260717@gmail.com` for `brandkite2e0717.cloud.lmnaslens.com`, or a fresh customer Site if Infra recommends that.
3. `site_setup.status` -> `site_setup.complete` -> final `site_setup.status`.
4. OAuth status/configure if setup completes.
5. Fresh generated CSS/JS route checks.
6. Action-log manifest checks proving generic commands use the Cluster runner digest and app-aware commands use the Release runtime digest.
