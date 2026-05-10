#!/usr/bin/env sh
set -eu

LLM_MODEL="${LLM_MODEL:-gpt-4.1-nano}"

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is required for the local OpenAI LLM smoke suite." >&2
  exit 2
fi

echo "WARNING: this four-case smoke suite uses paid API credits. Run locally only; do not put OPENAI_API_KEY on Zeabur." >&2
echo "Running LLM smoke suite with provider=openai, model=${LLM_MODEL}." >&2

PLANNER=llm \
LLM_PROVIDER=openai \
LLM_MODEL="$LLM_MODEL" \
MAX_LLM_CALLS_PER_RUN=1 \
MAX_STEPS=3 \
MAX_OUTPUT_TOKENS=300 \
REQUEST_TIMEOUT_SECONDS=30 \
python3 -m evals.run_eval --cases evals/cases_llm_smoke.json
