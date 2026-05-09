import json
from pathlib import Path

from browser_agent.agent import BrowserAgent


def test_trace_contains_required_scaffold_fields(tmp_path):
    result = BrowserAgent().run("simulator://shopping", "Add Red Shoes to the cart")
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    required = {
        "run_id",
        "status",
        "verified",
        "actions",
        "failures",
        "recoveries",
        "maintenance_events",
        "safety_events",
        "final_evidence",
        "token_count",
        "cost_usd",
        "started_at",
        "finished_at",
    }
    assert required.issubset(trace.keys())
    assert trace["status"] == "success"
    assert trace["verified"] is True
    assert trace["actions"]
