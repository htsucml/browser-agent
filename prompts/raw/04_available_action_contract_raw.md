# 04 Available-Action Contract Raw Prompt Record

- Type: Reconstructed representative prompt
- Date/phase: LLM action grounding phase
- Purpose: Ground LLM decisions in stable action IDs and handle key simulator workflows
- Safety notes: No API keys, Zeabur tokens, generated logs, or secrets included

## Prompt Excerpt

Refactor LLMPlanner action output toward available-action-only selection.

Context: real LLM shopping smoke tests failed when the model chose loose/fuzzy locators or unsupported semantic action types. Fake tests passed, but real model output exposed schema and grounding issues.

Goal: make LLM action selection scalable by requiring the model to choose from available action IDs.

Preferred output schema:

```json
{
  "decision": "act",
  "action_id": "shopping:add_to_wishlist:compact-usb-c-hub",
  "reason": "It is the cheapest USB-C hub with rating at least 4.5."
}
```

Other decisions:

```json
{
  "decision": "needs_user",
  "reason": "The support form requires an email address, but the user did not provide one."
}
```

Requirements:

- If available actions exist, choose exactly one valid `action_id`.
- Reject invalid or unknown action IDs before mutation.
- Keep backward compatibility for click/select only when a valid action ID exists.
- Do not add a growing list of arbitrary semantic action aliases.
- Add compact shopping observations and action IDs for wishlist/cart.
- Add support/missing-info preflight so support validation returns needs_user without inventing an email.
- Add generic form-fill action contract for support form.
- Add compact dashboard actions for review/approve and reject prompt-injection style actions.
- Do not hardcode case IDs.
- Do not weaken evaluator checks.

Acceptance:

- fake LLM shopping compare succeeds
- fake LLM support validation remains needs_user
- fake LLM support form succeeds
- fake LLM dashboard prompt injection succeeds
- wrong actions fail safely without mutation
- rule baseline unchanged
