# LensCloud Platform Agent Matrix

## Purpose

This repo owns the product layer for the `lenscloud` app. The agent roles below keep the repo focused and make it easy to hand off to other agentic coders.

## Agent Roles

### Platform Product Agent
- customer identity and access
- subscriptions and plan logic
- customer site requests
- bench and site lifecycle
- wildcard hostname and route lifecycle
- backup, restore, and upgrade workflows
- customer portal and platform console
- validate state-model alignment and mark missing backend behavior as gaps

### UI/UX Agent
- Frappe UI structure
- customer portal vs platform console
- role-aware navigation
- status and progress views
- shell, list/detail, and action-entry patterns

### Operator Integration Agent
- Frappe Operator contract
- implemented vs scaffolded CRDs
- safe lifecycle usage
- prevent scope drift into runtime reconciliation
- keep action surfaces aligned with `lenscloud-infra`

### Data/Model Agent
- customer
- subscription
- release group
- bench
- site
- DNS record
- backup
- restore
- upgrade
- state-model naming and compatibility

### Automation/Workflow Agent
- idempotent site creation
- DNS provisioning
- backups and restores
- upgrades
- retry and rollback behavior
- lifecycle action ordering and failure handling

### SOP/Docs Agent
- README quality
- requirements clarity
- runbooks
- release notes
- handoff readiness
- phase order, stop points, and work-item traceability

## Phase Mapping

- Handover Object 1: UI/UX Agent + Platform Product Agent
- Handover Object 2: UI/UX Agent
- Handover Object 3: Platform Product Agent + UI/UX Agent
- Handover Object 4: Platform Product Agent + UI/UX Agent
