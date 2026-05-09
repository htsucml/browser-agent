# Browser-Agent Spec

Browser-agent specs define runtime behavior.

## Runtime Contract

The agent receives:

- `start_url`
- natural language `task`
- optional simulator state/check context

The agent produces:

- status
- verified flag
- final reason
- trace file
- action, failure, recovery, maintenance, and safety records

## Non-Negotiable Rule

The agent must never claim success unless verification passes.

## Current Pass

Planner behavior is rule-based and simulator-specific. It stands in for a future LLM planner while exercising the full runtime flow.
