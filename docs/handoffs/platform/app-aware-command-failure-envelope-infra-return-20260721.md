# Expected Infra Return: App-Aware Command Failure Envelope And Recovery

Date: 2026-07-21
Owner: Infra completes this return; Platform reviews and accepts it.
Status: Awaiting Infra return

## Source Contract

- Platform-to-Infra handoff:
  `docs/handoffs/infra/app-aware-command-failure-envelope-recovery-20260721.md`
- Stage gate:
  `docs/stage-gates/app-aware-command-failure-recovery-20260721.md`

## Infra Revision

- Base commit: Pending
- Return commit: Pending
- Changed files: Pending
- Runtime/release image digest used for proof: Pending

## Ownership Decision

Document whether Infra changed runtime/admission code or confirmed that the
Platform-generated Release-runtime script is the correct envelope source.
Describe the exact boundary and why it preserves current admission policy.

Status: Pending

## Controlled-Failure Contract

Document the allowlisted fault identifiers, authorization/environment gates,
typed signals, production denial, and cleanup/disable procedure.

Status: Pending

## Classification And Recovery Contract

| Command/condition | Supplied message ID | Safe params | State inspection before retry | Retry/idempotency rule |
| --- | --- | --- | --- | --- |
| `site_bootstrap.install_apps` controlled failure | Pending | Pending | Pending | Pending |
| `site_setup.complete` controlled failure | Pending | Pending | Pending | Pending |
| Target queue overload | Pending | Pending | Pending | Pending |
| Timeout/unknown fallback | Pending | Pending | Pending | Pending |

## Automated Verification

List exact commands and results for envelope schema, classification precedence,
redaction, digest-pinned Release-image admission, generic-runner denial,
mutable/wrong image denial, and unauthorized controlled-fault denial.

Status: Pending

## Live Bootstrap Failure And Recovery Evidence

Record the disposable Site and Bench, Release digest, failed Job/Pod and action
log, supplied message and params, installed-app state, successful retry,
duplicate-command check, and cleanup result.

Status: Pending

## Live Setup-Complete Failure And Recovery Evidence

Record proof bootstrap succeeded, the Release digest, failed Job/Pod and action
log, supplied message and params, setup state, successful retry and final
status action logs, duplicate-command check, and cleanup result.

Status: Pending

## Secret-Safety Evidence

Confirm summaries, action logs, and evidence contain no raw traceback, Redis
URL, password, token, kubeconfig, Site configuration, environment dump, or
Kubernetes Secret value.

Status: Pending

## Remaining Caveats

List every unproven classification or recovery behavior. Do not mark the return
Ready unless both live failure-and-recovery scenarios are complete; otherwise
mark it Blocked with the exact missing capability.

Status: Pending

## Platform Acceptance

- Contract accepted: Pending
- Platform parser/persistence changes required: Pending
- Customer provisioning recovery resumed: Pending
- Reviewer/date: Pending
