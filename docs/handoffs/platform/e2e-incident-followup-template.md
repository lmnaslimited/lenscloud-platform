# E2E Incident Follow-Up Prompt Template

Use this template whenever a Platform-owned E2E incident is opened. For Infra-owned incidents, create the same shape under `docs/handoffs/infra/`.

```text
Work inside /workspace/frappe-bench/apps/lenscloud.

Read first:
- AGENTS.md
- docs/architecture/e2e-incident-management.md
- docs/incidents/e2e-incident-tracker.md
- docs/evidence/customer-launch/<dated-evidence>.md
- this incident follow-up prompt

Incident: <LC-E2E-YYYYMMDD-NNN>
Owner: <Platform|Infra|Design|Product>
Severity: <Critical|High|Medium|Low>
Scenario: <SOP scenario ID>
Status: <Open|In Progress|Fixed Pending Retest>

Evidence references:
- Action log: <ORCH-... or none>
- Screenshot/report: <path or none>
- Runtime object IDs: <safe names only>

Expected result:
<what should happen>

Actual result:
<what happened>

Safe reproduction steps:
1. <step>
2. <step>

Implementation / contract boundary:
<what Platform owns and what Infra/Design/Product owns>

Retest plan:
1. <focused test command or UI path>
2. <live verification if needed>
3. <evidence to capture>

Closure checklist:
- update code/docs if needed;
- run focused tests;
- update `docs/incidents/e2e-incident-tracker.md`;
- update dated E2E evidence;
- update `docs/platform-workitems.md` when launch status changes;
- resume from the next unpassed scenario in the E2E matrix without waiting for another operator prompt.
```
