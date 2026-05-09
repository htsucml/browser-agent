"""Trace logging for every agent run."""

from __future__ import annotations

import json
from pathlib import Path

from browser_agent.schemas import AgentTrace, utc_now


class TraceLogger:
    def __init__(self, root: str | Path = "logs/runs"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, trace: AgentTrace) -> str:
        trace.finished_at = trace.finished_at or utc_now()
        path = self.root / f"{trace.run_id}.json"
        path.write_text(json.dumps(trace.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return str(path)
