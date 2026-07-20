# Platform Handoff - `site_setup.complete` Queue Overloaded - 2026-07-20

## Incident

Tracker row: `LC-E2E-20260720-003`.

Source Platform-to-Infra handoff:

```text
apps/lenscloud/docs/handoffs/infra/site-setup-complete-queue-overloaded-20260720.md
```

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

## Result

Infra found and remediated the live runtime blocker.

`site_setup.complete` failed because Frappe refused to enqueue more work while
the Bench queues were overloaded:

```text
frappe.exceptions.QueueOverloaded: Too many queued background jobs (750).
```

The root cause was not the app-aware setup-complete Job image or Redis
reachability. The target Bench had scheduler activity and Redis queue state,
but all worker deployments were desired at zero replicas.

## Runtime Inspected

```text
Namespace: lenscloud-runtime-eu
Bench CR: FrappeBench/run-20260702-free-prod-bench
Redis queue pod: run-20260702-free-prod-bench-redis-queue-0
```

Before remediation:

```text
run-20260702-free-prod-bench-worker-default  0/0
run-20260702-free-prod-bench-worker-short    0/0
run-20260702-free-prod-bench-worker-long     0/0
```

FrappeBench CR desired state before remediation:

```text
worker-default.staticReplicas = 0
worker-short.staticReplicas   = 0
worker-long.staticReplicas    = 0
```

Queue counts before remediation:

```text
rq:queue:home-frappe-frappe-bench:default = 766
rq:queue:home-frappe-frappe-bench:long    = 204
rq:queue:home-frappe-frappe-bench:short   = absent
rq:workers                                = absent before workers started
```

Sample queued job IDs included stale E2E scheduled jobs for:

```text
run-20260702-free-site.cloud.lmnaslens.com
run-20260706-cua-134515.cloud.lmnaslens.com
tara-communo-hub.cloud.lmnaslens.com
tharahub.cloud.lmnaslens.com
brandkite2e0717.cloud.lmnaslens.com
```

No Redis failed/started registries were present for the scoped queues.

## Remediation Performed

Live patched the FrappeBench CR:

```text
scheduler.staticReplicas      = 1
worker-default.staticReplicas = 1
worker-short.staticReplicas   = 1
worker-long.staticReplicas    = 1
```

Worker rollout succeeded:

```text
run-20260702-free-prod-bench-scheduler        1/1
run-20260702-free-prod-bench-worker-default   1/1
run-20260702-free-prod-bench-worker-short     1/1
run-20260702-free-prod-bench-worker-long      1/1
```

Worker logs showed jobs being consumed successfully. No worker crashloop,
Redis error, or network error was observed.

Queues were not deleted or flushed. They were left to drain naturally because
workers consumed them successfully and the Bench is shared by multiple E2E
Sites.

Queue counts after remediation:

```text
rq:queue:home-frappe-frappe-bench:default = 0
rq:queue:home-frappe-frappe-bench:long    = 0
```

## Source Fix

Platform manifest generation was also fixed so future Bench reconciles do not
restore zero workers.

Changed:

```text
lenscloud/api/orchestration.py
lenscloud/lenscloud/doctype/database_server/test_database_server.py
```

New generated `FrappeBench.spec.componentAutoscaling` defaults:

```text
scheduler.staticReplicas      = 1
worker-default.staticReplicas = 1
worker-short.staticReplicas   = 1
worker-long.staticReplicas    = 1
```

## Platform Retry Guidance

Platform may retry setup for:

```text
tharahub.cloud.lmnaslens.com
```

Expected sequence:

```text
site_setup.status    -> Succeeded, Setup wizard Pending or Complete
site_setup.complete  -> Succeeded, no QueueOverloaded
site_setup.status    -> Succeeded, Setup wizard Complete
oauth.status/configure can proceed
```

Before retrying after any Platform deploy/reconcile, verify the Bench still has
workers:

```bash
kubectl --kubeconfig "$MANAGER_KUBECONFIG" \
  -n lenscloud-runtime-eu get deploy \
  run-20260702-free-prod-bench-worker-default \
  run-20260702-free-prod-bench-worker-short \
  run-20260702-free-prod-bench-worker-long
```

Expected:

```text
1/1 for each worker deployment
```

## Follow-Up Needed

Platform should add an operator-facing action in a later pass to inspect a
Site's failed Bench Commands and their retained sanitized manifest/summary.

Platform should also add a controlled cleanup action for Platform-owned
terminal Bench Command Jobs before planned upgrades. That action must delete
only Platform-labelled terminal Job/ConfigMap/Pod resources and must not clear
Frappe Redis queues. Redis queue cleanup remains an Infra/runtime operation
unless a separate tenant-safe contract is designed.

## Acceptance

Close `LC-E2E-20260720-003` after Platform retry proves:

1. `site_setup.complete` no longer fails with `QueueOverloaded`.
2. Final `site_setup.status` returns setup complete.
3. OAuth can proceed.
4. Customer portal reaches Ready or a clear terminal failure.
