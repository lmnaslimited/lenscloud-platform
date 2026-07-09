# Customer Progress Navigation Follow-Up - 2026-07-09

## Incident

`LC-E2E-20260709-002` tracks the customer `View progress` action on Subscriptions and Dashboard not opening the provisioning state. Refresh also caused the user to lose the launch timeline and land back on the dashboard/normal entry state.

## Fix Path

1. Use customer route URLs with `site` and `subscription` query parameters for progress links.
2. Ensure `/lenscloud/customer/plans?site=<Site>&subscription=<Subscription>` reconstructs launch progress from `get_customer_portal_context`.
3. Confirm the Subscriptions card `View progress` and Dashboard provisioning CTA both navigate to that URL.
4. Refresh the progress URL and confirm it remains on the launch timeline.

## Closure Evidence

Attach browser route assertions for desktop and mobile, plus a short note of the selected Site/Subscription used.
