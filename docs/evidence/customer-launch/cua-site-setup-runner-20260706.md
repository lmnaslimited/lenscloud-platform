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
