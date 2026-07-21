# Infra Follow-up — Customer Site Creation App Installation Exceeds Full Gate

Date: 2026-07-21
From: Platform
To: Infra
Status: Action required

## Live Result

Fresh Site `iron-monkey-0721113731.cloud.lmnaslens.com` correctly requested:

```yaml
spec:
  apps:
    - erpnext
    - brandkit
```

The FrappeSite resource was created at `2026-07-21T11:37:35Z` and its Ready condition transitioned at `2026-07-21T11:43:04Z`: 329 seconds. The browser failed the complete 300-second customer gate at canonical `route_pending` before setup or OAuth started.

Operator confirmation was later captured as `ORCH-2026-01142`. No separate `site_bootstrap.install_apps` Kubernetes Job was created.

## Required Infra Analysis

- Split the 329-second operator init Job into database creation, Frappe Site creation, ERPNext install, Brandkit install, migrations, and final reconciliation timings.
- Confirm image cache state for the operator init Pod, not only Platform-created command Pods.
- Determine whether default-app installation can be moved into a prepared Site/database template, snapshot, or another safe precomputed artifact.
- Identify work that can run concurrently without marking the Site Ready prematurely.
- Preserve `installedApps`, `failedApps`, `appInstallationStatus`, conditions, and the existing failure-message contract.
- Propose a realistic operator creation-to-Ready budget that leaves at least 120 seconds for setup and OAuth, or explicitly reject the current five-minute product target.

## Return Evidence

Return phase timestamps, proposed change, Infra commit range, and a fresh disposable proof under:

`docs/handoffs/platform/customer-site-creation-app-install-latency-infra-return-20260721.md`

