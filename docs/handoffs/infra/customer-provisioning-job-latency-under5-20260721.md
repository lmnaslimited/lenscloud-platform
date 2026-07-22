# Infra Handoff — Customer Provisioning Job Latency Under Five Minutes

Date: 2026-07-21
From: Platform
To: Infra
Status: Action required
Related gate: `docs/stage-gates/site-provisioning-under-5min-20260720.md`

## Outcome Required

Reduce cluster-side admission, scheduling, image startup, runner execution, and terminal-state delivery so a fresh customer Site can reach Ready in under 300 seconds.

Platform already observes Kubernetes Job terminal state every two seconds. Replacing polling with a watch may improve completion detection by at most about two seconds; it cannot explain the measured 36–201 second command intervals. Infra must therefore split actual Job latency from Platform observation and cleanup latency before proposing the fix.

## Live Evidence

Customer: `iron_monkey_private@example.com`

Site: `iron-monkey-0721081416.cloud.lmnaslens.com`

The recovery flow reached Ready with correct ordering and no duplicate commands, but took 492.885 seconds:

| Interval | Measured |
| --- | ---: |
| Bootstrap install | 201.197s |
| Setup complete | 71.437s |
| Setup verification | 36.685s |
| OAuth configure | 41.781s |
| OAuth verification | 134.733s |

Action logs:

| Action log | Operation | Result |
| --- | --- | --- |
| `ORCH-2026-00897` | `site_bootstrap.install_apps` | Succeeded |
| `ORCH-2026-00898` | `site_setup.complete` | Succeeded |
| `ORCH-2026-00899` | `site_setup.status` | Succeeded |
| `ORCH-2026-00900` | `oauth.configure` | Succeeded |
| `ORCH-2026-00901` | `oauth.status` | Succeeded |

Machine-readable evidence: `docs/evidence/customer-launch/provisioning-under5-20260721/iron-monkey-0721081416-recovery.json`.

## Infra Actions

For every command above, provide timestamps for:

1. Job create request received and admitted.
2. Job object created.
3. Pod scheduled.
4. Image pull started and completed, including cache-hit/miss.
5. Container started.
6. Runner command started and completed.
7. Termination summary written.
8. Kubernetes Job terminal condition set.
9. Any operator/runner acknowledgement emitted.

Then:

- explain the 201.197-second bootstrap interval and 134.733-second final OAuth verification interval;
- verify the Release-runtime image is digest-pinned and warm on eligible nodes before customer submission;
- verify the generic runner image is digest-pinned and warm on eligible nodes;
- reduce admission/scheduling and image-pull delay;
- remove avoidable runner startup or command initialization from `site_setup.status` and `oauth.status`;
- confirm whether a Kubernetes watch or an explicit terminal callback is supported and reliable;
- retain the existing nested `summary.message` failure envelope contract;
- do not weaken Release-runtime admission for app-aware commands.

## Target Budgets

| Command | Cluster terminal target |
| --- | ---: |
| `site_bootstrap.install_apps` | <= 90s |
| `site_setup.complete` | <= 60s |
| `site_setup.status` | <= 15s |
| `oauth.configure` | <= 30s |
| `oauth.status` | <= 15s |
| Job terminal to Platform-observable | <= 2s |

## Acceptance

Infra must return:

- before/after per-phase timestamps for each command family;
- evidence of image cache state;
- direct Release-runtime proof for app-aware commands;
- direct generic-runner proof for status/OAuth commands;
- proof that terminal Job state is observable by Platform within two seconds;
- the Infra commit range containing any fix;
- remaining caveats and the exact Platform retest procedure.

Return the result as:

`docs/handoffs/platform/customer-provisioning-job-latency-infra-return-20260721.md`

