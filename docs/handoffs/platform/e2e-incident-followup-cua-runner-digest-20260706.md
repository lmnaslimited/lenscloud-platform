# E2E Incident Follow-Up - LC-E2E-20260706-002

## Incident

CUA setup runner live E2E created and kept Site `run-20260706-cua-134515.cloud.lmnaslens.com`, but `site_setup.status` failed at Job admission. Platform used stale runner digest `b209...`; INF-021 evidence and admission pin use `ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:2905fb71dfb449258214a7b76016a67d9b98bd66ea378394f98d791ab293dad5`.

## Fix

Update `lenscloud/api/bench_command.py` `RUNNER_IMAGE` and Platform docs/evidence to the INF-021 live-verified digest.

## Retest

1. Run `bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command`.
2. Run `site_setup.status` against kept Site `run-20260706-cua-134515.cloud.lmnaslens.com`.
3. If pending, run `site_setup.complete` with non-secret setup args.
4. Run final `site_setup.status`.
5. Confirm Job/ConfigMap/terminal Pod cleanup and close this incident.
6. Keep the Site for OAuth/social-login follow-on.
