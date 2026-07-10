# Platform Handoff - Customer Provisioning UI Continuation - 2026-07-10

## Incident Thread

Primary E2E thread: `LC-E2E-20260709-001`.

Related incident tracker:

```text
docs/incidents/e2e-incident-tracker.md
```

Current target site under test:

```text
tara-communo-hub.cloud.lmnaslens.com
```

Customer test user:

```text
nithu@gmail.com
```

Credentials are available only in the local credential file:

```text
/tmp/lenscloud_credential_file.json
keys: customer_nithu, customer_nithu_password
```

## Why This Handoff Exists

The provisioning backend is now producing orchestration progress across the expected stages, but the customer portal UI still has three experience defects:

1. The launch timeline can jump from `Preparing workspace` directly to the final stage when a polling response returns several completed backend states at once.
2. The right inspector `Launch checklist` does not reliably show durable green completed icons for completed customer journey steps.
3. The setup defaults dialog in Step 2 is discoverable only by button; it should open automatically when required setup fields are incomplete.

If Codex hits a usage or tool limit again, continue from this file.

## Files To Touch

Frontend:

```text
frontend/src/pages/CustomerPlansPage.vue
```

Incident tracker:

```text
docs/incidents/e2e-incident-tracker.md
```

Avoid unrelated edits. There are existing pending changes in:

```text
lenscloud/api/bench_command.py
lenscloud/api/test_bench_command.py
docs/incidents/e2e-incident-tracker.md
```

Do not revert them.

## Intended Frontend Fix

### 1. Sequential launch timeline reveal

`CustomerPlansPage.vue` currently computes `provisioningSteps` directly from the latest `result`/`resultSite` snapshot. When a poll returns `runtime ready`, `route ready`, `setup complete`, and `oauth configured` together, several steps become `done` in one render and the spinner appears to skip the intermediate stages.

Add a small visual progression layer:

- Keep a raw backend-truth computed, for example `rawProvisioningSteps`.
- Add `visualProvisioningIndex = ref(0)`.
- Add `visualProgressTimer = null`.
- Compute a `targetProvisioningIndex` from backend truth:
  - first `failed` or `paused` index, if any;
  - otherwise first `active` index, if any;
  - otherwise last `done` index;
  - default `0`.
- Watch `targetProvisioningIndex` and advance `visualProvisioningIndex` one step at a time, about every `700-1000ms`.
- The displayed `provisioningSteps` should:
  - show indices below `visualProvisioningIndex` as `done`;
  - show the current index as `active` while revealing caught-up backend-completed stages;
  - show indices above it as `pending`;
  - preserve real `failed`/`paused` states immediately.
- Reset `visualProvisioningIndex` when `result.value?.site` changes.
- Clear `visualProgressTimer` in `onBeforeUnmount`.

This keeps the customer-facing timeline sequential while still respecting the backend status returned by polling.

### 2. Inspector completed icons

The inspector uses `flowSteps` and `currentStepIndex`. Add a helper such as `flowStepState(index)`:

```js
function flowStepState(index) {
	if (hasReadySite.value && index <= currentStepIndex.value) return 'done'
	if (index < currentStepIndex.value) return 'done'
	if (index === currentStepIndex.value && progressActive.value) return 'active'
	if (index === currentStepIndex.value) return 'current'
	return 'pending'
}
```

Update the inspector icon template so:

- `done` uses green background and `CheckCircle2`;
- `active` uses blue background and spinning `RefreshCcw`;
- `current` uses blue background and `Clock3`;
- `pending` uses gray background and `Clock3`.

The important UX requirement is that completed prior steps must always retain green ticks while provisioning is active or ready.

### 3. Auto-open Step 2 setup defaults dialog

Import `watch` from Vue.

Add:

```js
const setupDialogDismissed = ref(false)
```

Add helpers:

```js
function shouldAutoOpenSetupDialog() {
	return (
		step.value === 'setup' &&
		!setupDialogOpen.value &&
		!setupSchemaLoading.value &&
		setupFields.value.length > 0 &&
		!setupDefaultsComplete.value &&
		!setupDialogDismissed.value
	)
}

function maybeAutoOpenSetupDialog() {
	if (shouldAutoOpenSetupDialog()) setupDialogOpen.value = true
}

function dismissSetupDialog() {
	setupDialogDismissed.value = true
	setupDialogOpen.value = false
}
```

Call `maybeAutoOpenSetupDialog()` after `loadSetupSchema()` in `continueFromPlan()`.

Add a watcher:

```js
watch([step, setupFields, setupDefaultsComplete, setupSchemaLoading], maybeAutoOpenSetupDialog, { flush: 'post' })
```

Reset `setupDialogDismissed.value = false` when entering Step 2 from plan selection or when the user explicitly clicks the setup defaults button.

Use `dismissSetupDialog()` for backdrop close, close icon, and cancel button. On successful save, set `setupDialogDismissed.value = true` and close the dialog.

## Incident Tracker Updates

Update `docs/incidents/e2e-incident-tracker.md`:

- Mark `LC-E2E-20260709-003` as `Fixed Pending Retest` once the inspector green-tick fix is implemented.
- Add a row for the provisioning timeline jump, suggested id `LC-E2E-20260709-010`.
- Add a row for setup dialog discoverability, suggested id `LC-E2E-20260709-011`.

Suggested summaries:

```text
LC-E2E-20260709-010 | Customer launch timeline skips visible intermediate stages | Medium | Customer Plans provisioning timeline | Platform | Fixed Pending Retest
LC-E2E-20260709-011 | Setup defaults dialog is not automatically invoked in Step 2 | Medium | Customer Plans setup site step | Platform | Fixed Pending Retest
```

## Verification Commands

Run from:

```text
/workspace/frappe-bench/apps/lenscloud
```

Minimum checks:

```text
npm --prefix frontend run build
git diff --check -- frontend/src/pages/CustomerPlansPage.vue docs/incidents/e2e-incident-tracker.md
```

If live browser credentials are available and the dev server is already running, retest:

1. Login as `nithu@gmail.com`.
2. Recreate or refresh provisioning for `tara-communo-hub.cloud.lmnaslens.com`.
3. Confirm Step 2 auto-opens the setup defaults dialog when incomplete.
4. Confirm launch timeline visibly progresses step by step.
5. Confirm inspector completed customer steps show green ticks.

## Known Separate Issue

OAuth browser login callback 500 is tracked separately as `LC-E2E-20260709-009`. Do not mix that with this UI progression fix.

The likely blocker for `LC-E2E-20260709-009` remains local-dev issuer reachability from target Site pods when `Platform Settings.oauth_base_url=http://dev.localhost:8000`.


## 2026-07-10 Follow-Up Fix

The first continuation patch only smoothed frontend rendering. Live retest showed the spinner could still stay at `Preparing workspace` while the backend created orchestration logs, because `retry_customer_site_provisioning` performed several long-running stages inside one HTTP request and returned only after they completed.

The backend retry path was then split so each customer poll performs one stage and returns the updated `Site` state:

1. Runtime inspect and Site status sync / route check.
2. `site_setup.status`, moving setup to `Required` when setup is needed.
3. `site_setup.complete`, moving setup to `Running` while completion is verified on the next poll.
4. `site_setup.status` completion verification.
5. `oauth.status`, moving OAuth to `Pending` when configuration is needed.
6. `oauth.configure`, moving OAuth to `Running` while verification is checked on the next poll.
7. Final `oauth.status`, moving progress to ready when configured.

Frontend mapping was also aligned so setup status `Required` maps to `setup_running`; this moves the customer spinner to `Setting site defaults` instead of leaving it in the earlier setup-check stage.

Regression added:

```text
bench --site dev.localhost run-tests --module lenscloud.api.test_customer_site_setup
```

The focused test `test_progress_moves_to_setup_defaults_when_setup_required` confirms a Ready route with setup status `Required` reports customer progress `setup_running`.
