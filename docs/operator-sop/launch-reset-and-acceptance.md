# Launch Reset And Acceptance SOP

## Safety Rules

- Keep Kubernetes apply disabled except during an explicitly controlled reconcile window.
- Use Platform lifecycle APIs and the Python Kubernetes client only.
- Never use `kubectl` as a Platform runtime dependency.
- Never mutate or delete `MariaDB/default/frappe-mariadb`.
- Preserve operators, namespaces, CRDs, Traefik, wildcard TLS, RBAC, infrastructure Secrets, and PVCs not proven Platform-owned.
- Never print kubeconfig, token, password, Secret data, or private keys.

## 1. Capture Baseline

Record Platform revision, Infra handoff revision, Platform Settings apply state, direct database counts, Cluster permission preflight, and secret-safe runtime inventory. For each runtime owner record capture Cluster, namespace, kind, resource name, ownership labels, status, finalizers, and dependents.

Stop if access is denied, a protected operation is allowed, ownership labels do not match, or the API is unreachable.

## 2. Retire Runtime

For each exactly matched Platform-owned resource:

1. Request Site deletion from Platform.
2. Inspect and sync until the owner CR and attributable dependents are absent.
3. Request Bench deletion only after dependent Sites are absent.
4. Inspect and sync until absent.
5. Request platform-managed Database Server deletion only after attached Benches are absent.
6. Use its configured retention policy and verify attributable PVC behavior.
7. Retry only after correcting the failure recorded in Orchestration Action Log.

Do not delete unlabelled or unmatched resources. Record them for exact Infra cleanup.

## 3. Reset Tenant Data

Only after runtime absence is proven, delete obsolete test Customers, Sites, Benches, platform-managed Database Servers, Subscriptions, test runs, test requests, and obsolete test action logs. Preserve Cluster, Region, Runtime Namespace, Platform Settings, Release Group, Release, App, approved Plans/topology masters, and handoff evidence.

Run migration to reseed Environments, Site Control Profiles, Landscapes, Privacy Profiles, Free Plan mapping, and Workspace Sidebar.

## 4. Validate Launch Configuration

- One active Free Plan exists for each launch Release Group.
- Free uses Single Tier, Public, Prod, and the approved Release Group.
- Each launch Region has exactly one Ready Free Bench.
- Signup, wildcard root domain, Cluster health, and public capacity gates are green.
- Dashboard totals match direct database counts.
- Platform navigation is grouped and permission protected.

## 5. Fresh Free Journey

1. Sign up or use a fresh customer account.
2. Complete Customer linkage.
3. Select Free Plan and Region.
4. Enter a unique subdomain and review.
5. Submit once.
6. Observe product-level provisioning progress.
7. Verify HTTPS page and static asset success.
8. Confirm the customer never sees namespaces, CRs, Benches, MariaDB, Secrets, or kubeconfig data.

## 6. Sequential Topology Acceptance

Use a unique `run-YYYYMMDD-HHMM` prefix. Run Single, Two, Three, and Four Tier one at a time. Validate expected Environments, independent Bench/Database placement keys, cross-customer rejection, Prod/non-production database isolation, approval requirements, and current Bench Test/LATP gates. Clean each run through Platform before the next.

## 7. Browser Acceptance

Run authenticated desktop and mobile Playwright for Platform and customer flows. Fail on browser console errors. Cover dashboard counts/readiness, grouped sidebar, Free onboarding, provisioning/ready/failure recovery, Sites, Account, beta enrollment, and role isolation.

## 8. Close

Disable apply. Confirm no run-prefixed resources remain, protected MariaDB is Ready, and no unattributed PVC was touched. Update dated evidence, canonical workitems, and `docs/agent-handoff.md`.

## Child-Table Configuration Check

In Platform, select a Plan, Landscape, Site Control Profile, or Privacy Profile. Confirm the document editor opens below the list, can be resized or expanded, and moves to a dedicated editor view on mobile. Confirm child rows render as a grid with fixed row-number/primary/action columns, horizontal scrolling for remaining fields, typed controls, Link value help, Add, Duplicate, Remove, Up, and Down; Save must persist through reload. For a non-destructive smoke, change one grouping value on a Draft/test record, save and reload, then restore it and save again. Confirm the editor follows the DocType field order and renders Tab Break, Section Break, Column Break, Table, and Table MultiSelect fields. Release Group must show Image Family, Apps, and Included Apps with App value help. Active seeded policy edits affect new Subscription snapshots, so do not leave probe values behind.

