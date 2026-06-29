# LensCloud Release Model

## Purpose

LensCloud separates stable release-family master data from deployable release transactions.

## Release Group

Release Group is master data. It represents a product/image family.

Release Group should hold:

- title/name
- registry URL
- image repository
- included apps, selected from `App` master data through the `Release Group Apps` table multiselect
- supported Frappe major version
- release policy
- active/inactive status

Release Group should show:

- Releases in this family
- Benches using this family
- number of Benches per Release level
- Benches behind the latest eligible Release
- high-level actions such as create Release, promote Release, schedule rollout, and compare adoption

## Release

Release is transactional. It represents a specific deployable image/version inside a Release Group.

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

Release should support:

- mark build ready
- promote to Quality
- promote to Production eligible
- block Release
- view affected Benches
- schedule Bench upgrades

## Bench

Bench is the runtime deployment group. A Bench belongs to a Release Group and deploys a specific current Release from that group.

Bench should hold:

- release group
- current release
- next release
- region
- privacy
- namespace
- operator resource name
- storage class
- bench status
- upgrade window or scheduled upgrade time
- upgrade policy

Bench should support:

- create Bench from Release Group and Release
- schedule upgrade to next Release
- run pre-upgrade checklist
- start upgrade
- verify upgrade
- rollback to previous Release
- mark upgrade complete

## SOP Entity

The next operational layer should introduce a transactional entity such as `Bench Upgrade Plan` or `Release Rollout Plan`.

It should hold:

- bench
- current release
- target release
- scheduled window
- status
- checklist state
- operator job reference
- started at
- completed at
- rollback release
- approval owner
- notes

## Implementation Status

The first LensCloud Platform implementation pass now reflects this model:

- `Release Group` remains master data and no longer carries a deployable image tag/current-version concept.
- `App` is available as release-family master data, and `Release Group.included_apps` uses the `Release Group Apps` table multiselect instead of long text.
- `Release` is available as the transactional deployable version and links to `Release Group`.
- `Bench` links to `release_group`, `current_release`, and `next_release`, and carries upgrade window, policy, and SOP status fields.
- Frontend platform resources include `Release` and expose Release Group adoption, Release affected benches, Bench current/next release, and operator-readiness metadata.

Build/promotion and rollout planning remain future workflow work. Bench and
Site operator reconciliation is implemented and must now be live-accepted
through the approved `lens-pure` Release.

Approved Phase 1 release data:

- Release Group: `lens-pure`
- repository: `ghcr.io/lmnaslimited/lensdocker/lens-pure`
- Release tag: `v16.14.1`
- digest:
  `sha256:86dd9bec4ef7ef255bff6596b15480e88b3fb27751e1c88b22167ff69fb4a2a2`
- Frappe: `16.14.0`
- ERPNext: `16.13.1`

## Release Document Lifecycle

`Release` is a submittable Frappe document.

- Draft Release records can be edited and submitted through the platform UI.
- Submitted Release records represent approved transactional release metadata for a Release Group.
- Cancel and Amend use native Frappe document lifecycle semantics.
- Submitting a Release does not deploy it to a Bench; Bench movement still requires an explicit rollout/upgrade workflow and future operator-backed wiring.

## Implementation Guidance

- Do not store image tag on Release Group as the active deployable version.
- Do not upgrade a Bench directly by changing Release Group.
- Bench upgrades should move from current Release to next/target Release through an explicit SOP workflow.
- Frontend pages must distinguish master data, deployable release, and runtime bench state.
- Operator integration must use Bench current Release to derive the image deployed by `FrappeBench`.
