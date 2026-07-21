# Infra Return - Customer Provisioning Job Latency Under Five Minutes

Date: 2026-07-21
From: Infra
To: Platform
Status: Returned with infra-side fix and Platform retest procedure
Request: `docs/handoffs/infra/customer-provisioning-job-latency-under5-20260721.md`

## Summary

Infra installed live image prewarm and proved that Kubernetes admission,
scheduling, image startup, and terminal delivery are now inside the requested
budgets. The remaining under-five-minute blocker is the separate
post-ready `site_bootstrap.install_apps` Job for default creation apps.

Use the operator-native `FrappeSite.spec.apps` path for default
install-at-site-creation apps, then consume:

```text
FrappeSite.status.installedApps
FrappeSite.status.appInstallationStatus
FrappeSite.status.conditions[type=Ready]
```

## Infra Changes

- Added verifier:
  `lenscloud-infra/scripts/66-verify-customer-provisioning-job-latency.sh`
- Installed live DaemonSet:
  `lenscloud-runtime-eu/lenscloud-command-image-prewarm`
- Warming:
  - `ghcr.io/lmnaslimited/lensdocker/lens-pure@sha256:92196b4fb5c016e006c0bddc7ecffd6ba4ad8ce23c6ad290e81840fea0f6bca0`
  - `ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:3b71912830d3dac1465a7e3cfa03dd64c76b17826fd7614a6801e4c539813cf5`

Canonical evidence:

```text
lenscloud-infra/docs/customer-provisioning-job-latency-evidence-20260721.md
```

## Timing Evidence

After prewarm:

| Command | Observed wait | Terminal to observed |
| --- | ---: | ---: |
| `site_bootstrap.install_apps` idempotent | 10.236s | 0.216s |
| `site_setup.complete` idempotent | 10.479s | 0.407s |
| `site_setup.status` | 10.265s | 0.635s |
| `oauth.status` | 10.558s | 0.861s |
| `oauth.configure` | 14.078s | 1.443s |

All probes reported image cache hits. The temporary OAuth provider
`lenscloud_latency_probe` was removed after the configure proof.

## Completion Delivery

Platform service account watch support is already present:

```text
watch jobs.batch: yes
watch pods: yes
watch events: yes
```

No separate operator callback exists for Platform-created Bench Command Jobs.
Use Kubernetes list-then-watch for Jobs/Pods, with relist on reconnect. Polling
every two seconds is acceptable but should add only about two seconds; it does
not explain the 201s or 134s intervals.

## Required Platform Adjustment

For default creation apps, set `FrappeSite.spec.apps` when creating the Site and
skip the later `site_bootstrap.install_apps` Job once operator status confirms
the requested apps. Keep app-aware Jobs for post-creation capability installs.

The live `iron-monkey-0721081416` Site had no `spec.apps`; the operator
reported only Frappe framework installed, so Platform had to do a separate
bootstrap Job.

## Retest

1. Keep `lenscloud-command-image-prewarm` ready.
2. Create a fresh customer Site with default creation apps in
   `FrappeSite.spec.apps`.
3. Observe operator Ready plus `installedApps`/`appInstallationStatus`.
4. Skip post-ready bootstrap when those fields prove default apps are present.
5. Run setup/OAuth commands and measure command wait, terminal observation,
   route verification, socket delivery, and cleanup separately.

Expected warm-image command budgets: status/OAuth reads under 15s,
OAuth configure under 30s, terminal-to-observed under 2s.

## Platform Acceptance Preparation — 2026-07-21

Infra checkout was fast-forwarded from `a23258a` to `1697eae`. Platform reviewed the canonical Infra evidence and accepted these findings:

- image prewarm is ready for both digest-pinned execution images;
- Job terminal state is observable within the two-second contract;
- direct warm-image `site_setup.status`, `oauth.status`, and `oauth.configure` are within their requested budgets;
- the former 201-second bootstrap interval was real post-creation installation work, not Job-handshake latency.

Platform preparation completed before the next destructive test reset:

- `FrappeSite.spec.apps` now receives the Release Group apps marked `install_at_site_creation`;
- operator `Ready`, `installedApps`, `failedApps`, and `appInstallationStatus` are evaluated during Site status synchronization;
- Platform creates the canonical successful bootstrap action only when every requested creation app is confirmed and no requested app failed;
- missing/unconfirmed apps do not get treated as installed and retain the safe legacy fallback;
- operator-reported installation failure becomes a failed bootstrap action and stops automatic advancement;
- the separate post-ready bootstrap Job is skipped after operator-native confirmation.

Validation:

- `lenscloud.api.test_customer_site_setup`: 27 passed
- `lenscloud.api.test_provisioning_progress`: 9 passed
- `git diff --check`: passed

Platform is ready for the customer test Site and Subscription to be deleted. The next run must create a new Site/Subscription through the customer portal and retain the Infra prewarm DaemonSet.
