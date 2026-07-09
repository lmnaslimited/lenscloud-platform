# Customer Launch Progress Stall Follow-Up - 2026-07-09

## Incident

`LC-E2E-20260709-001` tracks customer launch progress stopping at `Preparing workspace` for CUST003 / SUB-00004 / `tarainnohub.cloud.lmnaslens.com` while the backend Site remained `provisioning_status=Accepted`, `route_status=Pending`, and the Site URL was manually reachable.

## Fix Path

1. Use nithu customer credentials from `/tmp/lenscloud_credential_file.json` keys `customer_nithu` and `customer_nithu_password`.
2. Open `/lenscloud/customer/plans?site=<Site>&subscription=SUB-00004` and verify the customer sees the launch timeline, not the dashboard.
3. Use the customer-safe refresh/retry action to call `retry_customer_site_provisioning`; for Accepted/Running/Ready Sites this must run `sync_site_status(check_route=True)` rather than only reconcile.
4. Confirm backend Site reaches `provisioning_status=Ready`, `route_status=Ready`, `tls_status=Ready` when the route check succeeds, or shows a customer-safe failed state if it does not.
5. Retest desktop and mobile progress states.

## Closure Evidence

Record the Site, Subscription, action log name, final Site statuses, and customer screenshot/probe result. Do not include credentials, pod logs, kubeconfig, secrets, or raw target Site config.
