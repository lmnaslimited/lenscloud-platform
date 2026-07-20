# Platform And Customer E2E Acceptance SOP

## Purpose

Use this SOP to approve and run the next Free-first LensCloud launch acceptance pass. It separates Platform operator validation from Customer launch validation so failures can be assigned clearly and evidence stays clean.

This SOP validates the current production-wired Free Plan path. Paid checkout, remaining Bench Command runner families, advanced Central User Access, and the broad visual coherence redesign are not blockers for this pass unless they expose a customer-facing launch defect.

## Safety Rules

- Never expose kubeconfig, tokens, passwords, Secret values, private keys, pod logs, or full environment dumps.
- Do not delete or mutate `default/frappe-mariadb`.
- Do not create Kubernetes namespaces from Platform.
- Keep Kubernetes apply disabled except during an explicitly approved live provisioning window.
- Clean only resources that are proven Platform-owned test resources.
- Preserve Cluster, Region, Runtime Namespace, Release Group, Release, Plan, Landscape, Privacy, Site Control, and handoff data unless a test explicitly says otherwise.

## Common Preflight

Run this before Platform or Customer E2E.

1. Confirm the target site is reachable and the correct branch/revision is deployed.
2. Confirm migrations have run.
3. Confirm production frontend build passes.
4. Confirm authenticated desktop and mobile Playwright credentials are available without printing them.
5. Confirm Platform Settings:
   - signup is enabled for the test path;
   - root domain is configured;
   - Kubernetes apply is disabled before the live window;
   - restricted kubeconfig reference is server-side only.
6. Confirm product baseline:
   - Release Group and Release are approved;
   - active Cluster and Region exist;
   - approved Runtime Namespace is synced;
   - Free Plan is submitted, public/self-service, and default/recommended as intended;
   - Free Plan resolves to Single Landscape, Prod environment, Public Privacy Profile, and the approved release group;
   - one ready shared Free Bench exists for the target Region.
7. Stop immediately if readiness, RBAC, runtime namespace, root domain, Free capacity, migrations, build, or authenticated login fails.

8. Confirm customer RBAC baseline:
   - Platform Settings has Customer Admin and Customer Member Role Profiles configured, or the conventional `LensCloud Customer Admin` and `LensCloud Customer Member` Role Profiles exist;
   - Role Profiles carry native DocType permissions for Plan, Subscription, Site, and Customer Member as intended;
   - signup/member approval creates a Customer User Permission;
   - customer menus are expected to appear only when the current user's Role Profile grants DocType read permission.

9. Confirm Capability baseline:
   - Platform sidebar shows Tool, Skill, Capability, Subscription Capability, and Capability Policy entries under Product and Delivery;
   - Tool and Skill are first-class Platform DocTypes;
   - Capability bundle child tables use Link fields for App, Tool, and Skill;
   - at least one customer-visible Capability is seeded for marketplace testing, or record that the Marketplace empty state is the expected result for this pass.

## Platform Operator Segment

The Platform operator verifies the service can safely provision and observe the customer journey.

1. Sign in as a Platform operator.
2. Open the Platform dashboard and confirm launch readiness is understandable:
   - signup;
   - Free Plan;
   - wildcard/root domain;
   - public capacity;
   - cluster health;
   - failed provisioning or action-required queues.
3. Open Product and Delivery records:
   - Plan;
   - Landscape;
   - Environment;
   - Privacy / Privacy Profile;
   - Site Control Profile;
   - Release Group and Release.
4. Confirm only submitted/customer-visible Plans are exposed to the customer portal.
5. Confirm hidden or entitlement-exhausted Plans remain unavailable for customer provisioning.
6. Open Runtime records:
   - Cluster;
   - Region;
   - Runtime Namespace;
   - Database Server;
   - Bench.
7. Confirm customer-facing flows cannot select Bench, Database Server, Runtime Namespace, Secret, or CR names.
8. Confirm existing Customer, Subscription, Site, and Orchestration Action Log pages are visible to Platform users.
9. Confirm metadata-driven administration regressions:
   - Platform Settings opens directly as a singleton detail editor, with no list/new chrome, and respects DocType tabs, sections, and columns;
   - Platform Privacy opens from Product and Delivery and allows authorized list/create/edit;
   - Database Server and Bench create/edit label runtime placement as `Privacy`;
   - choosing a Region in Database Server creation auto-populates the read-only Cluster from the DocType `fetch_from` rule.
10. Confirm protected resource rules still hold:
   - `default/frappe-mariadb` is protected/read-only;
   - unlabelled, cross-namespace, cluster-scoped, and protected-resource operations are rejected.

12. Open Product and Delivery Capability records:
   - Tool;
   - Skill;
   - Capability;
   - Subscription Capability;
   - Capability Policy.
13. Create or inspect one Capability and confirm its Apps, Tools, and Skills child tables use Link value help, not free-text codes.
14. Confirm the Platform Site detail shows read-only Site Capability State and offers only governed actions: Sync Capability State, Install Capability, and Install Bootstrap Apps.
15. Confirm direct editing of Site Capability State rows is not used as a mutation path.

11. Record the Platform evidence:
   - Platform user;
   - timestamp;
   - Plan;
   - Region;
   - Free Bench;
   - readiness result;
   - action log IDs if any;
   - screenshots of readiness and relevant records.

Expected result: Platform has enough product, capacity, runtime, and audit visibility to support a Free customer launch without Infra intervention.

## Customer Segment

The Customer segment validates the launch experience and customer-safe language.

1. Sign up or sign in as a test customer through the native LensCloud flow.
2. For a fresh signup, confirm LensCloud automatically creates or links Customer identity before Plan selection:
   - first company-domain user becomes active Customer Owner;
   - same-domain later signup becomes Pending Customer Member;
   - legacy Customer without `primary_domain` does not capture a later signup by email domain;
   - Frappe account verification copy is not treated as LensCloud membership approval;
   - customer login lands at `/lenscloud/customer/dashboard`, not `/me`;
   - public email signup creates an individual Customer;
   - Platform users are not created through signup.
3. Confirm a customer-only signup lands on Customer Dashboard, while Platform users land on Platform Dashboard only when they hold Platform roles.
4. Open Customer Dashboard.
3. If no Subscription exists, confirm the dashboard shows one primary action: `Choose a Plan`.
4. If a Subscription exists, confirm the dashboard shows service state and routes progress to Subscriptions.
5. Open Plans.
6. Confirm Plan cards are backed by Platform Plan records, not hard-coded mock data.
7. Confirm the default Free Plan is visually emphasized and customer-friendly.
8. Confirm hidden Plans are not shown and exhausted Plans are visible but disabled with helpful copy.
9. Select the Free Plan.
10. Set up the Site:
    - choose Region from active Regions;
    - enter subdomain;
    - confirm the domain suffix comes from Platform Settings;
    - enter the Site display name if prompted.
11. Review the Subscription:
    - Plan;
    - Region;
    - Site/subdomain;
    - included features;
    - zero payment for Free Plan.
12. Confirm Free checkout:
    - `₹0 due today`;
    - no payment method required;
    - no fake paid checkout fields.
13. Submit the Free Subscription request.
14. Confirm the portal shows provisioning progress or ready state.
15. Open Subscriptions.
16. Confirm Subscription detail shows:
    - Plan;
    - status;
    - start/end/renewal/frequency when available;
    - Landscape environment progression;
    - Site status and ready URL where available.
17. Open Account.
18. Confirm Account focuses on identity, organization, access roadmap, support, and contact preferences; it must not duplicate Plan comparison or provisioning workflow.
19. Click the shell Account/profile chip and confirm the floating widget shows Profile, Change Password, and Sign Out.
20. From the widget, click Change Password and confirm the Account page opens a compact password dialog without navigating to `/update-password` or leaving the LensCloud workspace. Do not print passwords in evidence.
21. Confirm Sign Out is available only from the widget/menu surface, not as a noisy Account page header action.
22. On mobile, confirm detail/inspector content is reachable through the Details drawer and Account actions are reachable from the mobile account widget.
23. Confirm no customer screen exposes Kubernetes, namespaces, Benches, MariaDB, Database Server, Secrets, CR names, kubeconfig, pod logs, or action logs.

24. Confirm customer menu and action access follows native Frappe permissions:
    - granting Plan read makes the Plans menu visible and Plan records load;
    - removing Plan read hides the Plans menu and direct Plans access shows a permission state;
    - granting Customer Member read/write makes the Members menu and approval actions available;
    - removing Customer Member access hides the Members menu;
    - users without Subscription create can browse Plans if Plan read is granted, but cannot start a Subscription;
    - if Customer User Permission is missing, APIs still return only the Customer from active membership or legacy `Customer.user` and must not leak another Customer.


25. Open Customer Marketplace.
26. If Capability records are seeded, confirm Capability cards render from Platform data and customer action language is request/subscribe, not install app. Request one Capability for the test Subscription when the pass explicitly permits mutation.
27. If no Capability records are seeded, confirm the Marketplace empty state renders without browser errors and record that no-card state as expected for this dataset.
28. Confirm customer pages do not expose raw app install controls; apps remain implementation details behind Capability fulfillment.

Expected result: a customer can understand what they bought, what happens next, and where to return, without learning platform runtime internals.

Provisioning retry checks:

- With Kubernetes apply disabled, a Free Subscription submission may reserve the Site but must show a customer-safe paused state and `Retry Setup`, not a fake success.
- After Platform enables apply for the controlled window, `Retry Setup` must reuse the existing reserved Site and move the same Subscription/Site toward real provisioning.
- If retry fails, create an incident and keep the customer message free of action-log, namespace, Bench, Database Server, Secret, and Kubernetes terms.


## CUA Site Bootstrap And SSO Segment

Run this segment in slices as Infra publishes CUA runner gates. Shared sequence: `docs/architecture/cua-site-bootstrap-sso-sequence.md`.

Platform preflight:

1. Confirm Platform commit `c520b5a` or newer is present and `docs/handoffs/infra/cua-site-bootstrap-sso-runner-20260703.md` records `site_setup.status` and `site_setup.complete` as live-verified.
2. Confirm Infra runner supports `site_setup.status`, `site_setup.complete`, `oauth.status`, and `oauth.configure` before running setup/OAuth automation. Confirm `user.ensure`, `user.disable`, `user.roles.set`, and `site_access.status` remain Unsupported until INF-023 is complete.
3. Confirm Platform Settings has CUA OAuth defaults: `oauth_provider=lenscloud`, `oauth_provider_name=LensCloud`, and public `oauth_base_url` for the current LensCloud Platform URL, such as `http://dev.localhost:8000` in local/dev. Platform creates or reuses a Frappe `OAuth Client` per target Site. The redirect URI must be `<site.access_url>/api/method/frappe.integrations.oauth2_logins.custom/lenscloud`. The OAuth client secret must never be entered in UI/API args and is supplied only through a short-lived Kubernetes Secret during `oauth.configure`.
4. Confirm no Administrator password, OAuth client secret, bootstrap token, kubeconfig, Secret value, pod log, or raw `site_config.json` appears in Platform API responses or action logs.
5. Confirm Site Bootstrap State and Site Access Grant records exist or migrations are ready.

Positive customer path:

1. Create a fresh Free Plan Subscription and provision one Prod Site.
2. Wait for Site Ready.
3. Trigger setup status and setup completion through Platform.
4. Verify setup wizard is complete.
5. Trigger OAuth status through Platform. If `LC-E2E-20260707-001` is still Open, stop here and restore Kubernetes API reachability before continuing.
6. Trigger Configure OAuth through the dedicated Site action or `lenscloud.api.bench_command.configure_site_oauth`; do not use generic args for `oauth.configure`.
7. Verify target Site trusts LensCloud Platform as OAuth/Social Login provider and the runner returns a sanitized display/result summary.
8. Verify cleanup removed the command Job, request ConfigMap, terminal command Pod, and short-lived OAuth Secret.
7. Ensure the Customer Owner/Admin user on the target Site through Platform.
8. Verify Site Access Grant is Active.
9. Click `Open Site` from the customer Subscription page. The link must open the target Site URL, not the OAuth callback URL.
10. If the target Site still shows username/password login because Infra has not disabled password login yet, click `Login with LensCloud` and continue through Platform OAuth.
11. Verify the customer reaches the target Site desk without entering a Site-local password.
12. Add or approve a second Customer Member, grant Site access, and verify that member can open the Site through Platform SSO.
12. Revoke or disable the member and verify target Site access is denied.

Negative/security path:

- direct customer access to Bench, Database Server, runtime namespace, Secret, CR names, action logs, pod logs, and raw setup details remains hidden;
- unsupported runner command returns Unsupported;
- wrong Customer/Site/Subscription relation is rejected;
- unlabelled/wrong-namespace runner requests are rejected by Infra admission/RBAC;
- Platform never asks a customer or operator to paste a Site Administrator password into the browser.



Current setup-runner proof: 2026-07-06 live E2E completed setup wizard on kept Site `run-20260706-cua-134515.cloud.lmnaslens.com`. Use that Site for the OAuth/social-login runner pass instead of deleting it. After OAuth passes, keep the Site for INF-023 user/site-access validation unless cleanup is explicitly approved.

Evidence required:

- Subscription, Site, Customer Member, and Site Access Grant IDs;
- action log IDs for setup status, setup complete, OAuth status, OAuth configure, user ensure, access status, and revoke/disable;
- sanitized runner result summaries;
- screenshot or Playwright proof that `Open Site` enters without password dialog;
- negative security proof;
- cleanup proof;
- incident IDs for any failed step.

## Controlled Live Provisioning Segment

Run this only after the common preflight and both UI segments pass.

1. Capture current Customer, Subscription, Site, Bench, Database Server, and action-log inventory.
2. Enable Kubernetes apply only for the approved test window.
3. Submit one Free Plan customer Subscription through the customer UI.
4. Watch Platform action logs and customer progress until the Site reaches a terminal ready or failed state.
5. Verify the ready Site:

5a. Verify bootstrap app install and customer-visible stage cadence:
   - before site setup completion, Platform creates a `site_bootstrap.install_apps` action when Release Group apps are marked Install At Site Creation;
   - the action excludes `frappe`;
   - apps are rendered in install sequence;
   - retry skips already-installed apps and fails on real install errors;
   - a customer progress poll advances at most one major backend gate: workspace/route, bootstrap install, setup status, setup completion, final setup status, OAuth status/configure;
   - Site setup (`site_setup.status` / `site_setup.complete`) runs only after bootstrap install has succeeded or there are no bootstrap apps;
   - failed `site_setup.status` leaves Site setup in a terminal Failed state until an explicit Retry, and background/status polling must not loop;
   - generic runner commands such as `site_setup.status` mount only the Bench `sites` PVC at `/home/frappe/frappe-bench/sites` with `subPath: frappe-sites`; they must not mount `/home/frappe/frappe-bench/sites/assets`.
5b. Verify Site Capability State remains read-only and reflects Capability fulfillment/sync evidence only.
   - HTTPS route responds;
   - static asset returns HTTP 200;
   - customer dashboard and Subscription detail show ready/open state.
6. Capture:
   - Customer ID;
   - Subscription ID;
   - Site ID;
   - hostname;
   - Region;
   - Plan;
   - action log IDs;
   - HTTPS/static asset proof;
   - screenshots.
7. Disable Kubernetes apply after the run unless continued live operation is explicitly approved.
8. Decide cleanup:
   - keep the Site only if it is part of launch baseline;
   - otherwise delete through Platform lifecycle APIs and record cleanup evidence.

Expected result: Free Plan E2E provisions a real customer Site with customer-safe progress and Platform-safe audit evidence.

## Automated Validation

Run where applicable:

- `bench --site dev.localhost migrate`
- `bench --site dev.localhost run-tests --module lenscloud.api.test_plan_catalog`
- `bench --site dev.localhost run-tests --module lenscloud.api.test_policy`

- `bench --site dev.localhost run-tests --module lenscloud.api.test_capability_api`
- authenticated Platform route smoke for `/platform/tools`, `/platform/skills`, `/platform/capabilities`, `/platform/subscription-capabilities`, and `/platform/capability-landscape-policies`
- customer Marketplace desktop/mobile Playwright capture
- `npm --prefix apps/lenscloud/frontend run build`
- authenticated desktop Playwright
- authenticated mobile Playwright

Browser validation must include console-error checks. Any customer-facing 403, missing route, hidden detail pane, or leaked platform runtime term is a stop condition.

## Incident Handling

Create an incident entry in `docs/incidents/e2e-incident-tracker.md` for every failed or suspicious scenario before continuing to the next major segment. Use `docs/architecture/e2e-incident-management.md` for severity, required fields, and the recovery loop.

For this pass, incidents live in `docs/incidents/e2e-incident-tracker.md`. Dated evidence files must link to incident IDs. If an incident blocks launch, update `docs/platform-workitems.md` and keep the incident open until fix and retest evidence are recorded.

Every incident must also link a follow-up prompt under `docs/handoffs/platform/` or `docs/handoffs/infra/`. The follow-up prompt is the autonomous resume instruction: after the fix lands, the next agent must read it, retest the incident, close or update the tracker, update evidence/workitems, and continue from the next unpassed scenario instead of waiting for a manual reminder.

Required incident triggers:

- customer signup does not create/link Customer identity;
- same-domain signup is not pending or is granted active access without approval;
- customer-only user can access Platform routes;
- platform user is treated as customer signup;
- customer provisioning ends as dry run without clear paused/retry guidance;
- retry cannot reuse an already reserved Site;
- real Kubernetes apply is expected but no runtime resource is created;
- customer sees runtime internals;
- Platform cannot inspect Customer, Subscription, Site, Bench, or action-log evidence;
- protected resources are mutated or deletion scope is ambiguous;
- mobile hides required detail content;
- any test failure with no documented next action.

## Evidence Template

Create dated evidence under `docs/evidence/customer-launch/`.

Record:

- date and operator;
- app revision;
- Infra revision if live cluster behavior is involved;
- test customer email without password;
- Plan, Region, Subscription, Site, and hostname;
- Platform readiness result;
- customer screenshots;
- Platform screenshots;
- action log IDs;
- HTTPS/static asset result;
- Playwright/build/test results;
- cleanup result;
- open defects;
- go/no-go recommendation.

## Stop Conditions

Stop and assign before continuing if:

- Platform apply cannot be disabled or safely bounded;
- restricted Kubernetes permission preflight fails;
- Free Plan or Free Bench capacity is missing;
- root domain is missing or wrong;
- customer can see runtime internals;
- customer can choose runtime infrastructure resources;
- provisioning creates records without a Subscription;
- dashboard or Subscription links route to the wrong place;
- mobile hides required detail content;
- paid/beta Plan flow provisions runtime resources without approval;
- tests or build fail.
