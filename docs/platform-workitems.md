# LensCloud Platform Workitems

## Purpose

This document tracks the overall LensCloud platform work across product, backend, infrastructure, operations, and local developer runtime. It complements the frontend handover tracker in `agent-handoff.md`; it does not replace that UI-specific tracker.

Status values:

- `Complete`: implemented and validated for the current scope.
- `Next`: the next logical work item.
- `Pending`: planned but not started.
- `Blocked`: cannot proceed without an external dependency, decision, or credential.

## Workitem Tracker

| Workstream | Work Item | Owner / Agent | Source Repo | Expected Outcome | Priority | Status |
|---|---|---|---|---|---|---|
| Requirements and Control | Keep product requirements, state model, workflows, agent docs, skills, and MCP docs aligned | SOP/Docs Agent | `lenscloud-platform` | Repo remains handoff-ready for agentic coders | P0 | Complete |
| Requirements and Control | Maintain this platform-wide workitem tracker as the cross-repo source of truth | SOP/Docs Agent | `lenscloud-platform` | Platform work can be tracked without mixing it into the frontend tracker | P0 | Complete |
| Requirements and Control | Use the repo-local Frappe UI product skill for frontend implementation and review | UI/UX Agent | `lenscloud-platform` | UI work follows Frappe-native patterns without introducing a bespoke design system | P0 | Complete |
| Product UI | Platform console and customer portal P0 shell | UI/UX Agent | `lenscloud-platform` | Role-aware Frappe UI surfaces for platform and customer users | P0 | Complete |
| Product UI | Release Group and Release model surfaced in UI | Platform Product Agent | `lenscloud-platform` | Release Group is master data; Release is deployable transactional version | P0 | Complete |
| Product UI | Operator-readiness fields surfaced for Bench, Site, and Platform Settings | Operator Integration Agent | `lenscloud-platform` | Product records can map to Kubernetes/operator resources | P0 | Complete |
| Product Backend | Define cluster registration model in LensCloud | Platform Product Agent + Infra Bootstrap Agent | `lenscloud-platform` | Platform can store cluster name, region, provider, Headlamp URL, operator namespace, storage class, namespace pattern, and credential reference | P0 | Complete |
| Product Backend | Add Cluster doctype and Region-driven placement model | Platform Product Agent + Infra Bootstrap Agent | `lenscloud-platform` | Regions determine Cluster for Bench and Site placement; Platform Settings is global defaults only | P0 | Complete |
| Product Backend | Add Free Plan self-service path | Platform Product Agent | `lenscloud-platform` | Customer create-site can use a real Free plan record without billing integration | P0 | Complete |
| Product Backend | Add legacy DNS Record and status model | Platform Product Agent | `lenscloud-platform` | Existing model remains available for compatibility/custom domains but is bypassed for wildcard Sites | P2 | Complete |
| Domain Edge | Adopt `cloud.lmnaslens.com` wildcard hostname model | Platform Product Agent + Infra Bootstrap Agent | Both | Standard Sites require hostname reservation and routing only, not per-Site DNS/certificates | P0 | Complete |
| Domain Edge | Replace standard Site DNS queue with wildcard route readiness | Platform Product Agent + Operator Integration Agent | `lenscloud-platform` | Customer/platform Site creation does not create DNS Record documents or call any DNS provider | P0 | Complete |
| Domain Edge | Add wildcard DNS/TLS/ingress readiness to Platform Settings and Cluster summaries | Data/Model Agent + UI/UX Agent | Infra wildcard handoff | Operators can see shared edge health without exposing provider credentials | P0 | Complete |
| Domain Edge | Confirm no DNS provider API dependency in Phase 1 platform | Platform Product Agent + SOP/Docs Agent | Wildcard edge contract | Platform dependencies and Site onboarding contain no DNS provider SDK/API calls | P0 | Complete |
| Domain Edge | Consume wildcard edge readiness | Platform Product Agent + Infra Bootstrap Agent | Infra Cluster handoff | Operators can distinguish wildcard DNS, TLS, ingress, and route readiness without GoDaddy credentials | P0 | Pending |
| Domain Edge | Add route reconciliation/status for each Site hostname | Operator Integration Agent | Frappe Operator/Traefik routing contract | Site becomes accessible after runtime and route readiness | P0 | Complete |
| Product Backend | Add safe backend dry-run orchestration methods | Operator Integration Agent | `lenscloud-platform` | Bench/Site manifests can be generated from Region-derived Cluster without Kubernetes apply | P0 | Complete |
| Product Backend | Derive Site identity from wildcard hostname and use it in FrappeSite manifest | Platform Product Agent + Operator Integration Agent | `Site.subdomain`, `Platform Settings.root_domain`, Frappe Operator `FrappeSite.spec.siteName` | Site identity is `{subdomain}.cloud.lmnaslens.com`; no per-Site DNS Record is required | P0 | Complete |
| Database Runtime | Define Database Server first-class model and operator contract | Platform Product Agent + Operator Integration Agent | Both | Database Server owns Region/Cluster, privacy, MariaDB runtime mapping, capacity, and Bench attachments | P0 | Complete |
| Database Runtime | Add Database Server DocType and platform workspace | Data/Model Agent + UI/UX Agent | `lenscloud-platform` | Platform team can create, register, inspect, and manage database capacity | P0 | Complete |
| Database Runtime | Add Database Server link and compatibility validation to Bench | Platform Product Agent + Operator Integration Agent | `lenscloud-platform` | Bench selects a compatible database server by Region, Cluster, privacy, owner, readiness, and capacity | P0 | Complete |
| Database Runtime | Add MariaDB CR dry-run and orchestration log actions | Operator Integration Agent | Both | Platform generates secret-safe MariaDB manifests and records every attempt | P0 | Complete |
| Database Runtime | Add `FrappeBench.spec.dbConfig.mariadbRef` to Bench dry-run | Operator Integration Agent | Database Server and Bench models | Multiple Benches can intentionally reference the same eligible MariaDB CR | P0 | Complete |
| Database Runtime | Register live EU `frappe-mariadb` as first Database Server | Platform Product Agent + Infra Bootstrap Agent | Live EU cluster handoff | EU shared MariaDB is visible and selectable in LensCloud | P0 | Complete |
| Database Runtime | Validate two Benches sharing one Public Database Server | Operator Integration Agent | EU Database Server registration and dry-run/apply path | Two Bench manifests reference the same MariaDB CR and Sites receive separate logical databases | P0 | Pending |
| Product Backend | Wire real Kubernetes apply through server-side credential references | Operator Integration Agent | `lenscloud-platform` | Platform backend can apply FrappeBench/FrappeSite after credentials and flags are configured | P0 | In Progress |
| Product Backend | Receive restricted EU kubeconfig artifact from Infra | Infra Bootstrap Agent + Operator Integration Agent | `lenscloud-infra/docs/platform-restricted-access-contract.md` | Platform backend receives a least-privilege mounted kubeconfig and only stores its server-side file reference | P0 | Complete |
| Product Backend | Define secure Kubernetes credential reference model | Operator Integration Agent | `lenscloud-platform` | Platform backend can use the mounted restricted kubeconfig without exposing content to frontend users | P0 | Complete |
| Product Backend | Implement Bench create/reconcile API backed by `FrappeBench` | Platform Product Agent + Operator Integration Agent | `lenscloud-platform` | Creating a Bench in LensCloud creates or updates the operator resource | P0 | Complete |
| Product Backend | Implement Site create/reconcile API backed by `FrappeSite` | Platform Product Agent + Operator Integration Agent | `lenscloud-platform` | Creating a Site in LensCloud creates or updates the operator resource | P0 | Complete |
| Product Backend | Implement status sync for cluster, bench, site route/TLS, backup, restore, and upgrade state | Automation/Workflow Agent | `lenscloud-platform` | LensCloud reflects real runtime state instead of only UI placeholders | P0 | In Progress |
| Product Backend | Add auditable platform job records for lifecycle actions | Automation/Workflow Agent | `lenscloud-platform` | Operators can see who triggered what, when, with outcome and logs | P1 | Pending |
| EU Runtime Cluster | Two-node Hcloud EU K3s cluster | Infra Bootstrap Agent | `lenscloud-infra` | One manager and one worker running K3s with workloads on worker | P0 | Complete |
| EU Runtime Cluster | Headlamp exposed for EU operations | Infra Bootstrap Agent | `lenscloud-infra` | `headlamp.cloud.lmnaslens.com` loads over wildcard HTTPS and can manage the EU cluster | P0 | Complete |
| EU Runtime Cluster | Move Headlamp under wildcard edge | Infra Bootstrap Agent | GoDaddy wildcard and Traefik TLS | `headlamp.cloud.lmnaslens.com` loads with the shared wildcard certificate | P1 | Complete |
| EU Runtime Cluster | MariaDB Operator and Frappe Operator installed | Operator Integration Agent | `lenscloud-infra` | Operators are healthy and CRDs are available | P0 | Complete |
| EU Runtime Cluster | Smoke MariaDB, FrappeBench, and FrappeSite | Operator Integration Agent | `lenscloud-infra` | One bench and one site prove the operator contract | P0 | Complete |
| US Runtime Cluster | Repeat the EU pattern for US | Infra Bootstrap Agent | `lenscloud-infra` | US cluster can be registered and managed by LensCloud | P1 | Pending |
| Multi-Cluster Operations | Manage EU and US through one LensCloud control plane | Platform Product Agent + Infra Bootstrap Agent | Both | Platform can select cluster/region target for Bench and Site lifecycle | P0 | Pending |
| Multi-Cluster Operations | Evaluate one central Headlamp instance vs per-cluster Headlamp | Infra Bootstrap Agent | `lenscloud-infra` | Platform team has a clear UI model for multi-cluster operations | P1 | Pending |
| Local Docker Runtime | Define Docker-only local K3s runtime architecture | Infra Bootstrap Agent + SOP/Docs Agent | `lenscloud-infra` | Local dev setup uses Docker Desktop only; no host kubectl, helm, k3d, or hcloud install | P1 | Pending |
| Local Docker Runtime | Build local tools container with Docker CLI, k3d, kubectl, and helm | Infra Bootstrap Agent | `lenscloud-infra` | Platform team can bootstrap local clusters through containerized commands | P0 | Pending |
| Local Docker Runtime | Create local K3s-in-Docker cluster profile | Infra Bootstrap Agent | `lenscloud-infra` | Local manager/worker containers mimic the Hcloud K3s topology closely enough for tests | P0 | Pending |
| Local Docker Runtime | Install Headlamp for local operations UI | Infra Bootstrap Agent | `lenscloud-infra` | Local users manage the cluster through a browser UI, similar to the old Portainer habit | P0 | Pending |
| Local Docker Runtime | Install operators and run smoke manifests locally | Operator Integration Agent | `lenscloud-infra` | Local Docker runtime proves the same MariaDB/Frappe operator workflows | P0 | Pending |
| Local Docker Runtime | Package a standalone dev-team runtime SOP | Release/SOP Agent | `lenscloud-infra` | Dev teams can recreate a standalone environment on Docker Desktop | P0 | Pending |
| DNS Automation | Manual EU Headlamp DNS | Infra Bootstrap Agent | `lenscloud-infra` | First DNS record is manually managed for speed | P0 | Complete |
| Domain Edge | Retire DNS-provider assumptions from normal customer onboarding | SOP/Docs Agent + Platform Product Agent | Wildcard model | No per-Site DNS propagation or certificate job remains in standard workflow | P0 | Pending |
| Domain Edge | Define multi-region wildcard origin routing | Infra Bootstrap Agent + Platform Product Agent | EU and future US ingress endpoints | Shared wildcard routes each hostname to its Region-selected Cluster | P0 | Pending |
| Storage and Database HA | Define shared file storage architecture | Infra Bootstrap Agent | `lenscloud-infra` | NFS or equivalent RWX is used only for Frappe shared files | P1 | Pending |
| Storage and Database HA | Define database HA architecture | Infra Bootstrap Agent + Operator Integration Agent | `lenscloud-infra` | Database HA is designed separately from NFS shared files | P1 | Pending |

## Local Docker Runtime Requirement

The platform team needs a local standalone runtime that feels as convenient as the earlier Docker Swarm model with Portainer and Traefik stacks.

Constraints:

- Docker Desktop is the only host prerequisite.
- No host install of `kubectl`, `helm`, `k3d`, `kind`, `hcloud`, or package managers.
- Kubernetes commands must run inside a repo-provided tools container.
- The local runtime must be reproducible from repo commands and SOPs.
- The local runtime must not require Hcloud, public DNS, or cloud credentials.
- The local runtime should expose a browser UI for cluster operations.

Preferred local approach:

- Use a `lenscloud-local-tools` container that mounts the Docker socket.
- Put Docker CLI, k3d, kubectl, and helm inside that tools container.
- Use k3d to run K3s inside Docker containers.
- Install the same operator stack used in the EU cluster.
- Expose Headlamp locally for cluster management.
- Keep Portainer optional for Docker container visibility, not as the Kubernetes source of truth.
- Prefer ingress-nginx for parity with the EU runtime unless a Traefik profile is explicitly added later.

Target local flow:

1. Start the tools container from `lenscloud-infra`.
2. Create a local k3d cluster with one server and one worker.
3. Install ingress, Headlamp, MariaDB Operator, and Frappe Operator.
4. Run the same smoke MariaDB, Bench, and Site manifests.
5. Open Headlamp in the browser and manage the local cluster from the UI.

## Immediate Next Work

1. Add Database Server DocType and platform workspace.
2. Register the live EU `frappe-mariadb` runtime through non-secret handoff values.
3. Attach Bench to Database Server and add `FrappeBench.spec.dbConfig.mariadbRef`.
4. Add MariaDB CR dry-run, validation, status, and orchestration logs.
5. Validate Public, Private Shared, and Private placement and rejection rules.
6. Replace per-Site DNS queueing with wildcard route readiness and ingress/TLS inheritance.
7. Run the restricted EU permission preflight before each controlled live test.
8. Enable idempotent real Kubernetes apply and status synchronization.
9. Complete platform-team and customer Free Plan Site creation over wildcard HTTPS.
