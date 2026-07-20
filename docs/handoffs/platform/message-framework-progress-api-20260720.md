# LensCloud Message Framework And Provisioning API Handoff

Date: 2026-07-20

## Implemented

- Generic `LensCloud Message` master with seven seeded Site-provisioning failure definitions.
- `Orchestration Action Log` is the message instance; it now retains message ID/type/source/destination, safe params JSON, normalized signature, matching evidence, customer/operator rendering, owner, and retryability.
- Failed orchestration actions resolve exact/pattern/fallback messages. Unclassified runner failures use `LC-INFRA-UNKNOWN-0001`; unclassified Platform failures use `LC-PLATFORM-UNKNOWN-0001`.
- `lenscloud.api.provisioning_progress.get_customer_site_progress(site)` is read-only and returns the canonical stage, active operation/action log, message, retryability, and owner.
- `lenscloud.api.provisioning_progress.advance_customer_site_provisioning(site, force=False)` advances at most one command and refuses to enqueue while any scoped command is queued/running.
- The new advancement path runs setup completion and OAuth configuration directly after their prerequisites, leaving status commands as final verification.

## Validation

- `bench --site dev.localhost migrate`
- `lenscloud.api.test_provisioning_progress`: 7 passed
- `lenscloud.api.test_customer_site_setup`: 24 passed
- `lenscloud.api.test_bench_command`: 42 passed

## Remaining

- Infra must emit its own `message_id` plus safe params JSON envelope; Platform currently pattern-matches retained evidence and uses the known Infra fallback. Executable handoff: [Infra message envelope runner contract](../infra/lenscloud-message-envelope-runner-contract-20260720.md).
- The customer frontend still uses the legacy retry/polling payload. Wire it to the read-only endpoint and explicit advancement action in the next pass.
- Realtime publishing and live under-five-minute timing evidence remain later passes.
- Broader Platform API message coverage remains outside this POC.
