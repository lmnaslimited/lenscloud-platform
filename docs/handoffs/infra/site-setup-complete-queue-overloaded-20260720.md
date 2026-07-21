# Infra Handoff - `site_setup.complete` Queue Overloaded - 2026-07-20

## Incident

Tracker row: `LC-E2E-20260720-003`.

Customer/Site under test:

```text
User: nithu@gmail.com
Customer: CUST003
Subscription: SUB-00006
Site: tharahub.cloud.lmnaslens.com
Bench: run-20260702-free-prod-bench
Cluster: lenscloud-eu-dev
Namespace: lenscloud-runtime-eu
```

## What Platform Verified

The customer provisioning stage loop and generic `site_setup.status` deadlock are not the current hard blocker:

- `site_setup.status` retries complete and return `Setup wizard: Pending`.
- Bootstrap apps are already installed: latest bootstrap action status is `Succeeded`.
- The customer progress endpoint now advances one major stage at a time.
- Failed setup remains terminal until explicit retry.

Recent action sequence:

```text
ORCH-2026-00653  site_setup.status    Succeeded  Setup wizard: Pending
ORCH-2026-00656  site_setup.complete  Failed
```

`ORCH-2026-00656` sanitized root cause:

```text
frappe.exceptions.QueueOverloaded: Too many queued background jobs (750). Please retry after some time.
```

The failure happens inside target Site/Frappe setup-complete, after the app-aware runtime job starts. Platform also updated the app-aware failure capture so future action logs preserve parseable sanitized `error_excerpt` instead of truncated JSON.

## Infra/Runtime Ask

Please inspect the target Bench queue/worker health for `run-20260702-free-prod-bench` and determine why the target Site sees 750 queued jobs during first-time setup.

Check at minimum:

1. Redis queue length / queue keys for the Bench.
2. Whether short/default/long workers are running and consuming jobs.
3. Whether stale jobs accumulated from repeated failed setup runs.
4. Whether the app-aware setup-complete Job can reach the same Redis queue endpoints as the Bench workers.
5. Whether any worker crashloop, queue config, or scheduler setting is preventing drain.
6. Whether it is safe to drain/clear stale jobs for this test Bench, and if so perform the safe cleanup.

Do not clear queues blindly if they may contain unrelated tenant work; provide the exact queue names/counts and safety basis first.

## Return To Platform

Place the response under:

```text
apps/lenscloud/docs/handoffs/platform/site-setup-complete-queue-overloaded-20260720.md
```

Return these exact details:

- Bench and namespace inspected.
- Queue names and counts before remediation.
- Worker deployments/pods inspected and their status.
- Any Redis/worker/runtime errors found.
- Whether queues were drained, cleared, or left unchanged, with reason.
- Queue names and counts after remediation.
- Whether Platform should retry `site_setup.complete` for `tharahub.cloud.lmnaslens.com`.
- If Platform must change anything else before retry, provide the exact contract change.

## Acceptance

After remediation, Platform will run explicit customer retry for `tharahub.cloud.lmnaslens.com` and expects:

1. `site_setup.status` returns Pending/Required or Complete normally.
2. `site_setup.complete` succeeds without `QueueOverloaded`.
3. Final `site_setup.status` returns `Setup wizard: Complete`.
4. OAuth status/configure can proceed.
5. Customer portal shows terminal Ready or a clear terminal failure, with no endless polling loop.
