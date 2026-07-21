# Stage Gate: App-Aware Command Failure Recovery And Customer Provisioning

Date: 2026-07-21
Status: In Progress; Infra amendment a23258a integrated, disposable-Site live recovery proof pending

## Ownership And Sequence

1. Platform defines the message, recovery, controlled-test, and evidence contract.
2. Infra supplies Release-runtime/admission support and live evidence through
   docs/handoffs/infra/app-aware-command-failure-envelope-recovery-20260721.md.
3. Infra completes
   docs/handoffs/platform/app-aware-command-failure-envelope-infra-return-20260721.md.
4. Platform accepts the return, completes customer provisioning recovery
   integration, and runs acceptance.

Current next action: Platform runs and retains both controlled failure/recovery
scenarios on a disposable customer Site, then continues that Site into the
under-five-minute provisioning gate. Infra's invocation contract is complete;
the transactional Platform integration passed 84 focused tests.

## Purpose

Extend the proven LensCloud message framework to app-aware commands without
moving those commands onto the generic Bench Command runner.

Scoped commands:

- `site_bootstrap.install_apps`
- `site_setup.complete`
- later `site_app.install` where it participates in customer fulfillment

These commands must continue using the immutable, digest-pinned Release Group
runtime image. The generic runner image remains denied by admission for these
operations.

## Required Work

1. Define the canonical nested failure envelope emitted by the Release-runtime
   scripts for app-aware commands.
2. Classify bootstrap app failures, setup queue overload, timeout, partial
   completion, retry-safe/idempotent recovery, and unknown fallback.
3. Retain sanitized failure evidence before cleanup.
4. Persist the supplied message ID and params on `Orchestration Action Log`.
5. Stop customer provisioning advancement on a terminal app-aware failure.
6. Expose backend-owned retryability, resolution owner, and customer-safe next
   action through `get_customer_site_progress`.
7. Permit `advance_customer_site_provisioning(..., force=True)` only where the
   catalog and recovery policy say retry is safe.
8. Publish/re-hydrate the same canonical stage after retry and browser refresh.

## Recovery Rules

- Never enqueue setup while bootstrap is queued, running, or failed.
- Never enqueue OAuth while setup completion or final verification is pending
  or failed.
- A retry must not create a duplicate queued/running command.
- App installation and setup completion must be idempotent or return a message
  requiring Platform/Infra action instead of blind retry.
- Queue overload must distinguish Platform worker saturation from target
  runtime queue saturation.
- Unknown failures must use a known fallback ID and retain safe params.

## Evidence Required

- Controlled Release-runtime failure for `site_bootstrap.install_apps`.
- Controlled Release-runtime failure for `site_setup.complete`.
- Persisted Platform action logs with `matched_by = Infra Supplied` or an
  explicitly documented Release-runtime supplied classification.
- Successful recovery/retry for each controlled failure.
- No duplicate commands during failure and recovery.
- Customer progress snapshots before failure, after failure, during retry, and
  after success.
- Job/ConfigMap/Pod cleanup evidence with no secret leakage.
- One fresh customer provisioning E2E continuing into the under-five-minute
  stage gate.

## Acceptance

- App-aware failures have stable message IDs and safe structured params.
- Customer progress stops at the correct backend stage.
- Retry is enabled only by backend policy.
- Recovery resumes from the failed stage without repeating successful stages.
- Bootstrap, setup, and OAuth ordering remains strict.
- The normal fresh Site path remains under the five-minute target when Infra
  capacity is healthy.
