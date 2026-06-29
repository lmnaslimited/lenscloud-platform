# Platform Handoff: Bench Command Result Display Contract - 2026-06-29

## Source

Infra completed the Bench Command sanitized result display contract.

```text
Infra repo: lenscloud-infra
Infra commit: 405e0c1
Infra workitem: INF-016
Infra evidence: docs/bench-command-result-display-evidence-20260629.md
Infra handoff: docs/platform-bench-command-handoff.md
```

## Objective

Update LensCloud Platform so successful Bench Command actions show the actual
safe result, not just `Succeeded`.

Example:

```text
Maintenance mode: Off
Developer mode: Off
CORS allowlist: https://app.example.com
```

## Runner Image

Use the current Infra-pinned runner digest:

```text
ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:ab69e3ff24584e268bfa92f44c5d71e680ce1780cc8a4a9a5ce1e60b3e4bf4e7
```

## Response Contract

The runner may return a top-level `display` object:

```json
{
  "display": {
    "label": "Maintenance mode",
    "value": "Off",
    "kind": "boolean",
    "rawValue": 0,
    "safe": true
  }
}
```

Platform should render `display` only when:

```text
display.safe == true
```

Use:

- `display.label` as the result label;
- `display.value` as the human-readable value;
- `display.kind` as a formatting hint;
- `display.rawValue` for backend assertions only when useful.

Do not render `details.value` directly unless the command/key is explicitly
known safe. Keep `details` for audit and tests.

## Display Mapping

| Command | Expected Display |
| --- | --- |
| `maintenance_mode.status` | `Maintenance mode: On/Off` |
| `developer_mode.status` | `Developer mode: On/Off` |
| `site_config.get` key `maintenance_mode` | `Maintenance mode: On/Off` |
| `site_config.get` key `developer_mode` | `Developer mode: On/Off` |
| `site_config.get` key `server_script_enabled` | `Server script: On/Off` |
| `site_config.get` key `client_script_enabled` | `Client script: On/Off` |
| `site_config.get` key `allow_cors` | `CORS allowlist: <safe origins>` |
| `cors.allowlist.get` | `CORS allowlist: <safe origins>` |

Boolean values are already normalized by Infra:

```text
0 / false -> Off
1 / true  -> On
```

## Failure Behavior

If `display` is absent, render only sanitized status fields:

```text
phase
code
summary
```

Expected examples:

```text
Unsupported / COMMAND_UNSUPPORTED
Failed / INVALID_ARGUMENTS
Failed / TARGET_NOT_FOUND
Failed / RUNNER_FAILED
```

Sensitive `site_config.get` keys must not show values. Infra rejects keys that
match password, token, secret, private key, credential, cookie, or authorization
patterns.

## Required Platform Work

1. Pull latest `lenscloud-infra` and confirm commit `405e0c1` or newer.
2. Update the pinned runner digest in Platform command Job generation.
3. Parse the runner termination summary and store the `display` object when
   present.
4. Render safe command results in:
   - Site action output;
   - Orchestration Action Log;
   - any Bench Command history/detail panel.
5. Add backend tests for:
   - `maintenance_mode.status` display;
   - `developer_mode.status` display;
   - `site_config.get` approved key display;
   - `cors.allowlist.get` display;
   - absent display for unsupported and failed commands;
   - no display for sensitive-key rejection.
6. Add UI tests or Playwright coverage proving readable command results are
   visible without exposing secret-like values.

## Security Rules

Never expose:

- kubeconfig contents;
- tokens;
- Kubernetes Secret values;
- DB passwords;
- private keys;
- pod logs;
- raw `site_config.json`;
- full environment dumps.

Do not require Platform operators to use `kubectl`.

## Platform Agent Prompt

```text
Work inside /workspace/frappe-bench/apps/lenscloud.

Pull latest /workspace/lenscloud-infra and confirm Infra commit 405e0c1 or newer.

Read:
- docs/handoffs/platform/bench-command-result-display-contract-20260629.md
- /workspace/lenscloud-infra/docs/platform-bench-command-handoff.md
- /workspace/lenscloud-infra/docs/bench-command-result-display-evidence-20260629.md
- docs/platform-workitems.md
- docs/operator-sop/bench-command-real-site-runner-verification.md

Implement Platform-side Bench Command result display.

Requirements:
- use runner image digest sha256:ab69e3ff24584e268bfa92f44c5d71e680ce1780cc8a4a9a5ce1e60b3e4bf4e7;
- prefer top-level display when present and display.safe is true;
- show label/value/kind in action output and Orchestration Action Log;
- never render details.value directly unless explicitly known safe;
- render sanitized phase/code/summary when display is absent;
- keep runner-pending families Unsupported;
- add tests for successful display, absent display, and sensitive-key rejection;
- do not expose kubeconfig, tokens, Secrets, DB passwords, private keys, pod logs, raw site_config.json, or env dumps.

Return:
- files changed;
- tests/build run;
- evidence that maintenance_mode.status now shows Maintenance mode: Off/On;
- remaining gaps.
```
