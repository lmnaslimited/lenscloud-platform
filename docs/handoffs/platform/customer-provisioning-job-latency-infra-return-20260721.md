# Expected Infra Return — Customer Provisioning Job Latency

Date: 2026-07-21
From: Infra
To: Platform
Status: Awaiting Infra
Request: `docs/handoffs/infra/customer-provisioning-job-latency-under5-20260721.md`

## Infra Commit Range

Pending.

## Per-Command Timing Evidence

Pending. Include create/admission, scheduling, image pull, container start, command start/end, termination summary, Job terminal condition, and Platform-observable timestamps.

## Changes Delivered

Pending.

## Image Warmth Evidence

Pending for both the digest-pinned Release runtime and generic runner images.

## Completion Delivery Contract

Pending. State whether Platform should continue its two-second terminal polling, use Kubernetes watch, or consume another explicit acknowledgement. Include reconnection and missed-event behavior.

## Remaining Caveats

Pending.

## Platform Acceptance Actions

After Infra returns this document, Platform will:

1. verify the supplied timestamps against Platform request/action-log timestamps;
2. instrument Platform observation and cleanup durations separately;
3. publish the terminal canonical snapshot immediately after safe evidence capture rather than making the customer wait for nonessential cleanup;
4. adopt Kubernetes watch only if it preserves timeout, reconnect, and missed-event correctness;
5. run one fresh customer Site from submission to Ready with a single monotonic clock;
6. verify live socket delivery independently from fallback polling;
7. attach final evidence to `docs/stage-gates/site-provisioning-under-5min-20260720.md`.

