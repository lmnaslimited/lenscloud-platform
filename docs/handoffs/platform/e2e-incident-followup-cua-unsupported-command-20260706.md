# E2E Incident Follow-Up - LC-E2E-20260706-001

## Incident

During the CUA setup runner E2E negative proof, `oauth.status` returned a validation error because OAuth/user/site-access commands were not in `CONTRACTED_COMMANDS`. Expected behavior is a safe `COMMAND_UNSUPPORTED` response until INF-022/INF-023 are implemented.

## Fix

Add future CUA runner commands to `RUNNER_PENDING_COMMANDS` and `CONTRACTED_COMMANDS`, but do not add them to `SUPPORTED_COMMANDS`.

## Retest

1. Run `bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command`.
2. Execute `oauth.status` against a Ready Site through `lenscloud.api.bench_command.run_site_control_command`.
3. Confirm response status is `Unsupported` and code is `COMMAND_UNSUPPORTED`.
4. Close the incident in `docs/incidents/e2e-incident-tracker.md` and resume the CUA setup runner E2E.
