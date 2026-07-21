# Stage Gate: LensCloud Message Framework POC

Date: 2026-07-20
Status: Complete for generic runner POC; app-aware recovery split to 2026-07-21 stage gate
Canonical workitem: `LensCloud message framework POC`

## Problem

Platform currently receives and records many failures as free text, both from external integrations such as Infra/runner/operator responses and from Platform-owned APIs. Examples include `RUNNER_FAILED`, generic validation strings, and sanitized summaries. This makes customer retry guidance unreliable, makes Platform/Infra handoffs expensive, and prevents future AI-assisted recovery from using stable semantics.

LensCloud needs one generic message framework for all product and integration errors, warnings, success confirmations, and actionable information. Integration errors are the first POC because they are black-box boundaries and currently hurt the most, but Platform-owned APIs must follow the same contract instead of throwing ambiguous generic messages.

The current `Orchestration Action Log` is already the transaction record for orchestration work. For orchestration transactions it should become the message instance by referencing a stable message master entry and storing transaction-specific parameter values.

## Direction

Adopt SAP-style message handling across LensCloud.

Every meaningful success, warning, or failure should have a stable message ID plus structured parameter values. This applies to Platform-owned APIs as well as Infra/runner/operator responses. Platform may still sanitize defensively, but neither UI nor operators should be forced to infer the message class from raw stderr, pod logs, arbitrary summaries, or ad hoc exception text.

For orchestration flows, `Orchestration Action Log` is the message instance. A separate message-instance DocType is not required for the POC because existing links, UI, incidents, and SOPs already revolve around `ORCH-*` records. If a single orchestration transaction later needs multiple messages, add an `Orchestration Action Message` child table rather than a disconnected transaction DocType.

## POC Scope

Start with the customer Site provisioning path, covering both Platform-owned orchestration decisions and Infra/runner/operator integration responses:

- `site_bootstrap.install_apps`
- `site_setup.status`
- `site_setup.complete`
- `oauth.status`
- `oauth.configure`
- runner digest mismatch
- runner mount/PVC failures
- queue overload / background job saturation

Do not roll this to every Platform API or integration surface until the POC proves the model. The framework is generic; the first rollout slice is intentionally narrow.

## Message Master Shape

Create a Platform-owned message master model, tentatively `LensCloud Message` or simply `Message`. Avoid naming it `Integration Message`, because Platform-native APIs must use the same framework.

Minimum fields:

- `message_id`: stable external ID, for example `LC-INFRA-RUNNER-0007`
- `message_type`: Success, Info, Warning, Error, Critical
- `source`: Platform API, Platform UI, Infra, Operator, Runner, Kubernetes, Customer
- `destination`: Customer, Platform Operator, Infra Operator, AI Agent
- `action_type`: Orchestration Action Log action type, when applicable
- `operation`: command/operation such as `site_setup.status`
- `short_text`: concise operator-facing text
- `message_template`: text with placeholders, for example `Bench command {command} failed with reason {reason}`
- `long_text`: fuller explanation
- `cause`: known or likely cause
- `customer_resolution`: customer-safe next step
- `platform_resolution`: Platform operator next step
- `infra_resolution`: Infra/operator next step
- `retryability`: Retryable, Retry After Delay, Retry After Platform Action, Retry After Infra Action, Customer Action Required, Not Retryable
- `owner`: Customer, Platform, Infra
- `sanitization_level`: Customer Safe, Operator Safe, Restricted
- `status`: Draft, Active, Retired
- `version` or `revision`: catalog evolution without losing historical meaning

## Message Instance Shape

For orchestration work, reuse and extend `Orchestration Action Log`; it is the message instance. Do not create a separate message-instance DocType in the POC.

Minimum fields to add to Orchestration Action Log:

- `message_id`
- `message_type`
- `message_params_json`
- `normalized_signature`
- `matched_by`: Infra Supplied, Platform Exact Match, Platform Pattern Match, Fallback Unknown
- `match_confidence`
- `customer_message`
- `operator_message`
- `resolution_owner`
- `retryability`
- existing resource links such as `site`, `bench`, `cluster`, `region`, `database_server` remain the transaction context

Existing `message` and `error` fields can remain as rendered text/fallbacks, but `message_id` and `message_params_json` become the primary identity.

For non-orchestration Platform API calls, start by returning the same message envelope from the API response. A later pass can decide whether those should create audit/message transaction rows outside Orchestration Action Log.

## Message Envelope Contract

For the POC, every scoped Platform API failure and every Infra/runner/operator response for the scoped operations must return or be converted into a message envelope.

Required envelope:

```json
{
  "message_id": "LC-INFRA-RUNNER-0007",
  "message_type": "Error",
  "source": "bench-command-runner",
  "destination": "platform",
  "params": {
    "command": "site_setup.status",
    "reason": "RUNNER_FAILED",
    "exit_code": 1
  },
  "safe_summary": "Site setup status check failed.",
  "details_ref": null
}
```

Contract rules:

- No failed scoped Platform API response should reach UI without `message_id`.
- No failed integration response should cross the Infra-to-Platform boundary without `message_id`.
- If Platform cannot classify its own error, it must return a known fallback ID such as `LC-PLATFORM-UNKNOWN-0001` with structured params.
- If Infra cannot classify the error, it must return a known fallback ID such as `LC-INFRA-UNKNOWN-0001` with structured params.
- Params must be JSON, not string interpolation.
- Params must avoid secrets at the source. Platform will sanitize again defensively.
- Volatile values such as site, pod, job, timestamp, and command IDs should be transaction params, not part of the message ID.
- Infra-owned messages must document source, meaning, params, and resolution owner.

## Platform Role

Platform owns:

- generic Message Master DocTypes and permissions
- message lookup and formatting
- message instance persistence
- customer-safe vs operator-safe rendering
- retryability and owner mapping
- Orchestration Action Log linkage
- UI display in Platform console and customer portal
- fallback mapping while Platform API and Infra POC responses are not complete
- publish/realtime event payloads that include message IDs

Platform must not:

- throw generic customer/operator-facing exceptions in scoped flows without a message ID
- rely on raw stderr as the primary error identity
- expose restricted params to customers
- auto-activate AI-generated message definitions

## Infra Role

Executable Infra implementation handoff: [LensCloud message envelope runner contract](../handoffs/infra/lenscloud-message-envelope-runner-contract-20260720.md).

Infra owns for Infra-sourced messages:

- stable message IDs for operator/runner/runtime failures
- structured params at the source
- runner termination/result envelope changes
- operator condition/message envelope changes where applicable
- message documentation for Platform consumption
- ensuring errors like digest mismatch, mount contract failure, queue overload, image pull, scheduling, and permission failure are emitted with known IDs

Infra must return the exact message IDs and params needed for Platform to classify retryability without parsing raw text. Platform-owned API errors must be classified by Platform using the same message catalog rules.

## KEDB / Known Error Relationship

The message master is not merely a KEDB row. It is the stable message catalog.

Known Error records can later sit on top of message IDs:

- same `message_id`
- constrained by normalized params
- resolution history
- successful recovery evidence
- automation eligibility

AI agents should use message ID + params + related action logs, not raw unclassified logs, as their primary recovery context.

## POC Acceptance Criteria

- Platform has generic Message Master representation and Orchestration Action Log message-instance fields.
- Scoped Platform API failures and runner failures attach `message_id` and params.
- Customer portal receives customer-safe message and retryability from backend, not frontend inference.
- Platform console shows operator message, params, related action log, and resolution owner.
- At least five current failures are represented:
  - queue overload
  - stale runner digest
  - mount/PVC contract failure
  - app install failure
  - generic runner failed / unknown
- Unknown message fallback creates a Platform/Infra follow-up, not a silent ambiguous error.
- No secrets appear in customer-visible or operator-safe message params.

## Rollout After POC

After Site provisioning POC passes:

1. Platform-native customer portal APIs in the launch/subscription/site setup path
2. Bench update / upgrade actions
3. route checks and asset readiness
4. Database Server actions
5. backup/restore runner families
6. deletion/finalizer workflows
7. capability install flows
8. broader Platform console document/action APIs

## Open Questions

- Should message master records be fixtures or editable master data in production?
- Which message ID namespace is owned by Platform vs Infra? Recommended examples: `LC-PLATFORM-*`, `LC-INFRA-*`, `LC-RUNNER-*`, `LC-OPERATOR-*`.
- Should Infra publish a machine-readable message catalog file for import?
- Should retired message IDs remain valid for historical logs forever? Recommended: yes.
