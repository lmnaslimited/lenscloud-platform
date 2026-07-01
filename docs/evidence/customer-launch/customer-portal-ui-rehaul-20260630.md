# Customer Portal UI Rehaul Evidence - 2026-06-30

## Scope

Implement the Free-first customer portal UI from non-legacy Stitch artifacts under `docs/design/stitch_lenscloud_designs`. The flow must be wired to real Platform APIs and must not expose runtime internals to customers.

## Design Inputs

Used:

- `lenscloud_service_portal/DESIGN.md`
- `welcome_to_lenscloud`
- `choose_your_plan`
- `review_subscription`
- `setup_your_site`
- `free_checkout_confirmation`
- `launching_your_site`
- `provisioning_mobile`
- `provisioning_failed_retry`
- `dashboard_ready_mobile`
- `my_sites`
- `account_settings`
- `operator_dashboard` for Platform companion direction only

Ignored:

- every `legacy_*` folder.

## Implementation Notes

Implemented customer-facing UI surfaces from non-legacy Stitch artifacts:

- Customer Dashboard: state-aware launch home with `Choose a Plan`, `View progress`, or `Open Site` primary action depending on real context.
- Customer Plans: guided Plan selection, setup details, Free checkout summary, `₹0` due today, no payment method required, and real `request_customer_subscription` submission.
- Provisioning result: customer-safe progress labels for subscription approval, Site reservation, workspace preparation, HTTPS connection, and ready-to-open state.
- Customer Sites: customer-safe setup/access cards with Open Site and support actions; Bench/runtime details removed.
- Customer Account: profile and future CUA/access-management framing; linked Sites show status/access only.

Adapted Stitch details for production truth:

- Did not copy standalone Tailwind/CDN/Material Symbols code; translated layout into repo Vue + Frappe UI + lucide.
- Removed/avoided unsupported customer-facing backup/version/runtime details such as backup timestamps, software version cards, Bench, Database Server, Kubernetes, namespaces, Secrets, action logs, pod logs, and operator wording.
- Paid/beta Plans remain approval/request states; no fake card payment form was added.
- Free checkout is real UI copy and calls the current Platform subscription API; live payment integration is still future scope.

## Validation

```text
python3 -m py_compile lenscloud/api/orchestration.py lenscloud/api/test_policy.py
bench --site dev.localhost run-tests --module lenscloud.api.test_policy
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
```

Results:

```text
backend policy/context tests: 15 passed
frontend production build: passed
authenticated desktop Playwright: passed
authenticated mobile Playwright: passed
```

Build warnings were the existing Rollup PURE-comment and chunk-size warnings.

## Remaining Live Gate

The UI is wired to production Platform APIs, but the controlled live Free E2E acceptance still needs to run with apply enabled for the test window: Free subscription, real Site provisioning, HTTPS/static asset proof, action-log evidence, and cleanup/retention decision.

## Corrective Follow-Up - Guided Activity

User review found that the first implementation still rendered Plan choice, setup details, and checkout as stacked sections on one page. This does not meet the intended Stitch guided activity model.

Correction target:

- render exactly one customer activity screen at a time;
- use explicit next/back transitions from Choose Plan to setup, checkout, provisioning, and ready/open Site;
- preserve real backend wiring through `get_customer_portal_context` and `request_customer_subscription`;
- keep customer-facing runtime boundaries intact;
- rerun frontend build and authenticated customer Playwright after correction.

## Corrective Completion - Guided Activity

Completed the corrective interaction change after user review:

- `/customer/plans` now renders one active activity screen at a time instead of stacked Plan/setup/checkout sections.
- The activity flow is: Choose Plan -> Setup Site -> Free Checkout -> Provisioning/Approval result.
- Free Plan checkout remains wired to `request_customer_subscription`; Playwright stops at checkout confirmation and does not create a live subscription.
- Customer-visible copy remains limited to Plan, Subscription, Region, Site, workspace, setup, access, support, and progress.
- The inspector was adjusted so it does not duplicate the active step heading.

Corrective validation:

```text
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
```

Results:

```text
frontend production build: passed
authenticated desktop Playwright guided flow: passed
authenticated mobile Playwright guided flow: passed
```

## Focused Correction - Dashboard Journey Entry

User review found the dashboard still looked legacy/pale and did not use the Stitch design tokens strongly enough. This focused pass is limited to the customer dashboard entry state:

- if the customer has no Subscription, `/customer/dashboard` must render the journey start screen;
- if the customer has a Subscription, `/customer/dashboard` must render the subscribed service dashboard state;
- the primary CTA must use the supplied blue theme, with aligned icon/text and clear button affordance;
- later onboarding screens are intentionally out of scope for this focused correction.

## Dashboard Journey Entry Completion

Completed the focused dashboard entry correction:

- `/customer/dashboard` now branches on real customer Subscription state.
- No Subscription: renders a Stitch-token welcome/start screen with a clear `Choose a Plan` primary action using `#1D4ED8`, aligned icon/text, and an onboarding checklist.
- Existing Subscription: renders the subscribed service dashboard state with the appropriate `Open Site`, `View progress`, or `Continue setup` primary action.
- This pass intentionally changed only the dashboard journey start/subscribed state. Later onboarding screens remain separate UI passes.

Validation:

```text
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
```

Results:

```text
frontend production build: passed
authenticated desktop Playwright: passed
authenticated mobile Playwright: passed
```

## Visual Parity Check - Dashboard Entry

User requested apples-to-apples Playwright comparison against the non-legacy Stitch references. This pass adds screenshot evidence at matching reference viewports and records concrete visual gaps before the next UI correction.

Visual artifacts generated:

- `docs/evidence/customer-launch/screenshots/20260630-dashboard/report.md`
- `docs/evidence/customer-launch/screenshots/20260630-dashboard/report.html`
- `docs/evidence/customer-launch/screenshots/20260630-dashboard/desktop-welcome.png`
- `docs/evidence/customer-launch/screenshots/20260630-dashboard/mobile-welcome.png`

Playwright detected the current customer state as `welcome` for desktop and mobile, compared against `welcome_to_lenscloud/screen.png`, found primary CTA `Choose a Plan`, and reported no browser errors.

## Focused Correction - Dashboard Token Polish

Follow-up correction focuses only on the dashboard welcome/subscribed surfaces. It applies the Stitch token contract more directly without changing backend flow or later onboarding screens.

## Dashboard Token Polish Completion

Completed the focused dashboard token polish:

- Removed the competing customer header `Choose Plan` action so the journey start has one obvious primary CTA.
- Applied the supplied Stitch blue token `#1D4ED8` directly to the primary `Choose a Plan` action.
- Added LensCloud brand/start treatment, stronger white canvas, aligned icon/text CTA, compact onboarding checklist, and bordered white checklist rows.
- Kept the branch production-wired: no Subscription renders the welcome/start state; existing Subscription renders the subscribed dashboard state.

Validation after polish:

```text
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json node frontend/tests/customer-dashboard-visual.mjs
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
```

Results:

```text
frontend production build: passed
visual Playwright capture: passed; desktop/mobile welcome state; CTA Choose a Plan; browser errors none
authenticated desktop Playwright: passed
authenticated mobile Playwright: passed
```

Updated visual artifacts:

- `docs/evidence/customer-launch/screenshots/20260630-dashboard/report.md`
- `docs/evidence/customer-launch/screenshots/20260630-dashboard/report.html`
- `docs/evidence/customer-launch/screenshots/20260630-dashboard/desktop-welcome.png`
- `docs/evidence/customer-launch/screenshots/20260630-dashboard/mobile-welcome.png`

## Customer Self-Service Plan Catalog Completion

Completed the first-class customer Plan catalog pass:

- Extended `Plan` with portal visibility, draft preview, self-service, request-access, experimental, badge, sort order, and feature JSON fields.
- Made `Plan` submittable so customer-visible catalog behavior can prefer submitted product records.
- Added Plan validation for conflicting portal flags and customer-hidden runtime terms in feature JSON.
- Added idempotent `lenscloud.patches.seed_self_service_plan_catalog` and registered it in `patches.txt`.
- Seeded four first-class Plans using existing topology records:
  - `Free` / `tier-1-free`: submitted, default, portal visible, self-service.
  - `Tier 2 Growth`: submitted, portal visible, request access.
  - `Tier 3 Scale`: submitted, portal visible, request access, experimental.
  - `Tier 4 Enterprise`: submitted, hidden from customer portal.
- Updated `get_customer_portal_context()` to return only eligible customer Plans with feature JSON, CTA mode, derived environments, and isolation summary.
- Updated `request_customer_subscription()` so customer requests require an active, submitted, portal-published Plan and respect CTA mode.
- Rebuilt `/customer/plans` so the Plan cards are driven by first-class Platform Plans, with the default Plan centered and a customer-safe request/self-service CTA model.

Validation:

```text
bench --site dev.localhost migrate
python3 -m py_compile lenscloud/api/orchestration.py lenscloud/lenscloud/doctype/plan/plan.py lenscloud/patches/seed_self_service_plan_catalog.py
bench --site dev.localhost run-tests --module lenscloud.api.test_plan_catalog
bench --site dev.localhost run-tests --module lenscloud.api.test_policy
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json node frontend/tests/customer-plans-visual.mjs
```

Results:

```text
migration: passed
Plan catalog backend tests: 3 passed
existing policy/context tests: 15 passed
frontend production build: passed
authenticated desktop Playwright: passed
authenticated mobile Playwright: passed
Plans visual Playwright: passed; desktop/mobile capture; visible Plans Tier 2 Growth, Free, Tier 3 Scale; Tier 4 hidden; CTA Start Free Plan; browser errors none
```

Visual artifacts:

- `docs/evidence/customer-launch/screenshots/20260630-plans/report.md`
- `docs/evidence/customer-launch/screenshots/20260630-plans/report.html`
- `docs/evidence/customer-launch/screenshots/20260630-plans/desktop-plans.png`
- `docs/evidence/customer-launch/screenshots/20260630-plans/mobile-plans.png`

## Customer Plan Selection UI Refinement

User review found the first Plan catalog implementation functionally correct but visually overloaded. Required follow-up:

- remove redundant old/legacy Plan page elements around the catalog;
- remove the separate CTA panel below the cards;
- clicking a Plan card selects it and the card button itself changes to the correct CTA (`Start Free Plan`, `Request access`, or `Coming soon`);
- reduce card density by moving Sites and Environments into compact list rows;
- replace verbose isolation summary block with a customer-facing placement/privacy filter above the cards;
- use Stitch-like contrast: default/recommended Plan card is white and strongly highlighted while non-default cards sit on a softer gray background;
- on mobile, show the default Plan first instead of preserving desktop center order.

## Customer Plan Selection UI Refinement Completion

Completed the focused Plan selection UI refinement after user review:

- Removed redundant usage/old activity elements from the Plan choice surface.
- Removed the separate CTA panel below the cards.
- Clicking a Plan card selects it; the selected card button itself becomes the CTA (`Start Free Plan` or `Request access`).
- Compact Sites, Environments, and placement are now list rows instead of heavy boxed summaries.
- Replaced verbose isolation block with a customer-facing placement filter: All, Public, Private.
- Default/recommended Plan uses stronger white/blue highlight; non-default cards use softer gray treatment.
- Mobile rendered order places the default Free Plan first, while desktop keeps the Free Plan centered between Tier 2 and Tier 3.

Validation after refinement:

```text
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json node frontend/tests/customer-plans-visual.mjs
```

Results:

```text
frontend production build: passed
authenticated desktop Playwright: passed
authenticated mobile Playwright: passed
Plans visual Playwright: passed
desktop rendered Plan order: Tier 2 Growth, Free, Tier 3 Scale
mobile rendered Plan order: Free, Tier 2 Growth, Tier 3 Scale
Tier 4 Enterprise: hidden
primary CTA: Start Free Plan
browser errors: none
```

## Customer Plan Page Chrome Cleanup

User review found remaining legacy wrapper elements on `/customer/plans`:

- remove `Free-first guided launch`;
- remove `Choose your LensCloud Plan` and its helper text from the main content header;
- remove top-right `Refresh` and `Dashboard` actions for the customer Plan selection screen;
- move visual activity/progress steps into the right pane.

## Customer Plan Page Chrome Cleanup Completion

Completed the focused `/customer/plans` chrome cleanup after user review:

- Removed the redundant main-page launch wrapper content that repeated the old Free-first guided launch message.
- Removed the extra top-right `Refresh` and `Dashboard` actions from the customer Plan selection activity.
- Kept the Plan choice as the primary screen content and moved activity progress into the right inspector pane.
- Aligned visible step headings with the guided flow: `Set up your first Site` and `Confirm your Free subscription`.
- Strengthened the authenticated Playwright path so it waits for the generated hostname preview before moving from setup to checkout.

Validation after cleanup:

```text
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json node frontend/tests/customer-plans-visual.mjs
```

Results:

```text
frontend production build: passed
authenticated desktop Playwright: passed; Platform desktop; Customer passed
authenticated mobile Playwright: passed; Platform mobile; Customer passed
Plans visual Playwright: passed
desktop rendered Plan order: Tier 2 Growth, Free, Tier 3 Scale
mobile rendered Plan order: Free, Tier 2 Growth, Tier 3 Scale
primary CTA: Start Free Plan
browser errors: none
```

Current visual artifacts:

- `docs/evidence/customer-launch/screenshots/20260630-plans/report.md`
- `docs/evidence/customer-launch/screenshots/20260630-plans/report.html`
- `docs/evidence/customer-launch/screenshots/20260630-plans/desktop-plans.png`
- `docs/evidence/customer-launch/screenshots/20260630-plans/mobile-plans.png`

## Customer Setup And Review Stitch Mapping

New focused UI pass started on 2026-07-01.

Scope:

- Launch progress should mark completed steps with green check icons, current step in blue, and pending steps muted.
- `Setup Your Site` should map directly to `docs/design/stitch_lenscloud_designs/setup_your_site/screen.png` and `code.html`.
- `Confirm your Free subscription` should map closely to `docs/design/stitch_lenscloud_designs/review_subscription/screen.png` and the available Stitch checkout HTML structure in `free_checkout_confirmation/code.html`.
- Frappe UI primitives should be reused where compatible. Native `select`/`input` controls are allowed for the setup step because the supplied Stitch `code.html` depends on that exact input-group composition.

Frappe UI reuse/deviation note:

- Reused: `Button`, `Alert`, `Badge`, existing `WorkspaceLayout`, and existing customer-safe API data.
- Custom/native: exact Stitch setup card, native Region `select`, native subdomain input group, availability badge, stepper/checkmark geometry, review card layout, checkout total card, and Stitch-like spacing/color treatment because Frappe UI does not provide these complete wizard templates in this repo.

## Customer Setup And Review Stitch Mapping Completion

Completed the 2026-07-01 setup/review mapping pass:

- Launch progress now clearly marks completed steps with green check icons, highlights the current step in blue, and leaves pending steps muted.
- `Setup Your Site` was rebuilt from the supplied `setup_your_site/code.html`: centered white setup card, header, `Step 3: Region & Domain`, Region select, `https://` + subdomain + Platform domain input group, availability badge, Site Name field, and Back/Continue footer.
- `Confirm your Free subscription` was rebuilt against the `review_subscription` reference and the available `free_checkout_confirmation/code.html` structure: completed breadcrumb, selected Plan, Region, subdomain, `₹0` total due today, no-payment helper text, and a confirmation action card.
- The flow remains production-wired: Plan context comes from `get_customer_portal_context`; Region choices come from active Regions attached to active Clusters; the domain suffix comes from Platform Settings `root_domain`; and the final action still calls `request_customer_subscription`.

Frappe UI reuse/deviation record:

- Reused Frappe UI primitives: `Button`, `Alert`, `Badge`, plus existing `WorkspaceLayout` and existing API helpers.
- Reused LensCloud/Frappe-native patterns: left workspace plus right inspector, compact task cards, semantic badges, disabled primary actions until required setup fields are present, and customer-safe language.
- Custom/native layout was used for Stitch-specific composition only: supplied setup card structure, native Region select, native domain input group, green completed-step icons, review card layout, checkout pricing summary, and reference-matched blue/white/gray treatments. No separate UI framework was introduced.

Validation after mapping:

```text
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json node frontend/tests/customer-plans-visual.mjs
```

Results:

```text
frontend production build: passed
authenticated desktop Playwright: passed; Platform desktop; Customer passed
authenticated mobile Playwright: passed; Platform mobile; Customer passed
visual report: passed
Plan selection desktop: Tier 2 Growth, Free, Tier 3 Scale; CTA Start Free Plan; errors 0
Plan selection mobile: Free, Tier 2 Growth, Tier 3 Scale; CTA Start Free Plan; errors 0
Setup your Site desktop: CTA Continue to Review; errors 0
Review subscription desktop: CTA Start Free Subscription; errors 0
```

Current visual artifacts:

- `docs/evidence/customer-launch/screenshots/20260630-plans/report.md`
- `docs/evidence/customer-launch/screenshots/20260630-plans/report.html`
- `docs/evidence/customer-launch/screenshots/20260630-plans/desktop-setup-site.png`
- `docs/evidence/customer-launch/screenshots/20260630-plans/desktop-review-subscription.png`



## Customer Setup Exact Code Adaptation

After user review, the setup step was changed from a visual approximation to a direct adaptation of `docs/design/stitch_lenscloud_designs/setup_your_site/code.html`. The customer-visible setup now matches the supplied structure: `Setup Your Site`, `Step 3: Region & Domain`, Region select, segmented domain input, availability badge, Site Name, Back, and `Continue to Review`.

Production data mapping:

- Region options: active `Region` records attached to active `Cluster` records.
- Domain suffix: Platform Settings `root_domain`, displayed as the suffix in the segmented URL control.
- Internal customer/company value: derived from Site Name for this exact setup component so no extra non-Stitch field is shown.

Validation rerun:

```text
npm --prefix frontend run build
bench --site dev.localhost run-tests --module lenscloud.api.test_plan_catalog
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json node frontend/tests/customer-plans-visual.mjs
```

Results:

```text
frontend production build: passed
Plan catalog backend tests: 3 passed
authenticated desktop Playwright: passed; Platform desktop; Customer passed
authenticated mobile Playwright: passed; Platform mobile; Customer passed
visual report: passed
Setup your Site desktop: viewport 1600x1000; CTA Continue to Review; errors 0
Review subscription desktop: viewport 1376x768; CTA Start Free Subscription; errors 0
```

## Customer Review Subscription Exact Code Adaptation

After user review, the review step was changed from the earlier approximation to a direct adaptation of `docs/design/stitch_lenscloud_designs/review_subscription/code.html`.

Implemented mapping:

- Main heading: `Review Subscription`.
- Left card: `Order summary` with Plan, Region, and Subdomain rows using live customer flow data.
- Right card: `Price breakdown` with Plan price, Taxes, `Total due today`, `₹0`, `No payment method required for Free Plan`, `Start Free Subscription`, and `Cancel`.
- Right inspector for checkout step: `Your service`, `Checkout details`, and the self-provisioned Free Plan explanation from the Stitch reference.
- Customer dashboard no longer uses generic `/api/resource/Site`; it uses `get_customer_portal_context.sites` to avoid customer-facing 403 console errors.

Validation rerun:

```text
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json node frontend/tests/customer-plans-visual.mjs
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
```

Results:

```text
frontend production build: passed
authenticated mobile Playwright: passed; Platform mobile; Customer passed
visual report: passed
Review subscription desktop: viewport 1376x768; CTA Start Free Subscription; errors 0
authenticated desktop Playwright: passed; Platform desktop; Customer passed
```

## Customer Subscription Summary Screen

New focused pass started on 2026-07-01.

Scope:

- Add a customer sidebar `Subscriptions` menu entry.
- Add a card-led customer Subscription screen using `get_customer_portal_context`.
- Keep visual language aligned with `docs/design/stitch_lenscloud_designs/lenscloud_service_portal/DESIGN.md`.
- Avoid generic Platform list/detail behavior for customer subscriptions.
- Hide runtime/internal terms and show customer-safe Plan, status, Region, linked Sites, payment summary, and next action.

## Customer Subscription Summary Screen Completion

Completed the customer `Subscriptions` screen pass.

Implemented:

- Added `Subscriptions` to the customer sidebar.
- Added `/customer/subscriptions` with a service-card layout rather than the generic Platform list/detail page.
- Uses `get_customer_portal_context` for subscriptions, Plans, Sites, usage, and onboarding state.
- Empty state points to `Choose a Plan`.
- Subscription cards show Plan, status, Region, linked Site count, and next action.
- Detail inspector shows customer-safe Subscription, Plan, Region, Free Plan payment summary, and linked Sites.
- Hidden from the customer screen: Bench, Database Server, Runtime Namespace, Kubernetes, CR names, Secrets, action logs, kubeconfig.

Design notes:

- Aligned with `docs/design/stitch_lenscloud_designs/lenscloud_service_portal/DESIGN.md`: white cards on `#f7f9fb`, restrained borders, compact Inter typography, Frappe Blue for primary actions, Emerald only for completed/ready states.
- Used Frappe UI primitives (`Button`, `Alert`, `Badge`) plus existing `WorkspaceLayout`.
- Custom layout is limited to the customer card/detail composition because this is not a dense Platform list.

Validation:

```text
npm --prefix frontend run build
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth
```

Results:

```text
frontend production build: passed
authenticated desktop Playwright: passed; Platform desktop; Customer passed
authenticated mobile Playwright: passed; Platform mobile; Customer passed
```

## July 1 Customer Subscription Lifecycle Detail

Refined the customer subscription surface after user review. The customer sidebar no longer exposes a standalone `Sites` entry; Sites now appear only as outcomes inside the selected Subscription Landscape. Subscription records now carry `plan_frequency` and `next_renewal_date`, while Plan records carry `billing_frequency`. The customer portal context enriches subscriptions with Plan-specific payment copy and a Landscape environment sequence, including Site status/provisioning state and customer-safe release version labels when available.

Validation results for this pass:

```text
bench --site dev.localhost migrate: passed
bench --site dev.localhost run-tests --module lenscloud.api.test_plan_catalog: passed, 4 tests
npm --prefix frontend run build: passed
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth: passed, Platform desktop and Customer
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth: passed, Platform mobile and Customer
```

Implementation note:

- Initial migrate exposed a legacy `seed_free_plan()` bug where a submitted Plan with stale Table MultiSelect child rows was saved during `after_migrate`. The hook now skips submitted Plans; the current self-service Plan catalog seed remains the authoritative submitted-Plan path.

Expected customer behavior:

- Subscriptions page shows Plan/status/Region/Landscape/environment count.
- Right pane shows start/end dates, frequency, next renewal, payment summary, and Landscape progress.
- Free Plan payment copy is used only for Free Plans; request-access/paid Plans show approval/payment-managed copy.
- No Kubernetes, namespace, Bench, Database Server, CR, Secret, action log, pod log, or kubeconfig text is visible to customers.

## July 1 Mobile Workspace Inspector Access

Implemented the design-wide mobile inspector correction after mobile review found right-pane content was inaccessible below desktop widths. `WorkspaceLayout` now keeps desktop right-rail behavior and exposes the same inspector slot through a mobile bottom-sheet drawer opened by a persistent `Details` action. Authenticated mobile Playwright now opens the drawer on Platform Dashboard and Customer Subscriptions and asserts inspector-only content is reachable.

Validation results for this pass:

```text
npm --prefix frontend run build: passed
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth: passed, Platform desktop and Customer
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth: passed, Platform mobile and Customer; mobile test opened inspector drawer and verified inspector-only content
```

Implementation note:

- The mobile drawer trigger uses Frappe UI `Button`. The drawer close control is a native icon button with Frappe-style classes because the Frappe UI wrapper did not expose a deterministic accessible/test target in the teleported drawer.

## July 1 Customer Subscription-Led Navigation Cleanup

Cleaned the customer launch navigation after validation. The customer sidebar no longer exposes `Create Site`; Site creation remains available only through Plan/Subscription flow, with the legacy route retained for compatibility. Dashboard progress and setup CTAs now route to Subscriptions, the Subscription count card is interactive, Site count cards remain informational, and Subscriptions uses `Add New Subscription` as the Plan catalog CTA. The backend now returns per-customer Plan entitlement state and enforces exhausted Plan limits server-side; exhausted Plans remain visible but disabled in the catalog.

Validation results for this pass:

```text
bench --site dev.localhost run-tests --module lenscloud.api.test_plan_catalog: passed, 5 tests
npm --prefix frontend run build: passed
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json npm --prefix frontend run test:auth: passed, Platform desktop and Customer
LENSCLOUD_CREDENTIAL_FILE=/tmp/lenscloud_credential_file.json LENSCLOUD_VIEWPORT=mobile npm --prefix frontend run test:auth: passed, Platform mobile and Customer
```
