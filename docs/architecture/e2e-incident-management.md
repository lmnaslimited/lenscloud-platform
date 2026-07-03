# E2E Incident Management

## Purpose

Pre-final Platform and Customer acceptance must not lose failures in chat, screenshots, or temporary logs. Every failed E2E scenario creates an incident entry tied to evidence, owner, fix, and retest result.

## Current Implementation

For the current acceptance pass, incidents are tracked in `docs/incidents/e2e-incident-tracker.md`. Dated evidence under `docs/evidence/customer-launch/` links to incident IDs and carries scenario proof, but it is not the canonical incident tracker. A first-class Platform Incident DocType is a later implementation item unless the acceptance pass proves that operators need in-product incident management before launch.

## Incident Fields

Each incident must include:

- incident ID, for example `LC-E2E-20260702-001`;
- date/time;
- scenario ID;
- severity: `Critical`, `High`, `Medium`, or `Low`;
- scope: `Platform`, `Customer`, `Runtime`, `Policy`, `UX`, or `Documentation`;
- owner: `Platform`, `Infra`, `Design`, or `Product`;
- customer/user used for the test, without passwords or tokens;
- affected record IDs: Customer, Subscription, Site, Bench, Database Server, Orchestration Action Log, or screenshot path;
- symptom;
- expected result;
- actual result;
- suspected cause;
- immediate mitigation;
- fix reference;
- retest result;
- status: `Open`, `In Progress`, `Fixed Pending Retest`, `Closed`, or `Deferred`.

## Severity Rules

`Critical` means launch cannot proceed: no login, no Free Subscription, no real Site provisioning, secret exposure, protected-resource mutation, or broken payment/free checkout trust.

`High` means launch is risky: confusing provisioning state, missing retry, wrong Plan entitlement, customer sees platform runtime terms, mobile cannot reach required details, or Platform cannot inspect customer records.

`Medium` means acceptance can continue with a documented workaround: copy gaps, visual inconsistency, minor routing confusion, or non-blocking evidence gaps.

`Low` means polish or documentation cleanup.

## Required Links

Each incident must link back to:

- `docs/platform-workitems.md` workitem;
- dated evidence file;
- SOP scenario ID;
- action log or screenshot path when available.

## Future First-Class Requirement

If incidents remain frequent after the Free-first launch pass, add a Platform `Incident` DocType with links to Customer, Subscription, Site, Bench, Database Server, Orchestration Action Log, owner, severity, status, and retest evidence. Until then, `docs/incidents/e2e-incident-tracker.md` is the canonical incident ledger for acceptance.

## Recovery Loop

E2E testing must be restartable without relying on chat memory. Every new incident must create or link a follow-up prompt under `docs/handoffs/platform/` or `docs/handoffs/infra/`, depending on owner. The prompt is the executable resume artifact for the fixing agent and must include enough context to close and retest the incident autonomously.

When an incident is opened, the tester must update these artifacts before moving to the next major segment:

1. `docs/incidents/e2e-incident-tracker.md` active incident row.
2. Dated evidence file with scenario status, symptom, and incident ID.
3. `docs/platform-workitems.md` row if the failure changes launch scope or status.
4. Follow-up prompt file, named with the incident ID and short topic, for example `docs/handoffs/platform/e2e-resume-LC-E2E-YYYYMMDD-NNN-<topic>.md`.

The follow-up prompt must include:

- incident ID, owner, severity, scenario ID, and status;
- exact evidence/action-log/screenshot references;
- safe reproduction steps;
- expected result and current actual result;
- implementation or Infra contract boundary;
- retest commands/scenarios;
- closure checklist;
- instruction to update the tracker, evidence, workitems, and handoff after retest.

When an incident is fixed, the fixing agent must not only mark the incident closed. It must also resume from the next unpassed scenario in the dated E2E evidence matrix, unless a stop condition remains.

If the incident owner is Infra, Platform still creates the Platform-side source handoff under `docs/handoffs/infra/`. After Infra returns evidence, Platform consumes it and closes the incident only after Platform-side retest passes.
