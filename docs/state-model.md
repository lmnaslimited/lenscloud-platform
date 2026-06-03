# LensCloud Platform State Model

## Core Entities

- Customer
- Subscription
- Release Group
- App
- Release
- Bench
- Site
- DNS Record
- Backup
- Restore
- Upgrade
- Bench Upgrade Plan

## Supporting Concepts

- Region
- Environment
- Tenant placement
- Approval state
- Provisioning state
- Audit trail

## Release Model

### Release Group

Release Group is master data. It represents a release family or product/image line, not a deployable version.

Release Group owns:

- title/name
- registry URL
- image repository
- included apps, selected from `App` through `Release Group Apps`
- supported Frappe major version
- release policy
- active/inactive state

Release Group is used to:

- group Releases
- group Benches
- show release adoption by bench
- show benches behind latest release
- start create-release, promote-release, and rollout-planning workflows

### Release

Release is transactional. It represents a specific deployable image/version inside a Release Group.

Release owns:

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

Release is used to:

- select the exact image a Bench deploys
- track build, promote, block, and rollout lifecycle
- compare Bench current release vs next release
- audit what was built and deployed

### Bench

Bench is the runtime deployment group.

Bench owns:

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

Bench is used to:

- know which Release is currently deployed
- plan movement to the next Release
- schedule upgrades
- track SOP progress
- create operator-backed runtime resources

### Bench Upgrade Plan

Bench Upgrade Plan is a future transactional/control entity for platform-team SOP execution.

Bench Upgrade Plan owns:

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

## Notes

- Release Group is the release-family master data.
- Release is the deployable image/version.
- Bench is the unit of runtime grouping.
- Site is the tenant boundary.
- DNS must be treated as lifecycle state, not manual admin work.
