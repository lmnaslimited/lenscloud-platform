# LensCloud Platform Agent Matrix

## Purpose

This repo owns the product layer for the `lenscloud` app. The agent roles below keep the repo focused and make it easy to hand off to other agentic coders.

## Agent Roles

### Platform Product Agent
- customer identity and access
- subscriptions and plan logic
- customer site requests
- bench and site lifecycle
- DNS and Route53 automation
- backup, restore, and upgrade workflows
- customer portal and platform console

### UI/UX Agent
- Frappe UI structure
- customer portal vs platform console
- role-aware navigation
- status and progress views

### Operator Integration Agent
- Frappe Operator contract
- implemented vs scaffolded CRDs
- safe lifecycle usage
- prevent scope drift into runtime reconciliation

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

### Automation/Workflow Agent
- idempotent site creation
- DNS provisioning
- backups and restores
- upgrades
- retry and rollback behavior

### SOP/Docs Agent
- README quality
- requirements clarity
- runbooks
- release notes
- handoff readiness

