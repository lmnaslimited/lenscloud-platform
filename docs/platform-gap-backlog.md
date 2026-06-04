# LensCloud Platform Gap Backlog

## Purpose

This backlog captures gaps found during the platform UI and operator-readiness review. It should be read before the next implementation pass.

## Frontend Routing And Runtime Gaps

These are small but important polish gaps before the platform is used for day-to-day work.

- Add default child redirects:
  - `/lenscloud/platform` should route to `/lenscloud/platform/dashboard`.
  - `/lenscloud/customer` should route to `/lenscloud/customer/dashboard`.
- Avoid noisy unauthenticated console errors:
  - `frappe.auth.get_logged_user` may return `403` for guest access.
  - The UI should continue handling this gracefully, but the session bootstrap should avoid presenting normal guest state as a runtime error.
- Handle Socket.IO availability cleanly:
  - WebSocket warnings can appear when Socket.IO is not running or not connected.
  - The UI should not depend on live socket connectivity for initial page rendering.
- Add a favicon:
  - `/favicon.ico` currently returns `404`.
- Keep lifecycle actions UI-only until backend support exists:
  - create, suspend, delete, backup, restore, upgrade, and DNS action surfaces must remain clearly marked as pending/locked/gap until wired to real backend/operator jobs.

## Release Model Correction

Release Group is master data. Release is the deployable transaction.

Do not put image tag or active release status on Release Group as the deployable version.

### Release Group Fields

Release Group should hold:

- title/name
- registry URL
- image repository
- included apps(Table multiselect or child table) - APP as a separate doctype
- apps/version metadata
- supported Frappe major version
- release policy
- active/inactive status

### Release Fields

Release should hold:

- release group
- image tag
- image digest when available
- build status
- build number or pipeline reference
- release status
- build date
- promoted date
- changelog or release notes
- compatibility notes
- rollout eligibility

## Operator-Readiness Data Gaps

To create a Bench through the Frappe Operator, the platform needs fields that map LensCloud records to Kubernetes/operator resources.

### Bench Fields

Bench should add:

- Kubernetes namespace
- operator resource name
- storage class
- release group
- current release
- next release
- bench status
- cluster or region runtime target
- upgrade schedule/window
- upgrade policy
- upgrade/SOP status

### Site Fields

Site should add:

- domain
- subdomain
- site status
- provisioning status
- operator resource name
- DNS status
- backup state
- restore state
- upgrade state

### Platform Settings Fields

Platform Settings should add:

- active cluster/context reference
- operator namespace
- default storage class
- default bench namespace pattern
- Route53 hosted zone ID or zone reference
- root domain
- integration toggles/status fields
- billing system configuration/status
- CRM system configuration/status
- support system configuration/status

## Infra And Operator Backend Gaps

The next implementation stage must connect LensCloud Platform to a real cluster created by `lenscloud-infra`.

- `lenscloud-infra` must create a live dev cluster.
- The cluster must install MariaDB Operator and Frappe Operator.
- The cluster handoff must expose:
  - region
  - kube context/API endpoint reference
  - operator namespace
  - default storage class
  - ingress mode
  - cluster status
- LensCloud Platform must register or reference that handoff.
- Bench creation must create or reconcile a `FrappeBench` resource.
- Site creation must create or reconcile a `FrappeSite` resource.
- Backup and restore actions must map to operator-supported backup/restore resources.
- `SiteJob` must not be assumed production-ready unless the operator code proves it.

## Implementation Order

1. Fix route redirects, guest session noise, Socket.IO tolerance, and favicon.
2. Correct the Release Group / Release / Bench data model.
3. Add operator-readiness fields to Bench, Site, and Platform Settings.
4. Update platform UI catalog and views for Release and release-level tracking.
5. Bring `lenscloud-infra` to a live dev cluster and produce a handoff artifact.
6. Wire platform backend actions to operator-backed Bench/Site creation.

