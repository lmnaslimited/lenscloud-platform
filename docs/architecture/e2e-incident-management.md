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
