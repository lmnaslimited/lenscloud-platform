# LensCloud Platform Agent Handoff

## Purpose

This repository is the product layer for the `lenscloud` app. It is Frappe-first, customer-facing, and role-aware.

## Agent Roles

- Platform Product Agent: owns customer lifecycle, subscriptions, site requests, and platform workflows.
- UI/UX Agent: owns Frappe UI structure and customer/platform navigation.
- Operator Integration Agent: ensures work matches the actual Frappe Operator contract.
- SOP/Docs Agent: keeps the repo handoff-ready and prevents scope drift.

## Skills To Associate

- `lenscloud-platform-sop`
- `frappe-ui-product`
- `frappe-operator-integration`
- `route53-automation`

## MCPs To Use

- Kubernetes MCP for operator and cluster inspection
- Route53 automation layer for DNS lifecycle work
- GitHub tooling for repo handoff and PRs

## Operator Truth

- `FrappeBench`, `FrappeSite`, `SiteBackup`, and `SiteRestore` are the implemented operator workflows to rely on.
- `SiteJob` is scaffolded and should not be treated as a production feature unless the codebase is explicitly updated to prove otherwise.

## Repo Boundary

- This repo owns the `lenscloud` app and product workflows only.
- Infra/bootstrap belongs in `lenscloud-infra`.
