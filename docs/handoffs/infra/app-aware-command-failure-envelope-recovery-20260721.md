# Infra Handoff: App-Aware Command Failure Envelope And Recovery Proof

Date: 2026-07-21
Owner: Infra owns Release-runtime admission and runtime-boundary failure signals. Platform owns command orchestration, the LensCloud message catalog, action-log persistence, and customer provisioning recovery.
Status: Ready for Infra implementation and return

## Objective

Provide a production-safe way to classify and prove failures from app-aware
commands running in the digest-pinned Release Group runtime image:

- `site_bootstrap.install_apps`
- `site_setup.complete`

The proof must not run either command through the generic Bench Command runner
and must not weaken the existing admission policy.

## Current Platform Path

Platform currently resolves the immutable image from `Bench.current_release`,
creates the app-aware Kubernetes Job, mounts the Bench sites PVC, executes a
Platform-generated script inside the Release runtime image, reads sanitized
JSON from `/dev/termination-log`, passes `summary.message` to the action log,
and cleans terminal resources after retaining evidence.

The relevant implementation is `lenscloud/api/bench_command.py`, especially
`site_setup_complete_script`, `app_install_script`, `run_app_aware_job`,
`run_site_setup_complete`, and `install_site_bootstrap_apps`.

The missing acceptance evidence is a controlled live failure and recovery for
each scoped command. Generic-runner tests do not satisfy this gate.

## Required Infra Work

1. Confirm the exact admission contract for both commands when their image is
   the digest-pinned current Release image.
2. Provide an explicitly gated controlled-failure mechanism usable only for
   acceptance testing. It must not accept arbitrary commands, secrets, raw
   stderr, or a mutable image tag.
3. Prefer typed failure signals or bounded error codes at the runtime boundary.
   Platform must not parse unbounded traceback when a typed signal exists.
4. Confirm retry/idempotency guarantees for interrupted app installation,
   partially completed setup, and target-runtime `QueueOverloaded`.
5. Confirm the termination summary remains readable before cleanup.
6. Prove the controlled failure does not weaken generic-runner or image-digest
   admission rules.

If no Infra code change is required because Platform-generated scripts are the
correct envelope source, the return must say so explicitly and provide the
controlled fault contract and live evidence Infra owns.

## Canonical Failure Envelope

```json
{
  "phase": "Failed",
  "command": "site_bootstrap.install_apps",
  "message": {
    "message_id": "LC-INFRA-BOOTSTRAP-0001",
    "message_type": "Error",
    "source": "Release Runtime",
    "destination": "Platform",
    "params": {
      "operation": "site_bootstrap.install_apps",
      "reason": "APP_INSTALL_FAILED",
      "app": "example_app",
      "exit_code": 1
    },
    "safe_summary": "A required Site application could not be installed.",
    "details_ref": null
  },
  "redacted": true
}
```

The same nesting used by the generic runner contract is mandatory. Platform's
current parser already consumes `summary.message`.

## Required Classifications

| Condition | Message ID | Minimum safe params | Retry expectation |
| --- | --- | --- | --- |
| Bootstrap application install failed | `LC-INFRA-BOOTSTRAP-0001` | `operation`, `reason`, `app`, optional `exit_code` | Inspect installed-app state first |
| Target Frappe queue overloaded | `LC-INFRA-QUEUE-0001` | `operation`, `reason`, optional bounded `queue` | Retry after target capacity is healthy |
| App-aware command timed out | `LC-INFRA-TIMEOUT-0001` | `operation`, `reason`, `timeout_seconds` | Inspect state first |
| Release image rejected or mismatched | `LC-INFRA-RUNNER-0001` | `operation`, `reason`, safe requested/admitted digests | Retry after Infra correction |
| Storage or mount contract failed | `LC-INFRA-STORAGE-0001` | `operation`, `reason`, `mount_kind` | Retry after Infra correction |
| No safer classification is available | `LC-INFRA-UNKNOWN-0001` | `operation`, bounded `reason` | No blind customer retry |

Do not emit `LC-PLATFORM-QUEUE-0001`; it is reserved for Platform worker queue
saturation before a runtime Job is admitted.

## Controlled Acceptance Scenarios

### Bootstrap failure and recovery

1. Use a disposable test Site and valid digest-pinned Release runtime image.
2. Trigger the narrow controlled app-install failure.
3. Retain a failed action log with `LC-INFRA-BOOTSTRAP-0001` and
   `matched_by = Infra Supplied`.
4. Inspect installed-app state, remove the fault, and retry once.
5. Prove success without duplicate Jobs or reinstalling installed apps.

### Setup-complete failure and recovery

1. Use a disposable Site whose bootstrap stage succeeded.
2. Trigger a narrow controlled setup failure or target queue overload.
3. Retain the supplied message ID and params on the failed action log.
4. Inspect setup state, remove the fault, and retry once.
5. Prove final setup status is complete with no duplicate Jobs.

Record exact Job, Pod, image digest, command annotation, action log, and cleanup
result for both scenarios. Evidence must be secret-safe.

## Safety Constraints

- Keep immutable Release-image admission mandatory.
- Do not expose arbitrary fault commands through a customer API.
- Gate test faults by exact environment, role, and allowlisted identifier.
- Do not retain raw traceback, Redis URLs, credentials, tokens, kubeconfigs,
  Site configuration, environment dumps, or Secret values.
- Capture the termination summary before resource cleanup.
- Do not reuse a message ID for different semantics.

## Expected Return Handoff

Infra must complete:

`apps/lenscloud/docs/handoffs/platform/app-aware-command-failure-envelope-infra-return-20260721.md`

The expected return template already exists there. Infra should replace its
pending sections with exact commit, contract, tests, and live evidence.

## Platform Work After Return

Platform will finalize envelope changes and tests, enforce retry policy in
`advance_customer_site_provisioning`, expose recovery through
`get_customer_site_progress`, prove no duplicate advancement, and run a fresh
customer provisioning E2E.
