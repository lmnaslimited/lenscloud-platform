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


## Migration Lock Reopen

The platform team reported a fresh `bench --site test.localhost migrate` failure in `after_migrate` while inserting `Role Profile`: Frappe `RoleProfile.on_update` queued `update_all_users` and raised `DocumentLockedError`.

### Fix

Customer Role/Profile setup seeding now uses migration-safe `db_insert()` for the standard setup records and their `Has Role` child rows. This avoids Role Profile controller queue locks during migrate while keeping the records idempotent.

### Retest

- `bench --site dev.localhost run-tests --module lenscloud.api.test_customer_identity` passed: 11 tests.
- `bench --site dev.localhost migrate` passed through `after_migrate`.
- A direct `test.localhost` migrate attempt in this container was blocked by the sandbox `bwrap` namespace wrapper before Frappe execution, not by LensCloud code.
