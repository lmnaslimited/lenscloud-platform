# Customer Setup Default Inputs Follow-Up - 2026-07-09

## Incident

`LC-E2E-20260709-004` tracks missing typed customer/setup-default capture for company, region, timezone, currency, and language before runner-backed `site_setup.complete`. The CUA architecture requires Platform to resolve setup inputs from server-side data and block bootstrap with a customer-safe message when required inputs are missing.

## Fix Path

1. Extend the customer setup flow and/or account/customer records with typed fields for required setup defaults.
2. Persist values server-side; do not pass browser-only ad hoc values directly to target Site APIs.
3. Update setup payload resolution for `site_setup.complete` to use Customer, Subscription, Plan, Site Control Profile, and Customer Member data as described in `docs/architecture/cua-site-bootstrap-sso-sequence.md`.
4. Show a customer-safe missing-input dialog/state and a Platform action-log entry when required defaults are incomplete.
5. Retest fresh Free Plan Site bootstrap through setup wizard completion.

## Closure Evidence

Record fields captured, server records updated, sanitized runner action logs, and target Site setup status.
