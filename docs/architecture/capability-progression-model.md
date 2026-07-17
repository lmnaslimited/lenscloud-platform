# Capability Progression Model

Date: 2026-07-16

LensCloud customers do not install raw Frappe apps. Customers request or subscribe to Capabilities. Platform resolves each Capability into the required apps, tools, skills, and progression policy, then fulfills it onto the appropriate Subscription Landscape and Site.

## Product Model

- `Capability` is product catalogue master data.
- `Capability App`, `Capability Tool`, and `Capability Skill` describe what the Capability bundles. `Capability Tool.tool` links to first-class `Tool`; `Capability Skill.skill` links to first-class `Skill`.
- `Subscription Capability` is the durable customer entitlement/progression record.
- `Capability Landscape Policy` controls whether the Capability can progress automatically, needs approval, is platform-managed, or is fulfilled at Site creation / after approval / after Bench upgrade / manual action.
- `Site Capability State` is read-only observed state on `Site`.

## Site Capability State

`Site Capability State` is an observation surface, not a mutation surface.

It answers: is this Capability active, pending, blocked, or failed on this Site?

It may include app evidence as JSON, but operators and customers must not edit the child rows directly. Changes must come from customer capability request actions, platform approval/fulfillment actions, command results, or cluster/runtime sync.

## Runtime Fulfillment

Capability app fulfillment uses the Site Bench Release Group and the active Release runtime image.

The runtime image is derived as:

```text
{Release Group.registry_url}/{Release Group.image_repository}@sha256:{Release.image_digest}
```

`lens-pure` is the current launch Release Group, not a platform constant.

## Customer Flow

1. Customer opens Marketplace.
2. Customer requests/subscribes to a Capability for a Subscription.
3. Platform creates or updates `Subscription Capability`.
4. Platform policy decides whether the request is self-service, approval-required, or platform-managed.
5. Fulfillment runs through app-aware Infra jobs when apps must be installed.
6. Customer sees friendly Capability status on the Subscription/Site surface.

## Platform Flow

1. Platform defines Capability bundle rows.
2. Platform defines Capability Landscape Policy rows.
3. Platform approves or fulfills Subscription Capability records.
4. Platform runs app-aware `site_app.install` only from a Capability fulfillment action.
5. Platform syncs Site Capability State from command results or runtime status.

## Non-goals

- Do not expose customer raw app install controls.
- Do not allow direct edits to Site Capability State rows.
- Do not hardcode a single runtime image repository for all Release Groups.
