# Failure Taxonomy

Initial failure categories:

- `observation_error`: unable to read current page/state
- `planning_error`: no safe or feasible plan
- `locator_error`: target element cannot be found
- `action_error`: browser action failed
- `verification_error`: expected outcome did not hold
- `safety_refusal`: task was unsafe or out of scope
- `maintenance_needed`: selector or UI drift detected
- `unknown_error`: uncategorized failure

Failures should record cause, evidence, and whether recovery was attempted.
