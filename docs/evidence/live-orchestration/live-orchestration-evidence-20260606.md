# Live EU Orchestration Evidence - June 6, 2026

## Scope

- Run prefix: `run-20260606-0811`
- Runtime namespace: `lenscloud-runtime-eu`
- Infra reference: `lenscloud-infra` revision `41a7ca7`
- Apply was enabled only for controlled reconciliation windows and is disabled.

## Platform-Side Results

- Migration completed.
- LensCloud backend tests passed: 5 of 5.
- Frontend production build passed.
- Authenticated Playwright passed for a System User platform dashboard and a Website User customer Create Site flow, including a successful Free Plan request and dry-run reconciliation while apply was disabled.
- Restricted permission preflight initially returned `all_required_allowed: true`.
- The final preflight timed out after the Kubernetes API endpoint became unreachable. If the laptop changed networks, run the infra API authorization watcher before continuing.
- Two Public Benches reconciled and synchronized as Ready: `run-20260606-0811-pub-a` and `run-20260606-0811-pub-b`.
- Platform and customer Free Plan Site creation reached operator Ready for `run-20260606-0811-platform.cloud.lmnaslens.com` and `run-20260606-0811-customer.cloud.lmnaslens.com`.
- The Sites received distinct logical database names and credential Secret references. Secret values were not read.
- No LensCloud DNS Record documents were created for either wildcard Site.
- Repeated Site reconciliation preserved the resources and advanced observed generation.
- Private Shared cross-boundary rejection and Private second-Bench rejection passed in backend tests.

## Action Logs

- Bench apply: `ORCH-2026-00029`, `ORCH-2026-00030`
- Bench status sync: `ORCH-2026-00031`, `ORCH-2026-00032`
- Initial Site apply/request: `ORCH-2026-00033` through `ORCH-2026-00035`
- Site reapply after encryption Secret contract fix: `ORCH-2026-00036`, `ORCH-2026-00037`

## Runtime Result

- Both FrappeSite resources reported `Ready` and both initialization Jobs
  reported `Succeeded`, but both wildcard HTTPS routes returned HTTP 500.
- An initial event recorded a missing `*-encryption-key` Secret. LensCloud now creates that Secret and includes `spec.encryptionKeySecretRef`; generation 3 was observed after reapply, but the routes still return 500.
- The restricted identity cannot read pod logs or delete FrappeSite, FrappeBench, Job, Secret, or PVC resources.
- Capacity was sequential-only, so Private Shared and Private live scenarios
  were deferred.

## Historical Infra Diagnostic Boundary

Infra inspected redacted logs for only the `run-20260606-0811-*` resources and
identified the missing operator asset cache as the root cause.

Never disclose Secret values. Preserve all resources in `default` and every pre-existing resource.

## Manager Cleanup Result

After evidence was captured, Infra deleted only resources whose names began
with `run-20260606-0811` in `lenscloud-runtime-eu`.

Infra confirmed:

- no `run-20260606-0811*` resource remains in `lenscloud-runtime-eu`
- `default/frappe-mariadb` is unchanged
- all pre-existing default Bench, Site, PVC, workload, and route resources remain
- restricted permission preflight returns `all_required_allowed: true`
- capacity is available for sequential Private Shared and Private scenarios.

## Closure

Infra diagnosed the failure as an image/operator filesystem contract mismatch:
the image lacked `/home/frappe/assets_cache`, so the operator-mounted assets PVC
remained empty.

The June 6 run was safely removed. On June 7, 2026, the replacement image
`ghcr.io/lmnaslimited/lensdocker/lens-pure:v16.14.1` passed live acceptance:

- Bench init copied the image asset cache into the PVC;
- Frappe `16.14.0` and ERPNext `16.13.1` installed successfully;
- the Site and generated CSS returned HTTPS 200;
- Administrator authentication succeeded.

The blocker recorded here is closed. New acceptance evidence must be written to
a new dated document and must cover Public, Private Shared, and Private using
the `lens-pure` Release.
