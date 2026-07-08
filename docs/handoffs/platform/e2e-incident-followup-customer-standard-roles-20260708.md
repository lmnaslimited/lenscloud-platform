# E2E Incident Follow-Up: Customer Standard Roles

Date: 2026-07-08  
Incident: `LC-E2E-20260708-002`  
Owner: Platform

## Problem

Fresh LensCloud Platform setup does not guarantee the standard customer roles and role profiles exist:

- `LensCloud Customer Admin`
- `LensCloud Customer Member`

Without these records, Platform Settings cannot select default customer role profiles and signup cannot assign the intended native RBAC profile.

## Required Fix

- Seed the two Roles and matching Role Profiles during Platform setup/migrate.
- Keep them idempotent and safe for existing installs.
- Ensure each Role Profile contains its matching Role.
- Add regression coverage in customer identity tests.
- Do not hardcode access checks in the UI; native Frappe roles and DocPerm remain authoritative.

## Retest

- Run `bench --site dev.localhost run-tests --module lenscloud.api.test_customer_identity`.
- Confirm the Role and Role Profile records exist after seeding.
- Close this incident only after evidence is recorded.
