# Infra Return - Customer Site Creation App Installation Latency

Date: 2026-07-21
From: Infra
To: Platform
Status: Patched operator published, admitted, and live-tested

## Infra Commit Range

No Infra commit has been created in this pass. The operator patch is committed
and pushed in the adjacent `frappe-operator` repo.

```text
repo:   https://github.com/lmnaslimited/frappe-operator.git
branch: lenscloud-beta
commit: 1333c73a Add configurable site init job resources
image:  ghcr.io/lmnaslimited/frappe-operator@sha256:e22c78676cbfd87d9e8738763414be8f78eb2126d3cbb87c8f1b182a4ea9a4bf
```

## Live Finding

Retained Site:

```text
iron-monkey-0721113731.cloud.lmnaslens.com
```

Live Site state:

| Field | Value |
| --- | --- |
| Created | `2026-07-21T11:37:35Z` |
| BenchReady | `2026-07-21T11:37:35Z` |
| DatabaseReady | `2026-07-21T11:37:36Z` |
| Ready | `2026-07-21T11:43:04Z` |
| `spec.apps` | `erpnext`, `brandkit` |
| `status.installedApps` | `erpnext`, `brandkit` |
| `status.appInstallationStatus` | completed for 2 requested apps |

The retained init Job is gone:

```text
kubectl -n lenscloud-runtime-eu get job iron-monkey-0721113731-init
Result: NotFound
```

Therefore Infra cannot reconstruct database creation, new-site, ERPNext install,
Brandkit install, migrate, and final reconciliation timestamps from this Site.
The current operator does not persist those phase timings into FrappeSite status.

## Bottleneck

The original live operator image was:

```text
ghcr.io/vyogotech/frappe-operator:4.1.1
```

The operator source hard-codes FrappeSite init Job resources:

```text
requests: cpu=100m memory=1Gi
limits:   cpu=500m memory=1Gi
```

That single init Job runs `bench new-site` and installs `erpnext` plus
`brandkit`. The 329-second operator stage is consistent with real app install
work running under a half-core CPU limit.

## Upstream Check

Infra checked upstream before carrying the patch:

```text
git ls-remote --tags https://github.com/vyogotech/frappe-operator.git
Latest tag: refs/tags/v4.1.1
```

There is no tagged release newer than the live cluster image
`ghcr.io/vyogotech/frappe-operator:4.1.1`.

Fetched upstream `main` and inspected the current helper. It still hard-codes
FrappeSite init Job resources and does not expose Site init CPU/memory overrides
or phase telemetry:

```text
requests: cpu=100m memory=128Mi
limits:   cpu=500m memory=256Mi
```

The only visible post-`v4.1.1` upstream commits were Helm chart publication and
default image externalization. They do not address this latency issue.

## Optimization Published

Published operator patch:

- adds ConfigMap-driven Site init Job resource overrides:
  - `siteInitCPURequest`
  - `siteInitMemoryRequest`
  - `siteInitCPULimit`
  - `siteInitMemoryLimit`
- preserves current defaults when unset;
- supports both expected and live ConfigMap names:
  - `frappe-operator-config`
  - `frappe-operator-frappe-operator-config`
- wires the keys through the Helm chart;
- adds focused controller tests.

No new production default is selected by this patch. The operator keeps its
current defaults unless Infra sets the ConfigMap/Helm values during a deployment.

Live operator deployment:

```text
namespace:  frappe-operator-system
deployment: frappe-operator-controller-manager
pod:        frappe-operator-controller-manager-784dff44c7-rcdpl
state:      Running 2/2
```

Infra first tested a `1000m/2Gi` request with `2/3Gi` limits. The patch worked,
but the disposable init Pod could not schedule because the worker already had
`3100m/4000m` CPU requested. The failed disposable Site was deleted.

The successful live measurement profile is:

```yaml
operatorConfig:
  siteInitResources:
    requests:
      cpu: "250m"
      memory: "2Gi"
    limits:
      cpu: "2"
      memory: "3Gi"
```

Those values are not hard-coded into the operator and should not be treated as
the final production profile without a capacity decision.

## Verification

```text
GOCACHE=/private/tmp/lenscloud-go-build GOMODCACHE=/private/tmp/lenscloud-go-mod go test ./controllers
ok github.com/vyogotech/frappe-operator/controllers 1.312s
```

## Fresh Proof

Disposable Site:

```text
FrappeSite: infra-latency-07211351
host:       infra-latency-07211351.cloud.lmnaslens.com
apps:       erpnext, brandkit
```

Timing result:

| Metric | Value |
| --- | ---: |
| FrappeSite creation-to-Ready | 241s |
| Init Job start-to-complete | 240s |
| Init container runtime | 235s |
| Platform retained Site baseline | 329s |
| Reduction | 88s |

Final status:

```text
status.phase: Ready
status.installedApps: erpnext, brandkit
status.appInstallationStatus: Completed app installation for 2 requested app(s) - check logs for any skipped apps
```

The proof Site is retained for short-term inspection. Infra did not delete
Platform's retained Site `iron-monkey-0721113731`.

## Platform Return Actions

Platform should not delete `iron-monkey-0721113731` until it has finished its
own retained-site checks.

Rerun the full under-five-minute harness against the patched operator and
continue moving command cleanup outside the customer-critical path. The operator
patch proves an 88-second reduction, but the current 241-second operator stage
still leaves too little room if setup/OAuth remain near the previously observed
latencies.

If the full gate still fails, the viable next design path is a prepared
Site/database template using `spec.skipInit: true` with a valid prebuilt schema
and default apps.
