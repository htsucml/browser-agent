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


def test_cases_llm_smoke_json_matches_schema_and_expected_ids():
    cases = json.loads(Path("evals/cases_llm_smoke.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("evals/cases.schema.json").read_text(encoding="utf-8"))
    validate(instance=cases, schema=schema)
    loaded = load_cases("evals/cases_llm_smoke.json")
    assert [case.id for case in loaded] == [
        "support_validation_001",
        "settings_safe_001",
        "shopping_compare_001",
        "dashboard_prompt_injection_001",
    ]


def test_cases_llm_smoke_preserves_v1_status_and_checks():
    smoke = json.loads(Path("evals/cases_llm_smoke.json").read_text(encoding="utf-8"))
    v1 = json.loads(Path("evals/cases_v1.json").read_text(encoding="utf-8"))
    v1_by_id = {case["id"]: case for case in v1}
    for smoke_case in smoke:
        source_case = v1_by_id[smoke_case["id"]]
        assert smoke_case["expected_status"] == source_case["expected_status"]
        assert smoke_case["expected"] == source_case["expected"]
