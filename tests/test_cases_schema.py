import json
from pathlib import Path

from jsonschema import validate

from evals.run_eval import load_cases


def test_cases_json_matches_schema():
    cases = json.loads(Path("evals/cases.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("evals/cases.schema.json").read_text(encoding="utf-8"))
    validate(instance=cases, schema=schema)
    loaded = load_cases("evals/cases.json")
    assert loaded[0].id == "shopping_add_red_shoes"


def test_cases_v1_json_matches_schema():
    cases = json.loads(Path("evals/cases_v1.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("evals/cases.schema.json").read_text(encoding="utf-8"))
    validate(instance=cases, schema=schema)
    loaded = load_cases("evals/cases_v1.json")
    assert len(loaded) == 13
    assert loaded[0].expected_status == "success"
