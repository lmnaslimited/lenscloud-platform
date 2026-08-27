# LensCloud Platform Test Record

This document tracks functional validation, defects, and acceptance testing for the LensCloud Platform UI and orchestration workflows.

Status: `Passed`, `Failed`, `Blocked`, or `Not Tested`.

## UI Validation Findings

| Area       | Finding                                                            | Severity | Status |
| ---------- | ------------------------------------------------------------------ | -------- | ------ |
| Bench List | Label displays **"New Benche"** instead of **"New Bench"**         | Minor    | Open   |
| Dashboard  | Bench and Site metrics are not accurately reflecting actual counts | Major    | Open   |

## Test Summary

| Metric           | Count |
| ---------------- | ----- |
| Total Test Cases | 17    |
| Passed           | 13    |
| Failed           | 4     |

## Detailed Test Results

| Test Case ID | Scenario                                                                                                  | Expected Result                                                              | Actual Result                   | Status |
| ------------ | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------- | ------ |
| TC-01        | Public Database Server A (No Customer) → Public Bench A (No Customer) → Site A (Customer 1)               | Site should be created successfully.                                         | Site created successfully.      | Passed |
| TC-02        | Public Database Server A (No Customer) → Public Bench A (No Customer) → Site B (Customer 2)               | Site should be created successfully.                                         | Site created successfully.      | Passed |
| TC-03        | Public Database Server A (No Customer) → Public Bench B (Customer 1) → Site C (Customer 1)                | Site should be created successfully.                                         | Site created successfully.      | Passed |
| TC-04        | Public Database Server A (No Customer) → Private Bench B (Customer 1)                                     | Bench should not be created.                                                 | Bench document cannot be saved. | Passed |
| TC-05        | Private Shared Database Server B (Customer 2) → Private Shared Bench C (Customer 2) → Site D (Customer 2) | Site should be created successfully.                                         | Site created successfully.      | Passed |
| TC-06        | Private Shared Database Server B (Customer 2) → Private Shared Bench C (Customer 2) → Site E (Customer 2) | Site should be created successfully.                                         | Site created successfully.      | Passed |
| TC-07        | Private Shared Database Server B (Customer 2) → Private Shared Bench C (Customer 2) → Site F (Customer 2) | Site creation should not be allowed after reaching the permitted site limit. | Site was created successfully.  | Failed |
| TC-08        | Private Shared Database Server B (Customer 2) → Private Shared Bench D (Customer 3)                       | System should prevent saving due to customer mismatch.                       | Document save was blocked.      | Passed |
| TC-09        | Private Shared Database Server B (Customer 2) → Private Shared Bench E (Customer 2)                       | System should prevent saving due to bench limit.                             | Document is getting saved.      | Failed |
| TC-10        | Private Database Server C (Customer 3) → Private Bench D (Customer 3) → Site G (Customer 3)               | Site should be created successfully.                                         | Site created successfully.      | Passed |
| TC-11        | Private Database Server C (Customer 3) → Private Bench D (Customer 3) → Site H (Customer 3)               | Additional site should not be created.                                       | Site was created successfully.  | Failed |
| TC-12        | Private Database Server C (Customer 3) → Private Bench D (Customer 3) → Site I (Customer 2)               | Site should not be created due to customer mismatch.                         | Site was created successfully.  | Failed |
| TC-13        | Private Database Server C (Customer 3) → Private Bench E (Customer 3)                                     | Additional private bench should not be created.                              | Creation was blocked.           | Passed |
| TC-14        | Private Database Server C (Customer 3) → Private Bench F (Customer 2)                                     | Bench should not be created due to customer mismatch.                        | Creation was blocked.           | Passed |
| TC-15        | Private Database Server C (Customer 3) → Private Shared Bench G (Customer 3)                              | Private Shared Bench should not be created under a Private Database Server.  | Creation was blocked.           | Passed |
| TC-16        | Private Shared Database Server B (Customer 2) → Private Shared Bench H (No Customer)                      | Bench document should not be created since no customer is maintained.        | Creation was blocked.           | Passed |
| TC-17        | Public Database Server A (No Customer) → Private Bench I (Customer 3)                                     | Database and Bench privacy should match.                                     | Creation was blocked.           | Passed |

## Acceptance Result

| Area                                       | Result              | Status |
| ------------------------------------------ | ------------------- | ------ |
| Public Database Server validations         | Working as expected | Passed |
| Public Bench ownership validation          | Working as expected | Passed |
| Private Shared customer validation         | Working as expected | Passed |
| Private Shared site limit validation       | Not enforced        | Failed |
| Private Shared bench limit validation      | Not enforced        | Failed |
| Private Bench single-site restriction      | Not enforced        | Failed |
| Private Site customer ownership validation | Not enforced        | Failed |

## Defects Identified

| Defect ID | Description                                                                                        | Severity | Status |
| --------- | -------------------------------------------------------------------------------------------------- | -------- | ------ |
| DEF-01    | Bench list label displays "New Benche" instead of "New Bench"                                      | Minor    | Open   |
| DEF-02    | Dashboard Bench count does not match actual Bench records                                          | Major    | Open   |
| DEF-03    | Dashboard Site count does not match actual Site records                                            | Major    | Open   |
| DEF-04    | Bench limit validation is not enforced for Private Shared Database Servers                         | Critical | Open   |
| DEF-05    | Site limit validation is not enforced for Private Shared Database Servers                          | Critical | Open   |
| DEF-06    | Multiple Sites can be created under a Private Bench when only one Site should be allowed           | Critical | Open   |
| DEF-07    | Customer ownership validation is not enforced during Site creation under a Private Database Server | Critical | Open   |

## Evidence

* Test execution date: 20 June 2026
* Tested by: Fathima Irfana

## Conclusion

The validation rules for Public Database Servers, Public Benches, privacy matching, and ownership restrictions are functioning correctly. However, several critical validation gaps remain in the Private Shared and Private Database Server workflows. These issues must be resolved before Private Shared and Private lifecycle acceptance can be considered complete.
