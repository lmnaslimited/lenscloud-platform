# Customer Self-Service Plan Catalog

Date created: 2026-06-30
Canonical workitem: `Customer self-service Plan catalog` in `docs/platform-workitems.md`.

## Purpose

After a customer clicks `Choose a Plan` from the dashboard welcome screen, LensCloud must show a customer-facing Plan selection activity based on first-class Platform `Plan` records. The screen should follow the non-legacy Stitch references:

- `docs/design/stitch_lenscloud_designs/choose_your_plan/screen.png`
- `docs/design/stitch_lenscloud_designs/choose_plan_mobile/screen.png`

The UI may adapt to the Platform shell, but Plan content, visibility, flags, and feature text must come from the Plan model and customer portal API, not hard-coded frontend arrays.

## Product Rules

- Plans are managed by Platform users as first-class `Plan` documents.
- Only submitted Plans are generally eligible for active customer portal display.
- Draft Plans may be shown only when an explicit Plan-level preview/portal flag allows it.
- Four plans should be seeded for the current tier model: Tier 1, Tier 2, Tier 3, and Tier 4.
- Tier 4 must not be visible in the customer portal for now.
- The default Plan must be visually centered/recommended in the customer Plan selection screen.
- Customer self-service availability must be configurable on the Plan.
- Request-access and experimental/beta treatment must be configurable on the Plan.
- Four Tier is not self-service at this stage.
- Plan cards must not expose Kubernetes, namespaces, Benches, MariaDB, Database Servers, Secrets, CR names, action logs, pod logs, or infrastructure internals.

## Proposed Plan Fields

Add product/customer-facing fields to `Plan`:

- `publish_in_customer_portal` Check: allows customer portal listing when other eligibility checks pass.
- `allow_self_service` Check: customers may subscribe directly when true and the Plan is otherwise available.
- `request_access_only` Check: customers see a request-access CTA; no immediate provisioning.
- `experimental` Check: shows experimental/beta treatment.
- `portal_badge` Data: short badge such as `Recommended`, `Popular`, `Beta`, `Request access`.
- `portal_sort_order` Int: deterministic display order.
- `portal_feature_json` Code/JSON: array of customer-facing features, initially shaped as `[{"icon":"...","feature":"..."}]`.

Existing fields remain authoritative for derived facts:

- `is_default`: default/recommended card and center placement.
- `is_free`, `monthly_price`: price/payment copy.
- `landscape`: environments/tier summary.
- `default_privacy_profile`, `allowed_privacy_profiles`: friendly isolation summary.
- `site_limit`, `subscription_limit`: usage limits.
- `availability`: Public/Beta/Invite Only/Retired state.
- `status`: Active/Inactive/Retired lifecycle state.

## API Rules

`get_customer_portal_context()` should return a customer-safe Plan catalog:

- include only portal-eligible Plans;
- include submitted Plans by default;
- include draft Plans only if their explicit preview flag allows it;
- exclude Tier 4 until its portal flag is enabled;
- sort by default Plan center/recommended treatment and `portal_sort_order`;
- return Plan feature JSON as structured data after validation/sanitization;
- derive customer-friendly environment/isolation summaries from Landscape and Privacy Profile;
- expose CTA mode: `self_service`, `request_access`, or `coming_soon`.

## Seed Plan Intent

Seed or migrate these four Plans from first-class Platform records:

- Tier 1 / Free or starter public Plan: visible, self-service, default, center card.
- Tier 2: visible if intended for customer awareness, request access unless self-service is explicitly enabled.
- Tier 3: visible if intended for customer awareness, request access unless self-service is explicitly enabled.
- Tier 4: configured as a Plan but not shown in customer portal yet.

Exact names, prices, feature JSON, Release Group, Landscape, and Privacy Profile links must be implemented from Platform data, not hard-coded in Vue.

## UI Rules

- `/customer/plans` should match the Stitch Plan selection references as closely as possible within the Platform shell.
- Desktop should use the `choose_your_plan` reference as the target.
- Mobile should use the `choose_plan_mobile` reference as the target.
- Use the supplied blue token `#1D4ED8` for primary actions.
- Default Plan is visually centered and recommended.
- Plan cards show customer-friendly outcomes: price, included Sites, environments, support/approval state, feature list, and friendly isolation summary.
- Plan cards never mention runtime implementation terms.
- CTA behavior comes from the Plan: subscribe, request access, coming soon, or disabled.

## Validation

- Migration/schema test confirms new Plan fields exist.
- Plan validation test covers portal visibility, draft/submitted rules, Tier 4 hidden behavior, default Plan ordering, and feature JSON parsing.
- API test confirms only eligible Plans are returned and no runtime terms/secrets leak.
- Frontend build passes.
- Authenticated Playwright captures Plan selection desktop/mobile screenshots.
- Visual report compares against `choose_your_plan/screen.png` and `choose_plan_mobile/screen.png`.

## Out Of Scope For This Pass

- Paid checkout implementation.
- Tier 4 customer portal launch.
- Subscribed dashboard visual parity evidence, which is intentionally deferred until after a real onboarding cycle creates a subscribed customer state.

## Guided Setup And Review UI Mapping

The customer Plan flow remains a production-wired guided activity. After Plan selection, the setup and review steps should track the non-legacy Stitch references:

- `docs/design/stitch_lenscloud_designs/setup_your_site/screen.png`
- `docs/design/stitch_lenscloud_designs/review_subscription/screen.png` and `code.html`

Implementation guidance:

- Launch progress must clearly mark completed steps with a green check icon, highlight the current step in blue, and leave future steps muted.
- Setup must keep customers focused on Region, Site name, company/project, subdomain, and optional notes. It must not expose Bench, Database Server, Runtime Namespace, Kubernetes, CR names, or action logs.
- Review must behave like a real Free checkout: selected Plan, Region, Site URL, price summary, `$0` total due today, and `No payment method required`.
- Use Frappe UI controls (`Button`, `Alert`, `Badge`) where they do not conflict with exact Stitch mapping. The `Setup Your Site` step intentionally uses native `select` and `input` controls from the supplied Stitch `code.html` so the Region/domain component matches the design exactly.


The `Review Subscription` step intentionally follows the supplied order summary, price breakdown, and checkout-details layout. Customer dashboard Site state must come from the customer-safe portal context, not generic `/api/resource/Site` calls.

## Customer Subscription Summary Screen

Customer users need a first-class `Subscriptions` menu entry, but the customer experience should not reuse the Platform list/detail model. Most customers are expected to have a small number of subscriptions, so the customer screen should use service cards with a focused detail panel. The customer sidebar should not expose a standalone `Sites` menu; Sites are contextual outcomes of a Subscription Landscape.

Design rules:

- Use the LensCloud Service Portal tokens from `docs/design/stitch_lenscloud_designs/lenscloud_service_portal/DESIGN.md`.
- Source data from `get_customer_portal_context` only: subscriptions, Sites, Plans, usage, and onboarding state.
- Show customer-safe fields: Plan, status, Region, Landscape, environment count, ready Site, and next action.
- Show lifecycle metadata in the detail panel: start date, end date when set, billing frequency, next renewal date, and Plan-specific payment copy.
- Payment copy must come from Plan/Subscription data. Free Plans may say `$0 due today` and `No payment method is required`; paid, beta, or request-access Plans must show approval/payment-managed copy instead.
- Replace flat `linked Sites` lists with a Landscape progression sequence. Each Landscape environment row shows the environment, Site status, provisioning status, access link when ready, and a customer-safe release/version label when available.
- Hide runtime terms: Bench, Database Server, Runtime Namespace, CR names, Kubernetes, Secrets, action logs, pod logs, kubeconfig, and raw operator resource names.
- Primary actions should be `Choose a Plan`, `View progress`, or `Open Site` depending on state.
- Use cards plus a compact detail panel. Do not use the generic Platform `ResourcePage` list/inspector for this customer screen.

## Subscription Billing Metadata

Plan owns the default commercial cadence through `billing_frequency`. Subscription snapshots that into `plan_frequency` and tracks `effective_from`, `effective_to`, and `next_renewal_date`. The initial implementation computes renewal from the Subscription effective date using Monthly, Quarterly, Yearly, or One Time rules. Future billing integration may replace the computed value with gateway-sourced renewal dates, but the customer UI should continue reading the Subscription snapshot first.

## Subscription-Led Customer Navigation

Customer Site creation is no longer a standalone customer menu path. Customers start from Dashboard, Plans, or Subscriptions; Site setup happens through a Subscription and its Landscape. The legacy `/customer/create-site` compatibility route may remain for old links while the sidebar omits `Create Site`.

Navigation and entitlement rules:

- Customer sidebar shows Dashboard, Plans, Subscriptions, and Account.
- Dashboard `View progress` and `Continue setup` route to `/customer/subscriptions`, not directly to Site detail.
- Dashboard Subscription count is interactive and opens `/customer/subscriptions`; Site count cards are informational only.
- Subscriptions page uses `Add New Subscription` for the Plan catalog CTA.
- Plan catalog receives customer-specific entitlement state from `get_customer_portal_context`.
- When a Plan's `subscription_limit` or `site_limit` is exhausted for the customer, the Plan remains visible but disabled with an explanatory limit message.
- The backend also enforces limits in `request_customer_subscription`; the UI is not the authority.
- Free Plan exhaustion is normally determined by the provisioned Site and one active Free subscription. An incomplete existing Free subscription can still continue toward Site setup.

