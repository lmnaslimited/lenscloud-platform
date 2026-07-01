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
9. Confirm protected resource rules still hold:
   - `default/frappe-mariadb` is protected/read-only;
   - unlabelled, cross-namespace, cluster-scoped, and protected-resource operations are rejected.
10. Record the Platform evidence:
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
2. Open Customer Dashboard.
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
19. On mobile, confirm detail/inspector content is reachable through the Details drawer.
20. Confirm no customer screen exposes Kubernetes, namespaces, Benches, MariaDB, Database Server, Secrets, CR names, kubeconfig, pod logs, or action logs.

Expected result: a customer can understand what they bought, what happens next, and where to return, without learning platform runtime internals.

## Controlled Live Provisioning Segment

Run this only after the common preflight and both UI segments pass.

1. Capture current Customer, Subscription, Site, Bench, Database Server, and action-log inventory.
2. Enable Kubernetes apply only for the approved test window.
3. Submit one Free Plan customer Subscription through the customer UI.
4. Watch Platform action logs and customer progress until the Site reaches a terminal ready or failed state.
5. Verify the ready Site:
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
- `npm --prefix apps/lenscloud/frontend run build`
- authenticated desktop Playwright
- authenticated mobile Playwright

Browser validation must include console-error checks. Any customer-facing 403, missing route, hidden detail pane, or leaked platform runtime term is a stop condition.

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
