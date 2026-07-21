# Stage Gate: Customer Site Provisioning Under 5 Minutes

Date: 2026-07-20
Status: In progress — canonical flow implemented; first live acceptance exceeded budget
Canonical workitem: `Customer Site provisioning under 5 minutes`

## Problem

Fresh customer Site provisioning currently spends too much time in repeated status checks, frontend polling loops, duplicate command creation, and ambiguous failure recovery. The customer experience is unreliable because the UI can lag behind backend state, and the backend sometimes performs status probes that do not add value for a new Site.

Target: complete the normal fresh Site install flow in under 5 minutes from customer submission to usable Site, excluding external capacity outages.

## Target Flow

For a fresh Site with setup defaults already captured:

```text
1. Create Subscription/Site request
2. Reconcile FrappeSite
3. Wait for runtime/route readiness
4. Install bootstrap apps
5. Run setup.complete directly
6. Run one final setup.status verification
7. Configure OAuth directly
8. Run one final oauth.status verification
9. Mark Ready / Open Site
```

Avoid preflight status checks that do not change the decision for a fresh Site.

## Stage Budget

| Stage | Target |
| --- | ---: |
| Subscription + Site request | < 10s |
| FrappeSite reconcile accepted | < 20s |
| Runtime + route ready | 60-120s |
| Bootstrap app install | 60-120s |
| Setup complete + final setup status | 60-90s |
| OAuth configure + final status | 30-60s |
| Total | < 300s |

## Backend Stage Gate Contract

Platform backend owns the canonical progress state. The customer UI must not infer stage from many raw fields.

Recommended snapshot:

```json
{
  "site": "tharahub.cloud.lmnaslens.com",
  "stage": "bootstrap_installing",
  "stage_status": "running",
  "active_operation": "site_bootstrap.install_apps",
  "active_action_log": "ORCH-2026-00849",
  "can_retry": false,
  "can_continue": false,
  "message_id": null,
  "customer_message": "Installing default apps.",
  "operator_message": null,
  "updated_at": "2026-07-20T19:43:54Z"
}
```

Stage values:

- `requested`
- `runtime_reconciling`
- `route_pending`
- `bootstrap_installing`
- `setup_completing`
- `setup_verifying`
- `oauth_configuring`
- `oauth_verifying`
- `ready`
- `failed`
- `blocked_customer_input`
- `blocked_platform_action`
- `blocked_infra_action`

## Polling And Realtime

Use realtime as the primary UX update path and polling as fallback.

Platform must publish realtime events after every meaningful transition:

- Site request created
- Site reconcile accepted
- Site status sync changed runtime or route status
- Bench Command queued
- Bench Command running, if observable
- Bench Command succeeded
- Bench Command failed
- known message matched
- retryability changed
- Site marked ready

Use `frappe.publish_realtime` with a customer-scoped event, for example:

```python
frappe.publish_realtime(
    "lenscloud_site_progress",
    snapshot,
    user=customer_user,
    after_commit=True,
)
```

The UI must also call a read-only endpoint on load/refresh:

```text
get_customer_site_progress(site)
```

Fallback polling should be read-only and slower, for example every 20-30 seconds. Polling must not itself enqueue commands.

## Mutating vs Read-Only APIs

Separate these responsibilities:

- `get_customer_site_progress(site)`: read-only, fast, renders current truth.
- `advance_customer_site_provisioning(site, force=False)`: starts the next backend action only when no active command exists and the previous stage is complete.

The current pattern where customer polling can both inspect and mutate must be replaced for reliability.

## Fresh Site Optimizations

For a new customer-created Site:

- Skip initial `site_setup.status` if setup defaults are already available.
- Run `site_setup.complete` directly after bootstrap succeeds.
- Run one final `site_setup.status` only as verification.
- Skip initial `oauth.status`; run `oauth.configure` directly after setup is complete.
- Run one final `oauth.status` only as verification.
- If Release Group bootstrap app list is empty, mark bootstrap `Skipped` / effectively succeeded without launching a Job.
- Do not run Site Status Sync repeatedly after route is already Ready unless a runtime action is pending or a timeout threshold is reached.
- Never enqueue a duplicate Bench Command while the latest same-operation command is `Queued` or `Running`.

## Failure Handling

When any stage fails:

1. Capture evidence before cleanup.
2. Attach Integration Message ID and params if available.
3. Classify retryability and owner.
4. Publish realtime failure snapshot.
5. Stop automatic advancement.
6. Show customer-safe next action.

Customer retry must be enabled only when backend says retry is safe.

## Platform Role

Platform owns:

- customer-facing Site progress model
- read-only progress endpoint
- mutating advancement endpoint
- realtime publish calls
- UI subscription to realtime events
- stage budget measurement
- duplicate-command prevention
- setup/OAuth shortcut optimization
- action-log linkage and customer-safe rendering
- E2E tests for stage order and elapsed time

Platform must not:

- infer UI stage in Vue from many raw fields once canonical snapshots exist
- mutate provisioning from read-only polling
- advance to setup while bootstrap is queued/running
- advance to OAuth while setup is queued/running or failed

## Infra Role

Infra owns:

- runner/operator execution performance for scoped commands
- ensuring Job scheduling and image pull do not dominate the 5 minute target
- exposing enough status/condition detail for Platform to publish meaningful transitions
- message envelopes for failures as defined in the Integration Message POC
- guidance on whether `site_setup.complete` and `oauth.configure` can safely run directly for fresh Sites
- any operator-side improvement needed to emit running/completed transitions promptly

Infra must confirm expected runtime timings for:

- FrappeSite reconcile to Ready
- route readiness
- app-aware bootstrap Job execution
- generic runner status commands
- app-aware setup complete Job
- OAuth configure/status commands

## Test Plan

Minimum automated coverage:

- fresh Site stage order contains no skipped/incorrect stage
- no duplicate command creation for queued/running operations
- read-only progress endpoint never mutates state
- mutating advance endpoint starts only one next operation
- bootstrap queued/running prevents setup stage
- setup queued/running prevents OAuth stage
- failure returns message ID / retryability when available

Minimum live E2E coverage:

- create one fresh customer Site from portal
- capture timestamps for every stage transition
- prove total time under 5 minutes or classify the bottleneck by owner
- verify realtime updates reach UI without manual refresh
- verify browser refresh rehydrates same stage from read-only endpoint
- verify no duplicated Bench Commands in Orchestration Action Log

## Acceptance Criteria

- Normal fresh Free Plan Site reaches Ready in under 5 minutes in the test cluster when Infra capacity is healthy.
- Customer UI updates within 2 seconds of backend stage transition through realtime.
- Browser refresh shows the same stage as backend truth.
- No mutating command is triggered by read-only polling.
- Any failure is backed by a message ID, params, owner, retryability, and customer-safe message once the message POC is available.
- Platform/Infra can identify the stage responsible for any run exceeding 5 minutes.

## Open Questions

- Should Platform run `site_setup.complete` directly before an initial status check for every fresh Site, or only when setup defaults are complete and Release Group is known to require setup?
- Can Infra expose app-aware command `Running` transitions, or only Queued/Succeeded/Failed through Platform action logs?
- Should the under-5-minute target include OAuth final verification, or stop at first usable admin/SSO handoff?
- Should customer UI show elapsed time and current action log ID during beta testing?

## Implementation And Live Evidence — 2026-07-21

Implemented:

- canonical read-only `get_customer_site_progress(site)` endpoint
- one-stage-only `advance_customer_site_provisioning(site, force=False)` endpoint
- duplicate queued/running operation guard and strict bootstrap/setup/OAuth ordering
- direct setup and OAuth mutation followed by one verification each
- customer-scoped `lenscloud_site_progress` realtime publication with 30-second read-only polling fallback
- Vue rendering from the canonical backend snapshot, including refresh rehydration
- read-only membership authorization; the first live request exposed and fixed an unintended User-role-profile write

Live recovery run:

- Customer: `iron_monkey_private@example.com`
- Site: `iron-monkey-0721081416.cloud.lmnaslens.com`
- Subscription: `SUB-00007`
- Result: `ready`
- Trustworthy recovery elapsed: `492,885 ms` (`8m 12.885s`)
- Under five minutes: **No**
- Refresh: `bootstrap_installing` before and after reload
- Command order: `site_bootstrap.install_apps` → `site_setup.complete` → `site_setup.status` → `oauth.configure` → `oauth.status`
- Duplicate app-aware commands: none

Measured canonical transition intervals:

| Stage interval | Elapsed |
| --- | ---: |
| Resume to route ready/bootstrap start | 6.952s |
| Bootstrap install | 201.197s |
| Setup complete | 71.437s |
| Setup verification | 36.685s |
| OAuth configure | 41.781s |
| OAuth verification | 134.733s |
| Total recovery | 492.885s |

The original submission-to-ready duration is intentionally not reported: the browser used UTC while Frappe creation timestamps were rendered in the site timezone, producing an invalid negative comparison. The monotonic recovery duration above is valid and independently sufficient to fail the 300-second gate.

Evidence:

- `docs/evidence/customer-launch/provisioning-under5-20260721/iron-monkey-0721081416-recovery.json`
- `docs/evidence/customer-launch/provisioning-under5-20260721/iron-monkey-0721081416-recovery-final.png`

Gate disposition:

- Reliability/order/refresh behavior: passed for this run.
- Under-five-minute performance: failed.
- Realtime delivery within two seconds: backend scoping is unit-tested, but live socket latency was not isolated from the one-second evidence polling and remains unproven.
- Next bottleneck work: reduce Release-runtime bootstrap startup/execution and especially final OAuth verification latency, then run a new fresh customer journey with a single monotonic timer from submission.

## Infra Performance Return And Platform Retest Preparation — 2026-07-21

Infra commit `1697eae` delivered image prewarm and direct command timing evidence. Warm-image status/OAuth commands completed in approximately 10–14 seconds, and Job terminal state was observable within 1.443 seconds. Infra identified the separate 201-second post-ready bootstrap as avoidable duplication for default creation apps.

Platform now emits Release Group creation apps through `FrappeSite.spec.apps`, consumes operator app installation status, and skips the separate bootstrap Job only after explicit operator confirmation. Focused validation passed 36 tests. A new fresh customer run is required to determine the final gate result.

## Fresh Operator-Native Retest — 2026-07-21

Fresh Site `iron-monkey-0721113731.cloud.lmnaslens.com` requested `erpnext` and `brandkit` in `FrappeSite.spec.apps`. No separate post-ready bootstrap Job was created. The browser's monotonic five-minute assertion failed at canonical stage `route_pending`.

The FrappeSite resource took 329 seconds from creation to operator Ready, exceeding the entire gate by 29 seconds before setup or OAuth began. Recovery from the ready resource through route, setup, and OAuth took another 197.678 seconds. The resulting minimum uninterrupted estimate is 526.678 seconds.

Post-ready command durations remained above Infra's idempotent probe timings: setup complete 68.720s, setup verification 36.779s, OAuth configure 42.140s, and OAuth verification 36.907s.

The run found and fixed unchanged status-sync action-log noise, an invalid synthetic bootstrap action type, and missing failed-run harness persistence. Final Site state is Ready/Complete/Configured, but the under-five-minute gate remains failed.

Evidence: `docs/evidence/customer-launch/provisioning-under5-20260721/iron-monkey-0721113731-failed-gate.json`.
