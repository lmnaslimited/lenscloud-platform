# Platform Handoff - Site Bootstrap App Install Failed - 2026-07-17

## Root Cause

Two request-shape issues caused the failed customer Site bootstrap.

First, the generated idempotency check is wrong for `bench list-apps` output.
Platform generated:

```bash
bench --site tharahub.cloud.lmnaslens.com list-apps | grep -qx erpnext
```

But `bench list-apps` prints app plus version columns:

```text
frappe  16.14.0 UNVERSIONED
erpnext 16.13.1 UNVERSIONED
```

Infra verified on the live Site:

```text
exact_erpnext_rc=1
first_column_erpnext_rc=0
exact_brandkit_rc=1
first_column_brandkit_rc=1
```

Use first-column matching instead:

```bash
bench --site "$SITE" list-apps | awk '{print $1}' | grep -Fxq "$APP"
```

Second, Platform selected a runtime image that does not contain every requested
app. The Job requested:

```text
apps: erpnext, brandkit
image: ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2
```

Infra verified that image contains only:

```text
erpnext
frappe
```

It does not contain `brandkit`.

Infra also verified the target Bench runtime is still:

```text
Bench: run-20260702-free-prod-bench
Runtime image: ghcr.io/lmnaslimited/lensdocker/lens-pure:v16.14.1
Runtime app dirs: erpnext, frappe
```

So `brandkit` must not be installed on `tharahub.cloud.lmnaslens.com` while
that Site is running on this Bench/runtime. Installing it would put the Site in
a state where the running Bench pods cannot import the app.

The failing command in the Platform flow was therefore the bootstrap sequence
at `install-app brandkit`. Infra did not execute `install-app brandkit` on the
customer Site because the target Bench runtime lacks `brandkit` and that
mutation would be unsafe.

Sanitized diagnostic output:

```text
STEP list-apps

frappe  16.14.0 UNVERSIONED
erpnext 16.13.1 UNVERSIONED

STEP exact grep erpnext
exact_grep_erpnext_rc=1
STEP first-column grep erpnext
first_column_grep_erpnext_rc=0
STEP install-app erpnext retry
App erpnext already installed
install_erpnext_rc=0
```

Classification:

```text
Primary: Platform request shape / Release Group image selection
Secondary: idempotency check bug in generated shell
Not observed: PVC/mount failure, namespace/RBAC admission failure, database outage
```

## Platform Request-Shape Decision

Platform must change the generated Job/script.

Required app-installed check:

```bash
app_is_installed() {
  bench --site "$SITE" list-apps | awk '{print $1}' | grep -Fxq "$1"
}
```

Required install loop shape:

```bash
set -euo pipefail

SITE="tharahub.cloud.lmnaslens.com"

for app in erpnext brandkit; do
  if app_is_installed "$app"; then
    echo "Skipping already installed app $app"
  else
    bench --site "$SITE" install-app "$app"
  fi
done
```

Required Release Group validation before Job creation:

- The app list must come from the Bench current Release Group/runtime, not only
  from a future or unrelated Release Group.
- Every requested app must be present in the selected runtime image inventory.
- The selected runtime image must match the Bench runtime app set.
- Do not request `brandkit` for `run-20260702-free-prod-bench` while it is on
  `lens-pure:v16.14.1` with only `frappe` and `erpnext`.

For first-time Site bootstrap on the existing Free Plan Bench, Platform should
request only apps supported by that Bench runtime. For the current Site this
means `erpnext` is already installed and `brandkit` must be skipped/deferred.

If Platform wants `brandkit` as a default app, it must first place the Site on a
Bench whose runtime image contains `brandkit`, or upgrade/roll the Bench to a
Release that contains `brandkit`, verify assets, and only then run
`site_app.install` for `brandkit`.

## RBAC/Logging Decision

Infra did not grant `pods/log` read to the Platform service account.

Reason: native Kubernetes RBAC cannot grant `pods/log` only for
Platform-labelled Bench Command pods. Granting `get pods/log` in the runtime
namespace would allow reading logs for unrelated runtime pods as well.

Replacement mechanism Platform should use:

- Write sanitized per-step failure details to `/dev/termination-log`.
- Capture the failing step name, exit code, and sanitized tail from stdout/stderr.
- Read the Pod termination message before cleanup.
- Continue avoiding full pod logs for customer-facing and orchestration output.

Recommended failure wrapper:

```bash
run_step() {
  step="$1"
  shift
  out="/tmp/${step}.out"
  if "$@" >"$out" 2>&1; then
    return 0
  fi
  rc=$?
  python3 - "$step" "$rc" "$out" > /dev/termination-log <<'PY'
import json, sys
step, rc, path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
text = open(path, "r", errors="replace").read().splitlines()[-40:]
print(json.dumps({
    "phase": "Failed",
    "summary": "Site bootstrap app install failed",
    "failed_step": step,
    "exit_code": rc,
    "error_excerpt": "\n".join(text)[-2000:],
    "redacted": True,
}))
PY
  exit "$rc"
}
```

Do not include Secret values, raw `site_config.json`, environment dumps,
kubeconfig material, tokens, private keys, or database passwords.

## Runtime Verification

Infra verification commands were run on the manager VM against:

```text
Namespace: lenscloud-runtime-eu
Site: tharahub.cloud.lmnaslens.com
Bench: run-20260702-free-prod-bench
```

Live Site app list after diagnostics:

```text
frappe  16.14.0 UNVERSIONED
erpnext 16.13.1 UNVERSIONED
```

`erpnext` is installed.

`brandkit` is not installed, intentionally. Infra did not install `brandkit`
because the current Bench runtime does not contain `brandkit`.

Selected image inventory diagnostic for:

```text
ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2
```

returned:

```text
erpnext
frappe
```

Target Bench runtime diagnostic returned:

```text
tag=v16.14.1
runtime app dirs: erpnext, frappe
```

## Cleanup Proof

Temporary diagnostic resources created by Infra:

```text
diag-site-bootstrap-20260717
diag-image-apps-20260717
```

Both were removed.

Cleanup verification:

```text
No resources found in lenscloud-runtime-eu namespace.
No resources found in lenscloud-runtime-eu namespace.
```

No Secret values were read or included.

## Platform Retry Instruction

Do not retry `retry_customer_site_provisioning("tharahub.cloud.lmnaslens.com")`
unchanged.

The current Site can be reused. It does not need to be recreated.

Recommended Platform recovery:

1. Fix the app-installed check to use first-column matching.
2. Recompute the bootstrap app list from the Site's actual Bench runtime
   Release Group.
3. For `run-20260702-free-prod-bench` on `lens-pure:v16.14.1`, do not include
   `brandkit`.
4. Mark/continue bootstrap based on the supported app set. `erpnext` is already
   installed.
5. Defer `brandkit` until the Bench is upgraded/rolled to a runtime image that
   contains `brandkit`, then install it through `site_app.install`.

The customer-facing setup can proceed once Platform no longer requires
`brandkit` for this Bench/runtime.
