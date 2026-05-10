# 02 Evaluation Reporting v2 Raw Prompt Record

- Type: Reconstructed representative prompt
- Date/phase: Evaluation/reporting v2 phase
- Purpose: Make reports readable and count expected refusals correctly
- Safety notes: No API keys, Zeabur tokens, generated logs, or secrets included

## Prompt Excerpt

We need to refactor evaluation/reporting before adding more agent capabilities.

Goal: implement evaluation/reporting v2:

1. user-facing result summary
2. unified ablation runner
3. clearer SPL/action metrics
4. dataset split scaffolding
5. failure-analysis report

Do not add new agent capabilities. Do not change Dataset v1 case semantics. Do not weaken verifier/evaluator checks. Do not add LLM-as-judge. Do not call real OpenAI in tests.

Add `AgentDisplayResult` for app/UI use. Add `python3 -m evals.run_ablation --cases evals/cases_llm_smoke.json --configs rule,llm_fake`.

Define `task_passed = verified_success OR correct_refusal` so `needs_user`/refusal cases are not presented as failures. Per-case results and summaries should include task passed, verified success, correct refusal, false success, unsafe action, steps, tokens, SPL, and failure analysis.

Add dataset split files:

- `evals/cases_smoke.json`
- `evals/cases_dev.json`
- `evals/cases_test.json`
- `evals/cases_llm_smoke.json`

Acceptance:

- tests pass without `OPENAI_API_KEY`
- fake LLM smoke suite still passes
- ablation report is generated
- failure analysis excludes correct refusals
