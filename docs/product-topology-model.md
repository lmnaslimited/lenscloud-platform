# LensCloud Product Topology Model

## Purpose

Plans describe the customer offer. A Subscription freezes the selected Plan's Landscape and Privacy Profile into an immutable policy snapshot. Runtime placement is derived from that snapshot; customers never choose a Bench, Database Server, namespace, or technical isolation primitive.

## Model

- **Environment**: ordered Dev, QA, Pre-Prod, or Prod master data.
- **Site Control Profile**: versioned Site behavior and promotion gates.
- **Landscape**: a versioned ordered set of Environment and Site Control Profile rows.
- **Privacy**: a versioned profile with independent Bench and Database boundaries per Environment.
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

A Privacy Environment Rule independently selects a Bench boundary and Database boundary from Platform, Customer, Subscription, Environment, Site, or Bench, plus a grouping key. Placement keys are generated from the immutable Subscription snapshot.

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

## Current Enforcement Boundary

Frappe validates and stores the model, snapshots, placement keys, approval states, uniqueness, and test gates. The installed Frappe Operator CRD does not currently expose the complete typed Site configuration, developer-mode, script, or CORS contract. Those settings must not be injected as invented CR fields. Runtime application remains a production gap requiring an explicit operator contract.
