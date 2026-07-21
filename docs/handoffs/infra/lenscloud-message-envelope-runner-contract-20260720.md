# Infra Handoff: LensCloud Message Envelope For Runner And Operator Failures

Date: 2026-07-20  
Owner: Infra owns failure classification at the runner/operator/runtime boundary. Platform owns the generic LensCloud message catalog, persistence, rendering, and customer progress API.

## Work Location And Boundary

Work inside the `lenscloud-infra` repository. Treat this document as the Platform-to-Infra contract.

Infra may change:

- Bench Command runner result/termination envelopes;
- operator/runner failure classification;
- Infra-owned message catalog documentation or machine-readable catalog;
- Infra tests and evidence needed to prove the contract.

Infra must not implement the Platform `LensCloud Message` DocType, customer progress API, customer UI, or `Orchestration Action Log`. Those remain in `apps/lenscloud`.

Reference Platform documents:

- `apps/lenscloud/docs/stage-gates/integration-message-model-poc-20260720.md`
- `apps/lenscloud/docs/stage-gates/site-provisioning-under-5min-20260720.md`
- `apps/lenscloud/docs/handoffs/platform/message-framework-progress-api-20260720.md`
- `apps/lenscloud/lenscloud/api/messages.py`
- `apps/lenscloud/lenscloud/api/provisioning_progress.py`

## Objective

Every failed scoped command crossing the Infra/runner/operator boundary must return a stable Infra-owned `message_id` plus secret-safe structured `params`.

Platform must not need to infer failure semantics from raw stderr, pod logs, arbitrary summaries, or strings such as `RUNNER_FAILED`.

Platform currently pattern-matches legacy summaries as a temporary compatibility layer. An Infra-supplied known message ID must become the primary identity and must take precedence over Platform pattern matching.

## POC Operations

Implement and verify the message envelope for failures from:

- `site_bootstrap.install_apps`
- `site_setup.status`
- `site_setup.complete`
- `oauth.status`
- `oauth.configure`

The first classifications must cover:

- queue overload/background-job saturation;
- stale, rejected, or mismatched runner image digest;
- Bench sites PVC/mount/subPath contract failure;
- bootstrap/default app installation failure;
- generic runner failure when no safer specific classification is available;
- unknown Infra failure fallback;
- command timeout;
- unsupported command, if it can cross this boundary for a scoped operation.

Do not broaden this pass to every Infra command family.

## Required Failure Envelope

Return this logical shape in the sanitized runner termination/result summary:

```json
{
  "phase": "Failed",
  "code": "RUNNER_FAILED",
  "command": "site_setup.status",
  "commandId": "BCMD-2026-00852",
  "message": {
    "message_id": "LC-INFRA-RUNNER-0002",
    "message_type": "Error",
    "source": "Runner",
    "destination": "Platform",
    "params": {
      "operation": "site_setup.status",
      "reason": "RUNNER_FAILED",
      "exit_code": 1
    },
    "safe_summary": "Site setup status check failed.",
    "details_ref": null
  },
  "redacted": true
}
```

If the existing result parser requires the envelope at the top level, Infra may return:

```json
{
  "phase": "Failed",
  "code": "RUNNER_FAILED",
  "command": "site_setup.status",
  "commandId": "BCMD-2026-00852",
  "message_id": "LC-INFRA-RUNNER-0002",
  "message_type": "Error",
  "source": "Runner",
  "destination": "Platform",
  "params": {
    "operation": "site_setup.status",
    "reason": "RUNNER_FAILED",
    "exit_code": 1
  },
  "safe_summary": "Site setup status check failed.",
  "details_ref": null,
  "redacted": true
}
```

Infra must select one canonical shape and document it in the return handoff. Platform will adapt its parser to that exact returned shape. Do not emit different nesting by command.

## Contract Rules

- `message_id` is mandatory for every failed scoped operation.
- `params` is a JSON object, never an interpolated string.
- `message_id` describes stable semantics. Site, Bench, Job, Pod, timestamps, command IDs, image digests, and exit codes belong in params.
- Params must be safe at the source and must not include secret values.
- `safe_summary` must be concise and operator-safe; it is not the message identity.
- Existing `phase`, `code`, `command`, `commandId`, `redacted`, target, and safe display fields may remain for compatibility.
- Platform must be able to parse the envelope from the termination message after the Job/Pod has been cleaned up.
- Infra must preserve a known fallback instead of returning an unclassified failure.
- Raw stderr, tracebacks, pod logs, `site_config.json`, environment dumps, Redis credentials, OAuth secrets, tokens, kubeconfigs, private keys, and Kubernetes Secret values must never enter the envelope.
- Infra-owned message IDs must remain valid for historical action logs after later catalog revisions.

## Initial Message IDs

Platform has provisional POC definitions for:

| Message ID | Meaning | Resolution owner | Retryability |
| --- | --- | --- | --- |
| `LC-INFRA-RUNNER-0001` | Runner image digest rejected, stale, or not admitted | Infra | Retry After Infra Action |
| `LC-INFRA-RUNNER-0002` | Generic runner failure with no safer specific classification | Infra | Retry After Infra Action |
| `LC-INFRA-STORAGE-0001` | Bench sites PVC/mount/subPath contract failure | Infra | Retry After Infra Action |
| `LC-INFRA-UNKNOWN-0001` | Unknown Infra/runner/operator failure | Infra | Retry After Infra Action |

Infra must either adopt these IDs or return a proposed replacement mapping without reusing an ID for different semantics.

Infra should propose additional stable IDs for:

- Infra/runtime queue overload if ownership is Infra rather than Platform;
- timeout;
- command unsupported;
- operator scheduling/image-pull/admission failures encountered in this POC.

Platform retains these Platform-owned IDs and Infra must not emit them:

- `LC-PLATFORM-QUEUE-0001`
- `LC-PLATFORM-BOOTSTRAP-0001`
- `LC-PLATFORM-UNKNOWN-0001`

If a queue overload occurs inside the target Site/runtime and Infra can classify it at source, propose an `LC-INFRA-*` ID. `LC-PLATFORM-QUEUE-0001` is reserved for Platform/Frappe worker queue saturation.

## Required Params By Classification

Use only available, safe values:

| Classification | Required params |
| --- | --- |
| Runner digest rejected | `operation`, `reason`; `requested_image_digest` and `admitted_image_digest` only if non-secret and useful |
| Storage/mount failure | `operation`, `reason`, `mount_kind`; optional PVC name because it is operator-safe, not customer-facing |
| Queue overload | `operation`, `reason`; optional safe `queue` and `queued_count` |
| Bootstrap/app install failure | `operation`, `reason`; optional non-secret app name and exit code |
| Generic runner failure | `operation`, `reason`; optional exit code |
| Timeout | `operation`, `reason`, `timeout_seconds` |
| Unsupported command | `operation`, `reason` |
| Unknown Infra failure | `operation`, `reason` using a bounded safe reason, never raw stderr |

Platform will defensively sanitize again and will exclude volatile identifiers from normalized signatures.

## Classification Precedence

Infra should classify from most specific to least specific:

1. explicit typed exception/result from the command implementation;
2. known runner contract error;
3. known Kubernetes/operator condition;
4. safe exact error-code mapping;
5. known Infra fallback `LC-INFRA-UNKNOWN-0001`.

Do not use free-text regex parsing when the runner already has a typed exception or exit/result code.

## Machine-Readable Catalog

Return either:

- a versioned JSON/YAML Infra message catalog committed in `lenscloud-infra`; or
- a documented Python/Go/TypeScript constant if that is the runner’s established pattern.

Each Infra message definition must include:

- message ID;
- message type;
- source;
- meaning;
- allowed/required params;
- resolution owner;
- retryability;
- safe summary/template;
- revision/status;
- operations that may emit it.

Do not require Platform to scrape prose to import or compare message definitions.

## Tests And Evidence

Automated contract tests must prove:

1. every failed scoped operation returns `message_id` and a JSON-object `params`;
2. each known failure maps to the expected stable ID;
3. an unknown error maps to `LC-INFRA-UNKNOWN-0001`;
4. volatile params do not change the stable message ID;
5. params and summaries contain no configured secret canaries;
6. all commands use the same envelope nesting;
7. existing phase/code/display parsing remains backward compatible;
8. a successful command is not incorrectly classified as a failure.

Live or controlled integration evidence must cover at least:

- one known runner failure envelope;
- one known storage/mount or admission/digest envelope;
- one unknown fallback envelope;
- one successful scoped command proving the normal result contract still works;
- cleanup proof showing Platform can retain the envelope after temporary resources are removed.

Do not create a production incident merely to exercise a failure. A controlled test fixture/dry-run admission rejection is acceptable where safer.

## Acceptance

This handoff is complete when:

- Infra has one canonical, versioned failure-envelope shape;
- all failed POC operations emit a stable message ID and safe params;
- known cases do not collapse to `RUNNER_FAILED`;
- unknown cases use `LC-INFRA-UNKNOWN-0001`;
- Infra supplies a machine-readable catalog and tests;
- no secrets appear in envelopes or evidence;
- Platform can parse, attach, and display an Infra-supplied message without regex classification;
- Infra provides exact retest instructions and a return handoff.

## Expected Return Handoff

Return the Platform-facing implementation handoff at:

```text
apps/lenscloud/docs/handoffs/platform/lenscloud-message-envelope-infra-return-20260720.md
```

Also retain the canonical Infra implementation evidence in the `lenscloud-infra` repository and link it from the Platform-facing return.

The return handoff must contain:

1. Infra commit revision.
2. Runner image and immutable digest, if changed.
3. Canonical envelope nesting decision with one complete sanitized JSON example.
4. Final Infra message-ID catalog and any mapping changes from the provisional IDs.
5. Machine-readable catalog path.
6. Exact required/optional params for every returned ID.
7. Automated test commands and results.
8. Positive and negative security evidence.
9. Controlled/live evidence with command IDs and sanitized results.
10. Cleanup evidence.
11. Backward-compatibility impact on existing Platform parsing.
12. Exact Platform code changes required, if any.
13. Exact Platform retest sequence.
14. Remaining classifications deferred beyond the POC.

End the return handoff with a copy/paste-ready Platform implementation prompt. The prompt must direct Platform to:

- read the returned canonical envelope and catalog;
- update `lenscloud.api.messages` parsing without removing fallback compatibility prematurely;
- attach Infra-supplied IDs and params to `Orchestration Action Log`;
- run message/provisioning/Bench Command tests;
- run the controlled Site provisioning retest;
- record action-log evidence proving `matched_by = Infra Supplied`;
- update the stage gate and workitem only after evidence passes.

## Platform Retest After Infra Returns

Platform will:

1. inspect the Infra commit, catalog, runner digest, and evidence;
2. update the result parser for the canonical envelope shape;
3. retain legacy pattern matching only as a migration fallback;
4. run the message framework, provisioning progress, customer setup, and Bench Command suites;
5. execute controlled `site_setup.status`, `site_setup.complete`, and OAuth progression;
6. verify the related `Orchestration Action Log` stores:
   - Infra message ID;
   - exact safe params JSON;
   - `matched_by = Infra Supplied`;
   - resolution owner and retryability;
   - customer-safe and operator-safe rendering;
7. verify unknown controlled failures use `LC-INFRA-UNKNOWN-0001`;
8. verify successful provisioning still advances one stage at a time without duplicate commands;
9. update the stage-gate evidence and resume the under-five-minute pass.
