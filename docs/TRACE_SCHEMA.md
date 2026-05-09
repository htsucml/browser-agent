# Trace Schema

Each run writes a JSON trace under `logs/runs/`.

Trace records include:

- run metadata
- status
- verified flag
- action records
- verification records
- failure events
- recovery events
- maintenance events
- safety events
- final evidence
- token and cost placeholders
- timestamps

The canonical dataclass models live in `browser_agent/schemas.py`.
