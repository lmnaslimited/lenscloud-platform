# Platform Handoff: LensCloud Message Envelope Infra Return - 2026-07-20

Infra implemented the source-side LensCloud message envelope for scoped POC
runner failures and verified it locally.

Infra workitem:

```text
INF-028 LensCloud message envelope for runner/operator failures
Status: Ready for Verification
```

Source contract:

```text
apps/lenscloud/docs/handoffs/infra/lenscloud-message-envelope-runner-contract-20260720.md
```

Infra source/evidence:

```text
lenscloud-infra/docs/handoffs/platform/lenscloud-message-envelope-infra-return-20260720.md
lenscloud-infra/docs/lenscloud-message-envelope-evidence-20260720.md
lenscloud-infra/bench-command-runner/message_catalog.v1.json
```

Infra revision:

```text
base commit: 5de2908
implementation commit: 603b894
```

Runner image digest:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:3b71912830d3dac1465a7e3cfa03dd64c76b17826fd7614a6801e4c539813cf5
```

The repo admission manifest is pinned to this digest. Live admission apply and
verification passed on 2026-07-21.

Manager checkout note:

```text
manager: 116.203.22.81:/root/lenscloud-infra
local repo used as canonical
previous manager checkout backup: /root/lenscloud-infra.backup-20260721-001545
```

## Canonical Envelope

Infra selected a nested `message` object. Platform should parse this shape:

```json
{
  "phase": "Failed",
  "code": "INVALID_ARGUMENTS",
  "command": "site_setup.complete",
  "commandId": "local-generic",
  "summary": "site_setup.complete args contain a sensitive key",
  "changed": false,
  "redacted": true,
  "message": {
    "message_id": "LC-INFRA-RUNNER-0002",
    "message_type": "Error",
    "source": "Runner",
    "destination": "Platform",
    "params": {
      "operation": "site_setup.complete",
      "reason": "INVALID_ARGUMENTS"
    },
    "safe_summary": "Runner command failed.",
    "details_ref": null
  }
}
```

When present, `message.message_id` is primary and must take precedence over
legacy summary/code pattern matching.

## Catalog

Machine-readable catalog:

```text
lenscloud-infra/bench-command-runner/message_catalog.v1.json
```

Final IDs:

| Message ID | Required params | Optional params |
| --- | --- | --- |
| `LC-INFRA-RUNNER-0001` | `operation`, `reason` | `requested_image_digest`, `admitted_image_digest` |
| `LC-INFRA-RUNNER-0002` | `operation`, `reason` | `exit_code` |
| `LC-INFRA-STORAGE-0001` | `operation`, `reason`, `mount_kind` | `layout`, `pvc` |
| `LC-INFRA-UNKNOWN-0001` | `operation`, `reason` | none |
| `LC-INFRA-QUEUE-0001` | `operation`, `reason` | `queue`, `queued_count` |
| `LC-INFRA-BOOTSTRAP-0001` | `operation`, `reason` | `app`, `exit_code` |
| `LC-INFRA-TIMEOUT-0001` | `operation`, `reason`, `timeout_seconds` | none |
| `LC-INFRA-COMMAND-0001` | `operation`, `reason` | none |

Platform-owned IDs remain reserved and Infra does not emit them:

```text
LC-PLATFORM-QUEUE-0001
LC-PLATFORM-BOOTSTRAP-0001
LC-PLATFORM-UNKNOWN-0001
```

## Verification

Automated contract test:

```bash
python3 -m unittest bench-command-runner/test_message_envelope.py
```

Result:

```text
Ran 4 tests in 1.045s
OK
```

Backward-compatibility smoke:

```bash
scripts/59-test-bench-command-runner-local.sh
```

Result:

```text
Bench command runner local verification passed.
```

Live admission verification:

```bash
MANAGER_KUBECONFIG=/etc/rancher/k3s/k3s.yaml \
PLATFORM_KUBECONFIG=/root/lenscloud-infra/.artifacts/lenscloud-eu.kubeconfig \
RUNTIME_NAMESPACE=lenscloud-runtime-eu \
scripts/58-verify-platform-bench-command.sh
```

Result:

```text
Bench Command Job/API RBAC verification passed.
Accepted Bench Command runner image: ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:3b71912830d3dac1465a7e3cfa03dd64c76b17826fd7614a6801e4c539813cf5
Accepted Bench Command runner image for site_setup.status: admitted
Stale Bench Command runner image for site_setup.status: denied
Generic runner image for site_setup.complete: denied
```

Live INF-028 envelope verification:

```text
runner image: ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:3b71912830d3dac1465a7e3cfa03dd64c76b17826fd7614a6801e4c539813cf5
prefix: run-20260721-0023-inf028
result: INF-028 live envelope verification passed
```

Covered live command IDs:

| Command ID | Command | Result |
| --- | --- | --- |
| `run-20260721-0023-inf028-success` | `site_setup.status` | `Succeeded`, no failure `message`, safe `display` |
| `run-20260721-0023-inf028-storage` | `site_setup.status` | `LC-INFRA-STORAGE-0001` |
| `run-20260721-0023-inf028-generic` | `oauth.status` | `LC-INFRA-RUNNER-0002` |
| `run-20260721-0023-inf028-timeout` | `oauth.status` | `LC-INFRA-TIMEOUT-0001` |
| `run-20260721-0023-inf028-unknown` | `oauth.status` | `LC-INFRA-UNKNOWN-0001` |
| `run-20260721-0025-inf028-oauth-configure` | `oauth.configure` | `LC-INFRA-RUNNER-0002` |

Cleanup:

```text
no job/configmap/pod resources remain for run-20260721-0023-inf028
no job/configmap/pod resources remain for run-20260721-0025-inf028-oauth-configure
```

Controlled evidence covered:

| Command ID | Command | Expected ID |
| --- | --- | --- |
| `local-unsupported` | `site_bootstrap.install_apps` | `LC-INFRA-COMMAND-0001` |
| `local-storage` | `site_setup.status` missing site path | `LC-INFRA-STORAGE-0001` |
| `local-queue` | `site_setup.complete` fake queue overload | `LC-INFRA-QUEUE-0001` |
| `local-timeout` | `oauth.status` fake timeout | `LC-INFRA-TIMEOUT-0001` |
| `local-bootstrap_a` | `site_bootstrap.install_apps` fake failed app | `LC-INFRA-BOOTSTRAP-0001` |
| `local-generic` | `site_setup.complete` rejected sensitive args | `LC-INFRA-RUNNER-0002` |
| `local-unknown` | `oauth.status` forced unknown failure | `LC-INFRA-UNKNOWN-0001` |
| `local-success` | `site_setup.status` success | no failure message |

Security evidence:

```text
Canaries absent from every tested termination payload:
must-not-leak
db_password
admin_password
client_secret
token=
private_key
BEGIN 
```

Cleanup evidence:

```text
Only local temp directories were created and removed.
No Kubernetes resources were created, changed, or deleted.
Protected baseline was not touched.
```

## Backward Compatibility

Existing top-level fields remain:

```text
phase
code
command
commandId
target
summary
changed
details
display
redacted
```

Successful commands do not include a failure `message`. Failed and unsupported
commands still do not include `display`.

## Required Platform Changes

Update `lenscloud.api.messages` and the Bench Command result parser to:

1. Prefer nested `message.message_id` when present.
2. Store exact `message.params` as JSON.
3. Resolve message metadata from Platform's catalog mirror.
4. Set `matched_by = Infra Supplied`.
5. Retain legacy pattern matching only when `message.message_id` is absent.
6. Keep defensive sanitization.

Attach to `Orchestration Action Log`:

```text
message_id
params
message_type
source
destination
safe_summary
details_ref
resolution_owner
retryability
matched_by = Infra Supplied
```

## Platform Retest

Run:

```bash
bench --site dev.localhost run-tests --app lenscloud --module lenscloud.api.test_message_framework
bench --site dev.localhost run-tests --app lenscloud --module lenscloud.api.test_provisioning_progress
bench --site dev.localhost run-tests --app lenscloud --module lenscloud.api.test_customer_site_setup
bench --site dev.localhost run-tests --app lenscloud --module lenscloud.api.test_bench_command
```

After Infra live-admits the runner image containing INF-028, run:

```text
site_setup.status
site_setup.complete
site_setup.status
oauth.status
oauth.configure
oauth.status
```

Expected action-log proof:

```text
message_id = Infra supplied LC-INFRA-*
params = exact safe JSON object from termination payload
matched_by = Infra Supplied
resolution_owner = Infra
retryability = Retry After Infra Action
customer-safe rendering uses Platform catalog text
```

Deferred:

- Platform action-log proof for `matched_by = Infra Supplied`;
- live generic-runner envelope tests for `site_setup.complete` and
  `site_bootstrap.install_apps`, deferred by the current app-aware admission
  boundary;
- operator scheduling/image-pull/admission failure live evidence;
- message envelopes outside the POC command set.

## Platform Verification - 2026-07-21

Platform integrated the canonical nested envelope and Infra v1 catalog. Migration, 79 focused tests, and live success compatibility action ORCH-2026-00872 passed. Evidence: docs/evidence/customer-launch/message-envelope-platform-verification-20260721.md. Live failure capture ORCH-2026-00873 persisted LC-INFRA-STORAGE-0001 with matched_by Infra Supplied; temporary resources were cleaned.

The app-aware generic-runner caveat is accepted: site_setup.complete and site_bootstrap.install_apps remain on the digest-pinned Release runtime path. Their live failure-envelope proof is deferred to the Release-runtime implementation and must not be obtained by weakening admission.

## Copy/Paste Platform Prompt

```text
You are in lenscloud-platform/frappe-bench/apps/lenscloud.

Read:
- docs/handoffs/platform/lenscloud-message-envelope-infra-return-20260720.md
- docs/handoffs/infra/lenscloud-message-envelope-runner-contract-20260720.md
- docs/stage-gates/integration-message-model-poc-20260720.md
- docs/stage-gates/site-provisioning-under-5min-20260720.md
- lenscloud/api/messages.py
- lenscloud/api/provisioning_progress.py

Implement Platform parsing for the Infra canonical nested runner envelope:
- Prefer result.message.message_id when present.
- Store result.message.params as the exact safe JSON object.
- Mark action-log matches as matched_by = Infra Supplied.
- Attach resolution owner, retryability, source, destination, type, and safe summary from the Platform catalog mirror.
- Keep legacy fallback pattern matching only when Infra did not supply a message_id.
- Keep existing phase/code/summary/display compatibility.
- Never render raw stderr, pod logs, site_config.json, environment dumps, OAuth secrets, tokens, kubeconfigs, private keys, or Kubernetes Secret values.

Run:
- bench --site dev.localhost run-tests --app lenscloud --module lenscloud.api.test_message_framework
- bench --site dev.localhost run-tests --app lenscloud --module lenscloud.api.test_provisioning_progress
- bench --site dev.localhost run-tests --app lenscloud --module lenscloud.api.test_customer_site_setup
- bench --site dev.localhost run-tests --app lenscloud --module lenscloud.api.test_bench_command

After Infra publishes/pins the runner image containing INF-028, run the controlled Site provisioning retest:
site_setup.status -> site_setup.complete -> site_setup.status -> oauth.status -> oauth.configure -> oauth.status.

Record action-log evidence proving:
- matched_by = Infra Supplied
- Infra message_id and params are retained
- customer-safe/operator-safe rendering works
- unknown controlled failures map to LC-INFRA-UNKNOWN-0001
- successful provisioning still advances one stage at a time without duplicate commands

Update the message model and under-five-minute stage gates only after evidence passes.
```
