# Live EU Orchestration Evidence - June 7, 2026

## Scope

- Platform revision: `d422323`
- Infra revision: `60158e5`
- Run prefix: `run-20260607-0623`
- Runtime namespace: `lenscloud-runtime-eu`
- Apply is disabled after the controlled Public window.
- No kubeconfig, token, password, or Kubernetes Secret value was recorded.

## Preflight

- Migration: passed.
- Full LensCloud backend suite: 7 of 7 passed.
- Frontend production build: passed.
- Restricted positive preflight: `all_required_allowed: true`.
- Negative RBAC: Node, CRD, Namespace, operator Deployment, and runtime delete mutations denied.
- Headlamp and wildcard smoke HTTPS: HTTP 200.
- Runtime namespace was empty before the run.

## Release

- Release Group: `lens-pure`
- Repository: `ghcr.io/lmnaslimited/lensdocker/lens-pure`
- Release: `RELEASE-lens-pure-v16.14.1`, submitted
- Digest: `sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2`
- Included app: ERPNext
- Frappe metadata: `16.14.0`; ERPNext metadata: `16.13.1`

## Inventory

Exact CR lookups returned 404 for the prior `run-20260606-0811-*` Benches and Sites. Their two Bench records were marked Retired and their two Site records marked Deleted/Released.

The legacy `bench-lenscx-eu-public` namespace is outside the restricted credential scope. Its draft records were preserved rather than assumed absent.

## Public Acceptance

Two unrelated customers use distinct Benches:

- `run-20260607-0623-pub-a` / `CUST001`
- `run-20260607-0623-pub-b` / `CUST002`

Both FrappeBench CRs are Ready and reference `MariaDB/default/frappe-mariadb`. Their manifests resolve `lens-pure:v16.14.1` and include ERPNext.

Live Sites:

- `run-20260607-0623-platform.cloud.lmnaslens.com`: page HTTP 200; generated `website.bundle.D4ZWF75O.css` HTTP 200.
- `run-20260607-0623-customer.cloud.lmnaslens.com`: page HTTP 200; generated CSS HTTP 200.
- `run-20260607-0623-free.cloud.lmnaslens.com`: created by authenticated customer Free Plan Playwright; page HTTP 200; generated CSS HTTP 200.

The platform and customer Sites use distinct logical database names and distinct database credential Secret references. Secret values were not read. No DNS Record document or per-Site certificate/TLS Secret was created.

Repeated Bench and Site reconciliation returned Ready, proving idempotent apply.

Key action logs:

- Public dry-run: `ORCH-2026-00042` through `ORCH-2026-00045`
- Public apply/sync: `ORCH-2026-00046` through `ORCH-2026-00054`
- Customer Free Plan request/apply/sync: `ORCH-2026-00055` through `ORCH-2026-00057`
- Idempotent reapply: `ORCH-2026-00058`, `ORCH-2026-00059`

## Browser Acceptance

- Authenticated desktop platform/customer Playwright: passed.
- Desktop customer submission created a real Free Plan Site: passed.
- Authenticated mobile platform/customer Playwright at 390x844: passed.
- Credential material remained in `/tmp/lenscloud-live-auth.json` with mode 600 and was not printed.

## Policy Evidence

Private Shared records and secret-safe manifests are prepared in dry-run:

- MariaDB: `run-20260607-0623-ps-db`
- Benches: `run-20260607-0623-ps-quality`, `run-20260607-0623-ps-production`
- Sites: matching Quality and Production hostnames
- Dry-run logs: `ORCH-2026-00060` through `ORCH-2026-00064`
- Cross-customer attachment rejected before apply with explicit privacy-boundary error: `ORCH-2026-00065`

Private records and secret-safe manifests are prepared in dry-run:

- MariaDB: `run-20260607-0623-private-db`
- Bench/Site: `run-20260607-0623-private`
- Dry-run logs: `ORCH-2026-00066` through `ORCH-2026-00068`
- Same-customer second Bench rejected before apply with explicit exclusivity error: `ORCH-2026-00069`

## External Cleanup Gate

Current live run-prefixed resources are:

- FrappeBench: `run-20260607-0623-pub-a`, `run-20260607-0623-pub-b`
- FrappeSite: `run-20260607-0623-platform`, `run-20260607-0623-customer`, `run-20260607-0623-free`
- PVC: `run-20260607-0623-pub-a-sites`, `run-20260607-0623-pub-b-sites`
- owned Jobs and Secrets may also exist under the exact prefix; values must not be read.

The restricted Platform identity cannot delete CRs, PVCs, Jobs, or Secrets. Infra capacity requires sequential scenarios. Manager-side exact-prefix cleanup is therefore required before live Private Shared and Private execution.

Preserve `default/frappe-mariadb` and every resource not named `run-20260607-0623` or beginning with `run-20260607-0623-`.

## Remaining Work

1. Infra removes only the completed Public run resources and confirms baseline health/capacity.
2. Platform enables apply, runs Private Shared live, captures HTTPS/static-asset evidence, and requests exact-prefix cleanup.
3. Platform runs Private live, captures evidence, and requests final exact-prefix cleanup.
4. Platform disables apply, completes the tracker, and records final production gaps.
