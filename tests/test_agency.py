from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from engine.agency import (
    AGENT_SEQUENCE,
    agent_timeline,
    build_agent_operations,
    create_plan,
    executive_delivery_chain,
    load_business_constraints,
    manager_timeline,
    replan_for_constraints,
    store_replan_artifact,
)
from engine.assessment import assess_portfolio
from engine.data_loader import load_portfolio


ROOT_DIR = Path(__file__).resolve().parents[1]
APEX_DATA_DIR = ROOT_DIR / "demo_data" / "apex_aerospace"
START_TIME = datetime(2026, 7, 12, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
def assessment() -> pd.DataFrame:
    return assess_portfolio(load_portfolio(APEX_DATA_DIR / "portfolio.csv"))


def test_all_required_agents_are_visible() -> None:
    operations = build_agent_operations(START_TIME)
    assert operations["Agent"].tolist() == AGENT_SEQUENCE
    assert {"Current Status", "Task", "Confidence", "Start Time", "Duration", "Result", "Cost"}.issubset(operations.columns)


def test_agent_and_manager_timelines_are_complete() -> None:
    assert len(agent_timeline(START_TIME)) == 7
    assert len(manager_timeline(START_TIME)) == 4
    assert "Hermes" in manager_timeline(START_TIME)["Manager"].values


def test_business_constraints_load() -> None:
    constraints = load_business_constraints(APEX_DATA_DIR / "business_constraints.json")
    assert constraints["annual_modernization_budget_usd"] == 8_500_000
    assert constraints["maximum_planned_downtime_hours"] == 8


def test_original_plan_preserves_assessment_waves(assessment: pd.DataFrame) -> None:
    plan = create_plan(assessment, 8_500_000)
    oracle = plan[plan["Platform"] == "Oracle Customer Analytics Warehouse"].iloc[0]
    assert oracle["Migration Wave"] == "Wave 1"
    assert plan["Planned Funding (USD)"].sum() == 8_500_000


def test_thirty_percent_reduction_creates_new_plan(assessment: pd.DataFrame) -> None:
    replan = replan_for_constraints(
        assessment, 8_500_000, 5_950_000, 8, "Customer Analytics Continuity"
    )
    assert replan["budget_reduction_percent"] == 30.0
    assert replan["new_plan"]["Planned Funding (USD)"].sum() == 5_950_000
    oracle = replan["new_plan"][replan["new_plan"]["Platform"] == "Oracle Customer Analytics Warehouse"].iloc[0]
    assert oracle["Migration Wave"] == "Wave 1"
    assert "Deferred" in replan["new_plan"]["Migration Wave"].values


def test_replan_reuses_evidence_and_only_reruns_planner_validation(assessment: pd.DataFrame) -> None:
    replan = replan_for_constraints(
        assessment, 8_500_000, 5_950_000, 4, "Customer Analytics Continuity"
    )
    assert "Metadata Discovery" in replan["reused"]
    assert "Consulting Assessment" in replan["reused"]
    assert replan["rerun"] == ["Prioritization Planner", "Validation Specialist"]
    assert replan["time_saved_hours"] == 14
    assert "rollback checkpoint" in replan["why"]


def test_replan_is_deterministic(assessment: pd.DataFrame) -> None:
    first = replan_for_constraints(assessment, 8_500_000, 5_950_000, 8, "Customer Analytics")
    second = replan_for_constraints(assessment, 8_500_000, 5_950_000, 8, "Customer Analytics")
    pd.testing.assert_frame_equal(first["new_plan"], second["new_plan"])
    assert first["why"] == second["why"]


def test_invalid_replan_budget_is_rejected(assessment: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="no greater than"):
        replan_for_constraints(assessment, 8_500_000, 9_000_000, 8, "Customer Analytics")


def test_replan_artifact_is_stored(assessment: pd.DataFrame, tmp_path: Path) -> None:
    replan = replan_for_constraints(assessment, 8_500_000, 5_950_000, 8, "Customer Analytics")
    artifact = store_replan_artifact(replan, tmp_path)
    assert artifact.is_file()
    assert '"manager": "Hermes"' in artifact.read_text(encoding="utf-8")


def test_executive_delivery_chain_requires_human_approval() -> None:
    chain = executive_delivery_chain("package.zip")
    assert chain["Stage"].tolist() == [
        "Executive Recommendation",
        "Recommended Candidate",
        "Migration Package",
        "Deployment Readiness",
        "Approval Status",
    ]
    assert chain.iloc[-1]["Status"] == "Pending Human Approval"
