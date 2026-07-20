# Platform Handoff - Customer Provisioning Stage Boundary Relapse - 2026-07-20

## Incident

Tracker row: `LC-E2E-20260720-001`.

Reported by: Arun during customer portal testing.

Customer/site under observation:

```text
User: nithu
Site: tharahub.cloud.lmnaslens.com
```

## Symptom

The customer portal spinner stayed on `Preparing workspace` while backend
orchestration logs showed later stages had completed. After a long wait the UI
jumped straight to `Checking setup status`.

This is the same customer experience class as `LC-E2E-20260709-010`, but the
2026-07-20 relapse is backend-driven: the retry endpoint again allowed a single
poll request to cross a runtime/route stage boundary and then continue into
setup/OAuth orchestration before returning.

## Root Cause

`retry_customer_site_provisioning` performed:

1. runtime inspect;
2. site status and route sync;
3. if the route was ready, setup/bootstrap/OAuth orchestration in the same
   request.

When the route became ready during step 2, the request did not return the
fresh `route_pending`/`setup_checking` snapshot. The browser stayed on the old
visual stage until the long request ended, then received a payload that had
already moved deeper into setup.

## Fix Implemented

Files changed:

```text
lenscloud/api/orchestration.py
lenscloud/api/test_customer_site_setup.py
docs/incidents/e2e-incident-tracker.md
```

`retry_customer_site_provisioning` now records the initial customer progress
state before runtime inspection. After status/route sync, if progress advanced
past the runtime gate from `started` or `route_pending`, it returns immediately.
Setup/bootstrap/OAuth work waits for the next poll.

Platform also now treats successful `site_bootstrap.install_apps` as its own
visible stage boundary: after bootstrap apps are installed, the request returns
before running `site_setup.status`. Terminal setup failures remain failed until
the customer/operator sends an explicit retry; background/status polling does
not reset `setup_status=Failed` back to Pending.

This restores the intended stage cadence:

```text
poll N     -> workspace / route progress snapshot
poll N + 1 -> setup/bootstrap status work
poll N + 2 -> setup completion work if required
poll N + 3 -> setup final status
poll N + 4 -> OAuth status/configure
```

The existing frontend visual cursor remains useful, but it should not be asked
to hide a backend request that has already run multiple lifecycle stages.

## Live Runtime Evidence Checked

Read-only manager VM inspection was possible for Kubernetes runtime state, but
not for Platform DB `Orchestration Action Log` rows. The manager has
`/root/lenscloud-infra` only; there is no Platform bench checkout or Platform
pod in `lenscloud-platform-system`.

Runtime evidence for `tharahub.cloud.lmnaslens.com`:

```text
Namespace: lenscloud-runtime-eu
Pod: tharahub-init-c99hl
Age at inspection: 43m
Phase: Completed
```

The init pod log showed:

```text
Creating Frappe site: tharahub.cloud.lmnaslens.com
No apps specified for installation
Only frappe framework will be installed
Site tharahub.cloud.lmnaslens.com created successfully!
Site initialization complete!
Running post-execution hook: clearing cache to ensure static assets load from new image...
Cache cleared successfully.
```

This confirms the backend workspace creation stage completed while the customer
portal report showed the visual spinner stuck earlier.

## Regression Test

Added helper coverage:

```text
customer_progress_advanced_past_runtime_gate("started", "route_pending") == true
customer_progress_advanced_past_runtime_gate("route_pending", "setup_checking") == true
customer_progress_advanced_past_runtime_gate("setup_checking", "setup_running") == false
customer_progress_advanced_past_runtime_gate("started", "failed") == false
bootstrap success returns before setup status polling
setup failure does not reset without explicit force retry
```

## Required Platform Verification

Run:

```bash
bench --site dev.localhost run-tests --module lenscloud.api.test_customer_site_setup
```

Then retest the customer portal:

1. Login as the `nithu` customer user.
2. Open progress for `tharahub.cloud.lmnaslens.com`, or create a fresh
   disposable nithu Site if that Site is already complete.
3. Trigger `retry_customer_site_provisioning`.
4. Confirm each poll visibly advances at most one major stage:
   `Preparing workspace`, `Connecting HTTPS`, `Installing default apps`,
   `Checking setup status`, `Setting site defaults`, `Platform access`,
   `Ready to open`.
5. Confirm the frontend does not continue polling after `provisioning=ready`
   or a terminal failure.
6. Compare orchestration logs with the customer UI timestamp sequence. The UI
   may lag by the visual cursor delay, but it must not stay on an old stage
   while one HTTP request is doing multiple backend stages.

## Acceptance

- `LC-E2E-20260720-001` can close only after a customer retest shows stage
  progression and no long poll-induced jump.
- If the UI still sticks despite this backend boundary, inspect
  `CustomerPlansPage.vue` polling lifecycle next: `progressActive`,
  `polling`, `startProgressPolling`, and `advanceVisualProvisioningIndex`.
