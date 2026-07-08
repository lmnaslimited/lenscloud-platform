# LensCloud Product Topology Model

## Purpose

Plans describe the customer offer. A Subscription freezes the selected Plan's Landscape and Privacy Profile into an immutable policy snapshot. Runtime placement is derived from that snapshot; customers never choose a Bench, Database Server, namespace, or technical isolation primitive.

## Model

- **Environment**: ordered Dev, QA, Pre-Prod, or Prod master data.
- **Site Control Profile**: versioned Site behavior and promotion gates.
- **Landscape**: a versioned ordered set of Environment and Site Control Profile rows.
- **Privacy**: first-class privacy family master data, such as Public, Private Shared, or Private.
- **Privacy Profile**: submitted policy document linked to Privacy with independent Bench and Database boundaries per Environment.
- **Runtime Privacy**: Bench and Database Server runtime records store the resolved `Privacy` family (`Public`, `Private Shared`, or `Private`), not the `Privacy Profile` document. The profile is consumed during Plan/Subscription policy resolution and snapshotting; runtime placement and namespace filtering use the family value.
- **Plan**: Release Group, Landscape, allowed/default Privacy Profile, availability, and limits.
- **Subscription**: Customer, Plan, Region, approval state, immutable policy JSON, and policy hash.
- **Site**: belongs to one Subscription and Environment. Only one non-deleted Site is permitted per pair.
- **Environment Test Run**: policy-hash-bound Bench Test or LATP evidence used by promotion gates.

## Seeded Landscapes

| Landscape | Environments |
|---|---|
| Single Tier | Prod |
| Two Tier | QA, Prod |
| Three Tier | Dev, QA, Prod |
| Four Tier | Dev, QA, Pre-Prod, Prod |

Higher environments use stricter control profiles. Prod LATP is non-destructive. Dev and QA can share a database group while retaining separate Bench groups. Pre-Prod and Prod use separate database and Bench groups by default.

## Isolation Boundaries

A Privacy Profile contains Privacy Environment Rules. Each rule independently selects a Bench boundary and Database boundary from Platform, Customer, Subscription, Environment, Site, or Bench, plus a grouping key. Placement keys are generated from the immutable Subscription snapshot.

Seeded profiles:

- **Public**: Platform-pooled Bench and Database capacity.
- **Private Shared**: Customer boundary for Bench and Database capacity.
- **Private**: Subscription Bench capacity and Bench-bound Database capacity.

The customer sees a short isolation summary supplied by the Plan. They do not select these profiles during Free onboarding.

## Free And Beta Rules

- At most one active Free Plan exists per Release Group.
- Free resolves to Single Tier, Prod, and Public.
- Exactly one Ready Free Bench may serve a Plan and Region.
- Customer selection stops at Plan, Region, and Site/subdomain; placement selects capacity.
- Non-Free Beta enrollment creates a Pending Approval Subscription.
- Policy edits create a new version. Existing Subscriptions retain their snapshot until an audited upgrade.

## Promotion Gates

When enabled by the Site Control Profile, current successful Bench Test and LATP runs must match the Subscription policy hash and target Release. Production LATP permits non-destructive mode only.


## Submitted Policy Versioning

Subscription remains a regular DocType in the immediate launch path, but Subscription approval must move to native Frappe Workflow. Free Plan subscriptions self-approve through workflow rules. Two Tier and higher, beta, invite-only, or paid subscriptions move through configured approval levels, rejection, cancellation, and audited state transitions. Provisioning may only consume a Subscription state that the workflow marks as approved/provisionable.

Site Control Profile and Privacy are policy documents and should follow an ERPNext BOM-like pattern:

- Operators edit Draft records.
- Submitted records are immutable runtime policy versions.
- Changes are made by Amend/Create Version, not by editing the submitted record in place.
- `status` still controls business availability such as Active, Default, Retired, or Deprecated.
- Existing Subscriptions keep their stored policy snapshot and hash until an audited upgrade/resnapshot flow explicitly moves them to a newer submitted version.

Site Control Profile should be keyed by Environment plus a profile family/code. Environment owns the default active Site Control Profile for that Environment, and Landscape Environment rows auto-pick that default while still allowing another active submitted profile for the same Environment when the operator intentionally overrides it.

Privacy is now the stable family key. A submitted Privacy Profile links to one Privacy family and contains the environment rules for Bench and Database boundaries. Plan Allowed Privacy Profiles point to submitted Privacy Profile documents, while the Plan also stores the default submitted Privacy Profile. New Subscriptions snapshot the submitted profile selected by the Plan; older Subscriptions do not drift when a default profile changes.

The customer-facing offer should continue to hide these internals. Plans expose friendly isolation summaries; Platform operators manage submitted policy versions and defaults.

### Implemented Baseline

The Platform now keeps Subscription as a regular DocType while Site Control Profile and Privacy Profile are submittable policy documents. Privacy is first-class master data. Site Control Profile remains anchored by Environment and Profile Code. Privacy Profile is anchored by its linked Privacy and uses names such as `PP-Public-01`; separate integer version/status fields are not required for Privacy Profile. Defaults are unique per Environment or Privacy. Landscape rows can omit Site Control Profile and will resolve the submitted default for that Environment. Plan and Subscription policy resolution consume only submitted Privacy Profile and Site Control Profile documents, preserving immutable Subscription snapshots.

## Current Enforcement Boundary

Frappe validates and stores the model, snapshots, placement keys, approval states, uniqueness, and test gates. Runtime application of Site Control Profile settings must not be injected as invented FrappeSite CR fields.

The preferred runtime contract is an Infra/operator-provided Bench Command Job/API. Platform should submit an approved command, target Site, and typed arguments; the operator-side wrapper executes the command in the correct Bench/Site context and returns status, logs, and sanitized failure details.

Expected command families include:

- backup and restore operations, equivalent to supported `bench --site` backup/restore flows;
- maintenance mode toggles;
- developer mode toggles;
- site configuration updates;
- client/server script policy actions where supported by Frappe;
- CORS allowlist updates;
- Bench Test and LATP trigger/status operations.

The contract must be secret-safe, role-gated, namespace-scoped, idempotent where possible, and auditable. Platform remains responsible for policy resolution and deciding whether a command is allowed. Infra/operator remains responsible for the wrapper that safely executes the command against the runtime workload. Until that contract exists, Platform can validate and snapshot Site Control Profiles but cannot claim live runtime enforcement of those controls.


### CUA Setup And Site Access Inputs

Subscription topology now feeds CUA Site bootstrap. Landscape and Environment decide which Sites exist; Site Control/Profile defaults decide setup policy; Customer/Subscription data supplies company and first-user context; Privacy/Profile does not grant access by itself. Platform resolves these inputs and passes only a typed, secret-safe payload to the Bench Execute runner described in `docs/architecture/cua-site-bootstrap-sso-sequence.md`.

The setup/OAuth/member-sync runner contract is distinct from backup/restore/LATP runner families. Until Infra publishes the contract, Platform may model Site Bootstrap State and Site Access Grants but must mark live enforcement as runner-pending.

### Platform Integration Status

Platform consumes the INF-010/INF-011 Kubernetes Job/ConfigMap contract through the Python Kubernetes API only. `bench_test.status` remains the harmless verification smoke path. Infra verification is complete through revision `f3d8057`; Platform live smoke succeeded in action log `ORCH-2026-00137`, and Platform now integrates the pinned production runner for `maintenance_mode.*`, `developer_mode.*`, approved `site_config.*`, and `cors.allowlist.*` behind Site Control policy. Backup, restore, Bench Test trigger, and LATP remain `Unsupported` with `COMMAND_UNSUPPORTED` until their runner contracts are built.
