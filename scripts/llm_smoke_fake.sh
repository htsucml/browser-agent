#!/usr/bin/env sh
set -eu

PLANNER=llm \
LLM_PROVIDER=fake \
python3 -m evals.run_eval --cases evals/cases_v1.json --case support_validation_001
