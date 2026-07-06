# CUA Site Setup Runner Platform Evidence - 2026-07-06

## Scope

Platform integrated the INF-021 setup-wizard Bench Command slice behind the existing Python Kubernetes API Bench Command path.

Implemented commands:

- `site_setup.status`
- `site_setup.complete`

Still unsupported/gated commands:

- `oauth.status`
- `oauth.configure`
- `user.ensure`
- `user.disable`
- `user.roles.set`
- `site_access.status`

## Infra Reconciliation

Checked Platform commit: `c520b5a`.

Read:

- `/workspace/lenscloud-infra/docs/infra-workitems.md`
- `/workspace/lenscloud-infra/docs/platform-bench-command-handoff.md`
- `/workspace/lenscloud-infra/docs/handoffs/platform/cua-site-setup-runner-handoff-20260706.md`
- `/workspace/lenscloud-infra/docs/evidence/cua/site-setup-runner-evidence-20260706.md`

Platform commit `c520b5a` removed the live-verification block. The local Platform handoff `docs/handoffs/infra/cua-site-bootstrap-sso-runner-20260703.md` records `site_setup.status` and `site_setup.complete` as live-verified. Platform can now proceed to the controlled Free Plan live E2E setup-runner test.

## Platform Changes

- Updated canonical workitem `CUA Site bootstrap and SSO automation` to `In Progress`.
- Added canonical workitem `CUA setup wizard runner integration`.
- Updated CUA architecture to remove the stale requirement for a branding/bootstrap app for setup wizard completion.
- Added `site_setup.status` and `site_setup.complete` to the Bench Command contract and Platform operator command selector.
- Updated the runner image digest to the active Infra handoff digest.
- Added strict non-secret scalar arg validation for `site_setup.complete`.
- Mounted the Bench sites PVC read-only for `site_setup.status`; `site_setup.complete` keeps read-write mount.
- Customer provisioning progress now includes setup status/defaults and future Platform access steps without exposing runtime terms.

## Validation

Backend:

```text
bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command
23 tests passed.
```

Frontend:

```text
npm --prefix frontend run build
Build passed.
```

## Live Status

No live customer/Site was created in the guarded implementation pass. After reconciling Platform commit `c520b5a`, the next pass should create a fresh customer/Site and run the setup status/complete sequence.

## Resume Point

Resume from:

1. Create a fresh test Customer and Free Plan Subscription.
2. Provision one real Prod Site.
3. Run `site_setup.status` from Platform against the Ready Site.
4. If pending, run `site_setup.complete` with non-secret setup args.
5. Run `site_setup.status` again and verify `display.safe=true` and `Setup wizard: Complete`.
6. Capture Orchestration Action Log IDs, sanitized display/result summary, Job/ConfigMap/pod cleanup proof, HTTPS/static asset proof, and customer-safe provisioning UI screenshots.
7. Keep OAuth, user sync, and Site access commands Unsupported until INF-022/INF-023 are complete.


## Live E2E Result - 2026-07-06

Result: **Passed with documented anomaly**.

Kept follow-on target for OAuth/social-login work:

```text
Customer: CUST004
Customer Member: CM-00004
Subscription: SUB-00002
Site: run-20260706-cua-134515.cloud.lmnaslens.com
URL: https://run-20260706-cua-134515.cloud.lmnaslens.com
Bench: run-20260702-free-prod-bench
Namespace: lenscloud-runtime-eu
Test user: run-20260706-cua-134515@gmail.com
```

The Site is intentionally **not deleted**. It remains the target for the next CUA OAuth/social-login setup pass.

### Provisioning Evidence

- Controlled apply window opened only for Site provisioning.
- Apply was restored to disabled after provisioning.
- Reconcile accepted: `ORCH-2026-00209`.
- Site reached Ready and HTTPS/static asset returned HTTP 200 on sync attempt 8: `ORCH-2026-00217`.
- Static asset proof:
  - page: `https://run-20260706-cua-134515.cloud.lmnaslens.com/` -> HTTP 200
  - asset: `https://run-20260706-cua-134515.cloud.lmnaslens.com/assets/frappe/dist/css/website.bundle.D4ZWF75O.css` -> HTTP 200

### Setup Runner Evidence

- First `site_setup.status`: `ORCH-2026-00219` failed with a container mount/startup error. The command Job, request ConfigMap, and terminal Pod were cleaned. Incident: `LC-E2E-20260706-003`.
- `site_setup.complete`: `ORCH-2026-00220` succeeded.
  - display: `Setup wizard: Complete`
  - summary: `Setup wizard completed`
  - cleanup removed:
    - `jobs/lenscloud-runtime-eu/bcmd-2026-00220-job`
    - `configmaps/lenscloud-runtime-eu/bcmd-2026-00220-request`
    - `pods/lenscloud-runtime-eu/bcmd-2026-00220-job-9gch6`
- Final `site_setup.status`: `ORCH-2026-00221` succeeded.
  - display: `Setup wizard: Complete`
  - summary: `Setup wizard is complete`
  - cleanup removed:
    - `jobs/lenscloud-runtime-eu/bcmd-2026-00221-job`
    - `configmaps/lenscloud-runtime-eu/bcmd-2026-00221-request`
    - `pods/lenscloud-runtime-eu/bcmd-2026-00221-job-ffh9g`
- Repeated final `site_setup.status`: `ORCH-2026-00223` succeeded.
  - display: `Setup wizard: Complete`
  - cleanup removed:
    - `jobs/lenscloud-runtime-eu/bcmd-2026-00223-job`
    - `configmaps/lenscloud-runtime-eu/bcmd-2026-00223-request`
    - `pods/lenscloud-runtime-eu/bcmd-2026-00223-job-cr2q8`

### Runtime Inventory

- Site runtime inventory: `ORCH-2026-00222`.
- Owner CR present: `true`.
- Related counts: `Ingress=1`, `Job=1`, `PersistentVolumeClaim=0`, `Pod=0`, `Service=0`.
- No command Job/ConfigMap/terminal Pod remained from the successful setup commands according to the cleanup responses above.

### Negative/Security Evidence

- Future CUA command unsupported behavior:
  - `oauth.status` returned `COMMAND_UNSUPPORTED` after fix: `ORCH-2026-00207`.
  - Incident: `LC-E2E-20260706-001`, closed.
- Stale runner digest admission failure:
  - `site_setup.status` Job denied when Platform used stale digest `b209...`: `ORCH-2026-00218`.
  - Fixed by updating Platform `RUNNER_IMAGE` to INF-021 digest `sha256:2905fb71dfb449258214a7b76016a67d9b98bd66ea378394f98d791ab293dad5`.
  - Incident: `LC-E2E-20260706-002`, closed.
- Sensitive setup arg rejection:
  - `site_setup.complete` rejected `password` before Kubernetes resource creation with: `Setup arg password is not allowed because it looks sensitive.`

### Validation Commands

```text
bench --site dev.localhost run-tests --module lenscloud.api.test_bench_command
23 tests passed.
```

No Playwright was run for this slice because the acceptance proof was backend/runtime/API based and the Site/HTTPS/static-asset checks were performed by `sync_site_status`.

### Remaining CUA Gaps

- OAuth/social-login runner commands remain Unsupported until INF-022.
- User sync, role sync, Site Access Grants, revocation, and passwordless Open Site remain Unsupported until INF-023.
- The kept Site above should be reused for the next OAuth/social-login runner pass.
