#!/usr/bin/env sh
set -eu

python3 -m evals.run_ablation --cases evals/cases_llm_dev.json --configs rule,llm_fake
