#!/usr/bin/env sh
set -eu

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is required for paid llm_openai ablation." >&2
  exit 2
fi

echo "WARNING: this ablation uses paid OpenAI API credits. Run locally only; do not put OPENAI_API_KEY on Zeabur." >&2

python3 -m evals.run_ablation --cases evals/cases_llm_dev.json --configs rule,llm_openai --allow-paid
