#!/usr/bin/env sh
set -eu

CASE_ID="${1:-support_validation_001}"
LLM_PROVIDER="${LLM_PROVIDER:-openai}"
LLM_MODEL="${LLM_MODEL:-gpt-4.1-mini}"

if [ "$LLM_PROVIDER" = "openai" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is required when LLM_PROVIDER=openai." >&2
  exit 2
fi

echo "WARNING: this smoke test may use paid API credits." >&2
echo "Running one-case LLM smoke with provider=${LLM_PROVIDER}, model=${LLM_MODEL}, case=${CASE_ID}." >&2

PLANNER=llm \
LLM_PROVIDER="$LLM_PROVIDER" \
LLM_MODEL="$LLM_MODEL" \
MAX_LLM_CALLS_PER_RUN=1 \
MAX_STEPS=3 \
MAX_OUTPUT_TOKENS=300 \
REQUEST_TIMEOUT_SECONDS=30 \
python3 -m evals.run_eval --cases evals/cases_v1.json --case "$CASE_ID"
