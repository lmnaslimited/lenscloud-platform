# LensCloud Platform State Model

## Core Entities

- Customer
- Subscription
- Release Group
- Bench
- Site
- DNS Record
- Backup
- Restore
- Upgrade

## Supporting Concepts

- Region
- Environment
- Tenant placement
- Approval state
- Provisioning state
- Audit trail

## Notes

- Release group is the unit of bench image management.
- Bench is the unit of runtime grouping.
- Site is the tenant boundary.
- DNS must be treated as lifecycle state, not manual admin work.

