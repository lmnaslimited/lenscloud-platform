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

## Multi-Cluster Runtime Target Model

LensCloud supports multiple active runtime clusters at the same time. Platform Settings does not select one global active deploy cluster.

### Cluster

Cluster is the registered runtime target used by Regions for deployment placement.

Cluster owns:

- cluster name
- linked Region
- provider and environment
- active/maintenance/disabled status
- manager host and Headlamp URL
- Kubernetes API/access reference
- operator namespace
- default runtime namespace
- default storage class
- default bench namespace pattern
- kubeconfig reference and credential reference, stored as server-side references only
- health status, last sync time, and last error

Cluster is used to:

- derive Bench placement from Region
- derive Site placement from Region
- keep Kubernetes details out of customer-facing UI
- provide the backend with a credential/reference boundary for future operator apply

### Region Placement

Region links to Cluster. Bench and Site deployment choose Region first, then derive Cluster from `Region.cluster`.

- Bench.region -> Region.cluster -> Bench.cluster
- Site.region -> Region.cluster -> Site.cluster
- Platform Settings keeps only global defaults and integration settings.

### Plan

Plan is commercial/product master data. The Free plan must exist for first customer self-service site creation.

### DNS Record

DNS Record tracks intended and applied DNS automation state. DNS is lifecycle state, not manual-only admin work.

A Site must not be marked DNS verified unless Route53 creation and verification actually succeed.

### Orchestration Action Log

Orchestration Action Log records every Bench, Site, and DNS orchestration attempt, including generated dry-run manifests and errors.

### Site Identity Derivation

Site `title` is derived control-plane identity, not user input. The platform derives it from the full hostname:

- Customer/operator provides `subdomain`.
- Platform Settings `root_domain` provides the default root domain for this pass.
- Site `domain` stores the root or approved domain only and is read-only in the Site document UI.
- Site `title` and document name are set to the full hostname `{subdomain}.{domain}`.
- `FrappeSite.spec.siteName` must use the same full hostname, not only the subdomain.
- Kubernetes/operator resource names remain slug-safe and may use the subdomain/operator resource field.
- Future approved-domain support may replace the Platform Settings root domain; customer custom-domain whitelisting is out of scope for this pass.
