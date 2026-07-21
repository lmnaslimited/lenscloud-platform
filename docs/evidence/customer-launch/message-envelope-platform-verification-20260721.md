# LensCloud Message Envelope Platform Verification

Date: 2026-07-21

## Infra Source Verified

Platform inspected Infra commit `603b894` over base `5de2908` after refreshing
the adjacent repository refs.

Verified Infra artifacts:

- `bench-command-runner/message_catalog.v1.json`
- `bench-command-runner/runner.py`
- `bench-command-runner/test_message_envelope.py`
- `docs/lenscloud-message-envelope-evidence-20260720.md`
- `docs/handoffs/platform/lenscloud-message-envelope-infra-return-20260720.md`

The canonical failure result uses a nested `message` object. Infra retains the
existing top-level phase/code/summary/details/display contract.

## Platform Integration

Platform now:

- recognizes all eight Infra v1 message IDs;
- prefers a known nested Infra message over legacy text/pattern matching;
- stores the defensively sanitized Infra params JSON;
- records `matched_by = Infra Supplied` and confidence `1`;
- records source, destination, type, safe summary, details reference,
  resolution owner, and retryability;
- retains Platform legacy matching when no known Infra envelope is supplied;
- accepts the same nested envelope from an app-aware termination summary when
  that runtime path implements it;
- does not reroute app-aware commands through the generic runner.

## Automated Evidence

Passed:

```text
lenscloud.api.test_infra_message_envelope   5
lenscloud.api.test_message_framework        1
lenscloud.api.test_provisioning_progress    7
lenscloud.api.test_customer_site_setup     24
lenscloud.api.test_bench_command           42
Total                                      79
```

The new action-log integration test proves a nested
`LC-INFRA-STORAGE-0001` result overrides legacy `RUNNER_FAILED`, retains the
exact safe params, and records `matched_by = Infra Supplied`.

Migration passed and seeded these active Infra IDs:

- `LC-INFRA-RUNNER-0001`
- `LC-INFRA-RUNNER-0002`
- `LC-INFRA-STORAGE-0001`
- `LC-INFRA-UNKNOWN-0001`
- `LC-INFRA-QUEUE-0001`
- `LC-INFRA-BOOTSTRAP-0001`
- `LC-INFRA-TIMEOUT-0001`
- `LC-INFRA-COMMAND-0001`

## Live Compatibility Evidence

Platform synced Cluster `lenscloud-eu-dev` to:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:3b71912830d3dac1465a7e3cfa03dd64c76b17826fd7614a6801e4c539813cf5
```

Read-only live command:

```text
Action log: ORCH-2026-00872
Command: site_setup.status
Site: tharahub.cloud.lmnaslens.com
Result: Succeeded
Display: Setup wizard: Complete
Failure message: absent, as required for success
Cleanup: Job, ConfigMap, and terminal Pod removed
```

This proves the admitted INF-028 runner remains compatible with Platform's
success/display parser and cleanup path.

## Live Failure Capture Evidence

Controlled temporary Site target: message-proof-20260721.cloud.lmnaslens.com. The target had no runtime Site path and was deleted after the proof.

Persisted action log:



An idempotent cleanup verification found no remaining bcmd-2026-00873 Job, ConfigMap, or terminal Pod. The temporary Platform Site record was deleted; the ORCH evidence remains.

## App-Aware Boundary Decision

The following live generic-runner envelope tests remain intentionally
deferred:

- `site_setup.complete`
- `site_bootstrap.install_apps`

This is not a Platform blocker or a reason to weaken admission. Both commands
are app-aware and must continue using the immutable, digest-pinned Release
Group runtime image. Platform's app-aware result path will persist a canonical
nested message if that Release-runtime termination summary supplies one.

Live failure proof for these operations belongs in a future Release-runtime
runner pass, not the generic Bench Command runner.

## Remaining Acceptance

- Generic-runner end-to-end supplied-envelope capture is complete.
- Continue with docs/stage-gates/app-aware-command-failure-recovery-20260721.md.
- Add Release-runtime failure and recovery evidence for app-aware commands without weakening admission.
- Continue the customer provisioning under-five-minute pass after app-aware recovery is proven.
