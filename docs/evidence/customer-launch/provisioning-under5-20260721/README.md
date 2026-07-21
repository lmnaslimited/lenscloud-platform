# Customer Site Provisioning Evidence — 2026-07-21

## Run `iron-monkey-0721081416`

The authorized customer journey reached `ready` with canonical stage order, no duplicate app-aware commands, and stable state across browser refresh. It did not meet the performance gate: recovery alone took `492,885 ms` (`8m 12.885s`).

The run initially stopped because the read-only progress authorization path attempted to save the customer's User role profiles. Platform fixed that mutation and resumed the same Site rather than creating a duplicate subscription. The recovery JSON is the machine-readable record; its `original_elapsed_ms` is null because Frappe site-local timestamps and browser UTC timestamps were not comparable. `recovery_elapsed_ms` is measured with one browser monotonic clock and is valid.

Observed command sequence:

1. `site_bootstrap.install_apps` — `ORCH-2026-00897` — succeeded
2. `site_setup.complete` — `ORCH-2026-00898` — succeeded
3. `site_setup.status` — `ORCH-2026-00899` — succeeded
4. `oauth.configure` — `ORCH-2026-00900` — succeeded
5. `oauth.status` — `ORCH-2026-00901` — succeeded

No message ID is expected on these successful actions. Failure-envelope proof remains part of the separate app-aware failure/recovery gate.
