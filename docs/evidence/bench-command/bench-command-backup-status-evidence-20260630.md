# Bench Command Backup Status Evidence - 2026-06-30

## Scope

Consume Infra `INF-017` for the metadata-only `backup.status` Bench Command runner path and keep backup create, restore, Bench Test trigger, and LATP trigger/status truthful as Unsupported until their runner contracts are implemented.

This evidence is non-secret. Do not record kubeconfig contents, tokens, Kubernetes Secret values, DB passwords, private keys, pod logs, raw backup content, raw `site_config.json`, or full environment dumps.

## Infra Source

```text
Infra revision: ac86bdc
Infra evidence: lenscloud-infra/docs/bench-command-remaining-families-evidence-20260630.md
Infra handoff: lenscloud-infra/docs/platform-bench-command-handoff.md
Runner image: ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:eebfa0199c328207b14a949fa6232954a203a3937b1eed4930e9c3ec95b654d6
```

## Platform Change

Platform updated the pinned runner digest and now treats `backup.status` as a supported read/status command. The remaining contracted commands stay Unsupported:

```text
backup.create
restore.preview
restore.execute
restore.status
bench_test.trigger
latp.trigger
latp.status
```

`backup.status` uses the existing safe display contract only when the runner marks `display.safe=true`.

## Direct Backend Evidence

```text
site: run-20260629-free-prod-site.cloud.lmnaslens.com
command: backup.status
action log: ORCH-2026-00170
command id: BCMD-2026-00170
status: Succeeded
display text: Backups: 0 available
summary kind: backup-status
summary rawValue: {"count": 0, "latest": null}
cleanup: command Job and ConfigMap removed
post-cleanup verification: jobs=[], configmaps=[]
```

Unsupported direct check:

```text
command: backup.create
action log: ORCH-2026-00171
status: Unsupported
code: COMMAND_UNSUPPORTED
runner Job created: no
```

## Authenticated UI Evidence

Authenticated Playwright exercised the Site action panel and proved both display and unsupported behavior:

```text
command: backup.status
action log: ORCH-2026-00172
status: Succeeded
visible UI card: Bench Command result -> Backups: 0 available
cleanup: command Job and ConfigMap removed
post-cleanup verification: jobs=[], configmaps=[]
```

```text
command: backup.create
action log: ORCH-2026-00173
status: Unsupported
message: contracted but unsupported by the current runner/API
successful result display: absent
```

## Validation

```text
python3 -m py_compile lenscloud/api/bench_command.py
bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:bench-command-backup-status
```

Result:

```text
backend tests: 17 passed
frontend build: passed
Playwright backup.status display and backup.create unsupported checks: passed
```

The production frontend build reported existing Rollup PURE-comment and chunk-size warnings only.

## Remaining Gaps

- `backup.create` runner contract is still pending.
- Restore preview/execute/status runner contracts are still pending.
- Bench Test trigger runner contract is still pending.
- LATP trigger/status runner contracts are still pending.
- Backup retention/location policy and evidence model remain product/runtime design work.
