# Development Progress

## Starting Idea

The project began as a reliability-first browser-agent assignment: do not build a flashy click bot first; build the data, traces, verifier, evaluator, and deployment surface that make future browser-agent capabilities measurable.

The working loop was:

```text
intent -> task type -> environment -> failure mode -> deterministic check -> trace -> eval -> targeted fix
```

## Milestones Completed

### 1. Scaffold and Project Structure

Created the separated repo layout:

- `browser_agent/`
- `simulator/`
- `evals/`
- `app/`
- `docs/`
- `tests/`
- `logs/`

Added typed schemas for eval cases, traces, action records, verification results, failures, recovery, maintenance, safety, and eval results.

### 2. Deterministic Simulator and Evaluator

Built a resettable simulator and offline evaluator. The evaluator reads JSON cases, runs the agent, loads traces, applies deterministic checks, computes metrics, and writes reports.

Key reliability metrics:

- verified success
- false success
- unsafe action
- correct refusal
- task passed
- action counts and SPL
- token/call counts
- failure analysis

### 3. Dataset v1

Created Dataset v1 with 13 deterministic simulator cases:

- shopping constraints
- cheapest-item comparison
- long-horizon shopping
- fake success
- selector drift
- modal blocking
- safe setting changes
- destructive setting refusal
- vague instruction
- support form filling
- missing required form information
- dashboard table comparison
- dashboard prompt injection

### 4. RulePlanner Baseline

Implemented a deterministic RulePlanner baseline. It currently passes 8/13 tasks by task-passed metric in Dataset v1 and remains useful as an integration-test driver.

Important rule: RulePlanner should not become the main intelligence layer or grow into case-specific spaghetti. Future improvements should prefer shared mechanisms such as action candidates, validators, verifier coverage, preflight checks, recovery, and memory.

### 5. MLOps / Zeabur Checkpoint

Added:

- FastAPI UI.
- Dockerfile.
- Playwright Chromium installation.
- `/health` endpoint.
- Port-env startup.
- Logs directory creation.
- Zeabur-compatible deployment path.

### 6. Read-Only Playwright Backend

Added a real-web read-only backend:

- open URL
- extract title/current URL/headings/visible text/link count
- optional screenshot
- write trace
- no clicking
- no form filling
- no navigation beyond initial page load

### 7. LLMPlanner Evolution

#### Fake Provider

Added a fake LLM client for tests and dry runs. This allows LLMPlanner plumbing to be tested without external calls or API keys.

#### Real OpenAI Smoke

Added OpenAI-compatible provider support with strict local caps:

- `MAX_LLM_CALLS_PER_RUN`
- `MAX_STEPS`
- `MAX_OUTPUT_TOKENS`
- `REQUEST_TIMEOUT_SECONDS`

Paid runs require explicit local commands and are not used in tests.

#### Available-Action Contract

Real-key smoke tests showed that fuzzy model outputs could choose wrong locators/items. The planner was refactored so the LLM chooses stable `action_id` values from compact `available_actions`.

#### Schema Normalization

Added strict-but-practical normalization for model outputs:

- `decision=act` + `action_id` is preferred.
- `decision=click/select` can be normalized only when a valid `action_id` is present.
- Unknown/fuzzy targets fail safely before mutation.

#### Form Action Contract

Added a generic support-form contract:

- `fill_and_submit`
- `act_sequence`
- field IDs
- submit action ID
- missing required fields handled by preflight/needs_user

#### Prompt-Injection Case

Added and solved the dashboard prompt-injection case with action candidates and validation. The agent marks only Morgan Lee's pending reimbursement request and ignores page text that looks like a system instruction.

### 8. Evaluation and Reporting v2

Added:

- `task_passed = verified_success OR correct_refusal`
- clearer markdown reports
- ablation reports
- per-case comparison tables
- failure-analysis grouping
- user-facing display result summaries

This fixed the earlier reporting problem where correct `needs_user` outcomes looked like failures.

### 9. LLM-Ready Dev Subset

Created `evals/cases_llm_dev.json` with seven cases suitable for current LLM action contracts:

- `support_validation_001`
- `settings_safe_001`
- `shopping_compare_001`
- `dashboard_prompt_injection_001`
- `support_form_001`
- `dashboard_table_001`
- `shopping_normal_001`

Latest known OpenAI ablation passes 7/7 by task-passed metric.

### 10. BYOK Public Demo Safeguards

Added or verified:

- BYOK disabled by default.
- Server OpenAI key fallback disabled by default.
- Demo token support.
- Per-IP rate limit.
- Global active-run guard.
- Runtime/cost caps.
- URL safety for real-web read-only mode.
- Secret redaction.
- Password inputs and warning copy in UI.

### 11. Real-Web Read-Only LLM Summarization

Added optional LLM answering/summarization for real pages:

- Uses extracted page evidence only.
- Stores raw answer text in trace.
- Displays readable answer first.
- Preserves raw JSON in debug details.
- Handles bullets and incomplete/malformed output defensively.

## Current Status

Dataset v1:

- 13 cases.
- RulePlanner task passed 8/13.
- Verified successes 6/13.
- Correct refusals 2/13.
- False successes 0.
- Unsafe actions 0.

LLM-ready dev:

- 7 cases.
- RulePlanner task passed 7/7.
- OpenAI LLMPlanner task passed 7/7.
- OpenAI LLMPlanner verified successes 6/7.
- Correct refusal 1/7.
- False successes 0.
- Unsafe actions 0.

Real-web:

- Read-only extraction works.
- BYOK summarization works locally.
- UI displays answer, source, title, evidence, metrics, trace path, and raw debug trace.

## Next Steps

1. Add screenshots/GIFs for README and demo.
2. Expand Dataset v2 and create a frozen test split.
3. Implement fake-success recovery.
4. Implement modal recovery.
5. Implement selector-drift rediscovery and persistent locator memory.
6. Generate real-web available actions from DOM/accessibility trees.
7. Add real-web clicking/forms only with strict confirmation and deterministic verification.
8. Strengthen SPL/cost reporting for multi-step tasks.
9. Add more adversarial benchmark cases.
