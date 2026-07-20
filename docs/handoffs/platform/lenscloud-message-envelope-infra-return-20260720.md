# Infra Return Handoff: LensCloud Message Envelope

Date: 2026-07-20  
Status: Awaiting Infra implementation and evidence

## Source Request

Infra implementation contract:

`apps/lenscloud/docs/handoffs/infra/lenscloud-message-envelope-runner-contract-20260720.md`

Infra must replace the placeholders in this document after implementing and
verifying the message-envelope contract. Do not mark this handoff complete
without committed Infra evidence.

## Infra Revision

- Infra commit: `PENDING`
- Runner image: `PENDING`
- Immutable runner digest: `PENDING` or `UNCHANGED`
- Machine-readable Infra message catalog: `PENDING`
- Canonical Infra evidence document: `PENDING`

## Canonical Envelope

Selected shape: `PENDING` (`nested message object` or `top-level fields`)

Provide one complete sanitized JSON result:

```json
{
  "status": "PENDING"
}
```

Confirm:

- all scoped commands use the same nesting;
- `message_id` is mandatory for every failure;
- `params` is always a JSON object;
- the envelope remains available after temporary resource cleanup;
- no secrets or raw logs are present.

## Final Infra Message Catalog

Replace this section with the implemented catalog.

| Message ID | Meaning | Source | Required params | Resolution owner | Retryability | Revision |
| --- | --- | --- | --- | --- | --- | --- |
| `PENDING` |  |  |  |  |  |  |

Document any mapping changes from these provisional Platform IDs:

- `LC-INFRA-RUNNER-0001`
- `LC-INFRA-RUNNER-0002`
- `LC-INFRA-STORAGE-0001`
- `LC-INFRA-UNKNOWN-0001`

Infra must not emit Platform-owned `LC-PLATFORM-*` IDs.

## Scoped Operations

Report implementation status and evidence for:

| Operation | Envelope implemented | Tests | Controlled/live evidence | Remaining gap |
| --- | --- | --- | --- | --- |
| `site_bootstrap.install_apps` | Pending |  |  |  |
| `site_setup.status` | Pending |  |  |  |
| `site_setup.complete` | Pending |  |  |  |
| `oauth.status` | Pending |  |  |  |
| `oauth.configure` | Pending |  |  |  |

## Automated Validation

Provide exact commands and results proving:

1. every failed scoped operation returns a message ID and JSON params;
2. known failures map to stable IDs;
3. unknown failures map to `LC-INFRA-UNKNOWN-0001`;
4. every operation uses the same envelope nesting;
5. configured secret canaries do not appear in params or summaries;
6. successful commands are not classified as failures;
7. existing phase/code/display consumers remain compatible.

```text
PENDING
```

## Controlled Or Live Evidence

Provide sanitized evidence for:

- a known runner failure;
- a storage/mount or admission/digest failure;
- the unknown fallback;
- a successful scoped command;
- cleanup with the result envelope retained.

```text
PENDING
```

## Security And Cleanup Evidence

- Secret-canary test: `PENDING`
- Unsafe/raw error suppression: `PENDING`
- Temporary Job cleanup: `PENDING`
- Temporary ConfigMap cleanup: `PENDING`
- Temporary Pod cleanup: `PENDING`
- Remaining resources: `PENDING`

Do not include kubeconfigs, tokens, passwords, OAuth client secrets, Kubernetes
Secret values, private keys, raw pod logs, raw `site_config.json`, or full
environment dumps.

## Backward Compatibility

- Existing result fields retained: `PENDING`
- Existing Platform parser impact: `PENDING`
- Required Platform changes: `PENDING`
- Legacy fallback period: `PENDING`

## Platform Retest Instructions

Provide exact test target and sequence:

1. `PENDING`
2. `PENDING`
3. `PENDING`

The sequence must prove that `Orchestration Action Log` records:

- the Infra-supplied message ID;
- exact safe params JSON;
- `matched_by = Infra Supplied`;
- resolution owner and retryability;
- customer-safe and operator-safe messages.

## Remaining Infra Gaps

```text
PENDING
```

## Copy/Paste-Ready Platform Implementation Prompt

Infra must replace the block below with the final prompt.

```text
Work inside /workspace/frappe-bench/apps/lenscloud.

Read:
- AGENTS.md
- docs/handoffs/infra/lenscloud-message-envelope-runner-contract-20260720.md
- docs/handoffs/platform/lenscloud-message-envelope-infra-return-20260720.md
- docs/stage-gates/integration-message-model-poc-20260720.md

Infra implementation is pending. Do not integrate until this return handoff
contains an Infra commit, canonical envelope, catalog, tests, and evidence.
```

