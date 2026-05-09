# Dataset Schema

Eval cases are JSON objects with:

- `id`: stable case identifier
- `domain`: high-level domain
- `start_url`: simulator or site URL
- `task`: natural language instruction
- `expected`: deterministic checks
- `max_steps`: step budget
- `tags`: optional labels

The executable JSON Schema lives at `evals/cases.schema.json`.
