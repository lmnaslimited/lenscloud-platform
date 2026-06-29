# Infra Handoff: Bench Command Production Runner/API - 2026-06-27

## Context

Platform has completed the INF-010 consumer integration for the Bench Command Job/API contract.

Verified Platform evidence:

- Platform evidence: `apps/lenscloud/docs/evidence/bench-command/bench-command-platform-evidence-20260625.md`
- Platform action logs:
  - `ORCH-2026-00135`: pre-firewall Kubernetes API reachability failure
  - `ORCH-2026-00136`: unsupported-command behavior
  - `ORCH-2026-00137`: successful live `bench_test.status`
- Infra evidence: `lenscloud-infra/docs/bench-command-job-evidence-20260625.md`
- Infra handoff: `lenscloud-infra/docs/platform-bench-command-handoff.md`
- Infra revision verified by Platform: `dcd94d8`

Platform now needs Infra/operator support for production command execution beyond the harmless `bench_test.status` verification stub.

## Prompt For Infra Agent

Work inside `lenscloud-infra`.

Start from Infra revision `dcd94d8` or newer. Read:

1. `docs/infra-workitems.md`
2. `docs/platform-bench-command-handoff.md`
3. `docs/bench-command-job-evidence-20260625.md`
4. This handoff prompt copied into the Infra task context
5. Platform evidence summary in the Context section above

Create/update the canonical Infra backlog before implementation. Add a dated workitem for the production Bench Command runner/API, with date created, status, and date completed when finished.

Goal:

Build the production-safe Bench Command runner/API for real Site Control operations. Preserve the existing INF-010 Job/ConfigMap contract and admission guardrails. Platform must continue to use the Python Kubernetes API only and must not need `kubectl`.

Required command families:

- `backup.create`
- `backup.status`
- `restore.preview`
- `restore.execute`
- `restore.status`
- `maintenance_mode.enable`
- `maintenance_mode.disable`
- `maintenance_mode.status`
- `developer_mode.enable`
- `developer_mode.disable`
- `developer_mode.status`
- `site_config.set`
- `site_config.unset`
- `site_config.get`
- `cors.allowlist.update`
- `cors.allowlist.get`
- `bench_test.trigger`
- `bench_test.status`
- `latp.trigger`
- `latp.status`

Implement safely:

- Execute commands only in the approved target Bench/Site context.
- Keep namespace scope restricted to approved runtime namespaces.
- Preserve `default/frappe-mariadb` and all cluster infrastructure.
- Do not mount Kubernetes Secrets into arbitrary jobs unless the runner contract explicitly owns a safe mechanism.
- Do not allow pod logs, Secret listing, kubeconfig content, DB passwords, private keys, raw backup contents, or full environment dumps to be returned.
- Return only sanitized termination summaries matching the handoff contract.
- Include stable error codes such as `COMMAND_UNSUPPORTED`, `COMMAND_NOT_ALLOWED`, `INVALID_ARGUMENTS`, `TARGET_NOT_FOUND`, `TARGET_MISMATCH`, `NAMESPACE_NOT_APPROVED`, `ADMISSION_DENIED`, `RBAC_DENIED`, `TIMEOUT`, `RUNNER_FAILED`, and `SECRET_REDACTION_VIOLATION`.
- Keep unsupported commands truthful until each production command is implemented and verified.

Validation required:

- Positive live proof for every implemented command.
- Negative proof for invalid command, invalid target, wrong namespace, Secret access, pod log access, unsafe Job shape, unlabelled Job, and default namespace mutation.
- Cleanup proof for every temporary Job, ConfigMap, and runner artifact.
- Protected baseline proof that `MariaDB/default/frappe-mariadb` remains Ready/Running.
- Evidence that sanitized summaries contain no credentials, Secret values, private keys, kubeconfig content, pod logs, raw backup contents, or full environment dumps.

Return to Platform:

- Infra commit hash.
- Updated `docs/infra-workitems.md`.
- Production runner/API contract changes, if any.
- Dated live evidence document.
- Exact request/response examples for each supported command.
- Supported/unsupported command matrix.
- Cleanup proof.
- Remaining runner/API gaps.
- A Platform handoff prompt telling the Platform agent exactly which commands can now be enabled in UI/policy enforcement and which must remain `Unsupported`.

## Platform Follow-Up After Infra Handoff

Platform will:

- update `apps/lenscloud/docs/platform-workitems.md`;
- update Site Control Profile command availability;
- add typed validation for newly supported command args;
- expose progress/retry/action-log flows per supported command;
- run authenticated UI tests;
- run live smoke for each supported command;
- update dated Platform evidence and SOPs.
