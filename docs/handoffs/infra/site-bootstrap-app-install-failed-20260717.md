# Infra Handoff - Site Bootstrap App Install Failed - 2026-07-17

## Source Incident

`LC-E2E-20260717-001`

Platform/customer Free Plan E2E is blocked at Release Group default app install for the customer Site created by `nithu@gmail.com`.

Infra should return its response under:

```text
apps/lenscloud/docs/handoffs/platform/site-bootstrap-app-install-failed-20260717.md
```

## Current Live Platform State Checked Before Handoff

Checked from Platform on 2026-07-17 after the customer recreated the Site from the customer portal.

```text
Customer user: nithu@gmail.com
Customer: CUST003
Subscription: SUB-00004
Site: tharahub.cloud.lmnaslens.com
Bench: run-20260702-free-prod-bench
Namespace: lenscloud-runtime-eu
Site status: Ready
Provisioning status: Ready
Route status: Ready
Setup status: Failed
Setup error: Site bootstrap app install failed
OAuth status: Not Checked
```

Latest relevant orchestration logs:

```text
ORCH-2026-00455
  action_type: Bench Command
  operation: site_bootstrap.install_apps
  status: Failed
  message: App-aware command site_bootstrap.install_apps finished with phase Failed; cleanup removed 2 resource(s).
  error: phase: Failed; summary: Site bootstrap app install failed
  modified: 2026-07-17 13:06:25.862519

ORCH-2026-00452
  action_type: Bench Command
  operation: site_bootstrap.install_apps
  status: Failed
  message: App-aware command site_bootstrap.install_apps finished with phase Failed; cleanup removed 2 resource(s).
  error: phase: Failed; summary: Site bootstrap app install failed
  modified: 2026-07-17 13:05:54.230234

ORCH-2026-00454 / ORCH-2026-00451 / ORCH-2026-00449 / ORCH-2026-00447 / ORCH-2026-00445
  operation: status-sync
  status: Succeeded
  latest Ready message: FrappeSite runtime phase: Ready; route: Ready.

ORCH-2026-00453 / ORCH-2026-00450 / ORCH-2026-00448 / ORCH-2026-00446 / ORCH-2026-00444
  operation: inventory
  status: Succeeded
  latest inventory message: Runtime inventory collected for lenscloud-runtime-eu/tharahub without Secret values.
```

## Platform Request Shape

Platform creates an app-aware Bench Command Job for `site_bootstrap.install_apps`.

Observed request shape from the same flow:

```text
Command family: site_bootstrap
Command: site_bootstrap.install_apps
Action type: Bench Command
Target namespace: lenscloud-runtime-eu
Target Site: tharahub.cloud.lmnaslens.com
Release Group runtime image: ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2
Apps requested from Release Group, in sequence: erpnext, brandkit
frappe is intentionally not sent as an install app.
```

The generated script shape is:

```bash
set -euo pipefail
trap 'rc=$?; printf '''%s
''' '''{"phase":"Failed","summary":"Site bootstrap app install failed","apps":["erpnext","brandkit"],"site":"tharahub.cloud.lmnaslens.com","redacted":true}''' > /dev/termination-log; exit $rc' ERR
if bench --site tharahub.cloud.lmnaslens.com list-apps | grep -qx erpnext; then echo 'Skipping already installed app erpnext'; else bench --site tharahub.cloud.lmnaslens.com install-app erpnext; fi
if bench --site tharahub.cloud.lmnaslens.com list-apps | grep -qx brandkit; then echo 'Skipping already installed app brandkit'; else bench --site tharahub.cloud.lmnaslens.com install-app brandkit; fi
printf '%s
' '{"phase":"Succeeded","summary":"Site bootstrap app install completed","apps":["erpnext","brandkit"],"site":"tharahub.cloud.lmnaslens.com","redacted":true}' > /dev/termination-log
```

Platform validated the generated shell with `bash -n` after fixing an earlier trap quoting issue.

## What Platform Fixed Before This Handoff

Platform-side fixes already applied in the current worktree:

1. `site_bootstrap.install_apps` now logs as `Bench Command`, not invalid `Bench App Command`.
2. Platform runner digest now matches the infra admission policy for regular Bench Command runner jobs.
3. Customer timeline now has a visible `Installing default apps` step.
4. Customer context now returns `bootstrap_status` for Site rows.
5. Customer timeline no longer marks failed backend steps as done through visual animation.
6. Setup completion no longer proceeds after failed default app install.
7. App-aware bootstrap jobs use the 900s timeout path.
8. Failed bootstrap jobs write a redacted termination summary.
9. Platform attempted bounded pod-log capture, but the service account currently cannot read `pods/log`.

The remaining failure is no longer a UI/state sequencing issue; the runtime app install command exits non-zero inside the app-aware Job.

## Current Visibility Blocker

Platform cannot capture the actual failed pod log because Kubernetes denies `pods/log`:

```text
User "system:serviceaccount:lenscloud-platform-system:lenscloud-platform" cannot get resource "pods/log" in API group "" in the namespace "lenscloud-runtime-eu"
```

Platform now ignores that RBAC denial for customer-facing copy, so the portal shows the cleaner failure:

```text
Site bootstrap app install failed
```

But without either Infra-provided logs or a safe `pods/log` grant, Platform cannot identify whether the failure is:

- missing `erpnext` or `brandkit` in the Release Group runtime image;
- app dependency/order issue;
- Site already-partially-installed state;
- Bench/Site mount/path issue;
- database/migrate failure during `bench install-app`;
- another runtime/container issue.

## Ask For Infra

Please clear the blocker by doing one of the following, preferably both:

1. Grant the Platform service account least-privilege read of `pods/log` for Platform-labelled Bench Command pods in `lenscloud-runtime-eu`, or provide an equivalent safe log-return mechanism.
2. Reproduce/inspect `site_bootstrap.install_apps` for `tharahub.cloud.lmnaslens.com` and determine the exact app install failure.

When inspecting, use the exact app sequence and image from above:

```text
image: ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2
site: tharahub.cloud.lmnaslens.com
apps: erpnext, brandkit
namespace: lenscloud-runtime-eu
bench/sites PVC: run-20260702-free-prod-bench-sites
```

## Return Contract For Infra

Please return the handoff at:

```text
apps/lenscloud/docs/handoffs/platform/site-bootstrap-app-install-failed-20260717.md
```

Include these exact sections:

1. **Root cause**
   - Which command failed: `list-apps`, `install-app erpnext`, or `install-app brandkit`.
   - Sanitized stderr/stdout tail, with Secrets redacted.
   - Whether the failure is image content, dependency/order, Site state, PVC/mount, database, permission, or platform request shape.

2. **Platform request-shape decision**
   - State explicitly whether Platform should change the generated Job, image selection, app ordering, mounts, or script.
   - If Platform must change anything, provide the exact expected contract.

3. **RBAC/logging decision**
   - State whether Infra granted `pods/log` read for Platform-labelled Bench Command pods.
   - If not granted, state the replacement mechanism Platform should use to receive safe failure details.

4. **Runtime verification**
   - Exact command/job/manual verification used.
   - Result of `bench --site tharahub.cloud.lmnaslens.com list-apps` after the fix.
   - Whether `erpnext` and `brandkit` are installed.

5. **Cleanup proof**
   - Any diagnostic Job/Pod/ConfigMap names created.
   - Confirmation that temporary resources were removed.
   - Confirmation that no Secret values are included.

6. **Platform retry instruction**
   - Whether Platform should retry `retry_customer_site_provisioning("tharahub.cloud.lmnaslens.com")` unchanged.
   - Whether the current Site can be reused or must be recreated.

## Safety

- Do not expose kubeconfig, service account tokens, database passwords, OAuth secrets, private keys, or full unsanitized logs.
- Do not delete `tharahub.cloud.lmnaslens.com` unless the operator explicitly approves.
- Do not mutate `default/frappe-mariadb`.
- Keep any diagnostic changes scoped to Platform-labelled Bench Command resources or the named Site/Bench.
