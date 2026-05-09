# Architecture

The scaffold is split into five layers:

1. `browser_agent/`: runtime agent interfaces, trace models, verification, recovery, logging, and orchestration.
2. `simulator/`: deterministic fake websites used for repeatable local evaluation.
3. `evals/`: offline cases, checkers, metrics, and report generation.
4. `app/`: FastAPI human interface for ad hoc tasks.
5. `docs/` and `.agents/skills/`: project guidance for human and coding-agent maintainers.

Runtime flow:

```text
observe -> plan -> locate -> act -> verify -> log -> final report
```

The current browser implementation targets the simulator. A future milestone can add Playwright or another real-browser adapter behind the same interfaces.
