# Customer Standard Roles Evidence

Date: 2026-07-08  
Incident: `LC-E2E-20260708-002`

## Result

Fixed and retested.

## Changes Verified

- Fresh Platform setup/migrate seeds standard customer Roles:
  - `LensCloud Customer Admin`
  - `LensCloud Customer Member`
- Matching Role Profiles are also seeded with their matching Role rows.
- The stale duplicate `after_migrate = lenscloud.setup.seed_defaults` hook was removed; `lenscloud.setup.after_migrate` is the single active setup hook and now calls customer role-profile seeding.

## Validation

- `bench --site dev.localhost run-tests --module lenscloud.api.test_customer_identity` passed: 11 tests.
- New regression test: `test_standard_customer_role_profiles_are_seeded`.
