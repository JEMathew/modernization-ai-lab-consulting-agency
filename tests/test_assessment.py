from pathlib import Path

import pandas as pd
import pytest

from engine.assessment import (
    SCORE_COLUMNS,
    assess_portfolio,
    consulting_recommendation,
    recommend_6r,
    select_modernization_candidate,
    store_assessment_artifact,
)
from engine.data_loader import load_portfolio


ROOT_DIR = Path(__file__).resolve().parents[1]
PORTFOLIO_PATH = ROOT_DIR / "demo_data" / "apex_aerospace" / "portfolio.csv"


@pytest.fixture
def portfolio() -> pd.DataFrame:
    return load_portfolio(PORTFOLIO_PATH)


@pytest.fixture
def assessment(portfolio: pd.DataFrame) -> pd.DataFrame:
    return assess_portfolio(portfolio)


def test_python_calculates_all_required_scores(assessment: pd.DataFrame) -> None:
    for column in SCORE_COLUMNS:
        assert column in assessment.columns
        assert assessment[column].between(0, 100).all()
    assert (assessment["operating_cost_usd"] > 0).all()


def test_assessment_is_deterministic(portfolio: pd.DataFrame) -> None:
    first = assess_portfolio(portfolio)
    second = assess_portfolio(portfolio)

    pd.testing.assert_frame_equal(first, second)


def test_every_recommendation_is_a_valid_6r(assessment: pd.DataFrame) -> None:
    valid_outcomes = {"Retire", "Retain", "Rehost", "Replatform", "Refactor", "Replace"}

    assert set(assessment["six_r_recommendation"]).issubset(valid_outcomes)


@pytest.mark.parametrize(
    ("criticality", "lifecycle", "platform_type", "cost", "debt", "complexity", "expected"),
    [
        ("Low", "Vendor Supported", "Data Mart", 1, 20, 20, "Retire"),
        ("Medium", "Vendor Supported", "Data Mart", 1, 20, 20, "Retain"),
        ("High", "Vendor Supported", "Operational Reporting", 1, 20, 20, "Rehost"),
        ("Critical", "Vendor Supported", "Data Warehouse", 1, 45, 50, "Replatform"),
        ("Critical", "End of Support", "Data Lake", 1, 90, 70, "Refactor"),
        ("High", "Vendor Supported", "Business Intelligence", 1, 40, 30, "Replace"),
    ],
)
def test_6r_rules_cover_all_outcomes(
    criticality: str,
    lifecycle: str,
    platform_type: str,
    cost: int,
    debt: float,
    complexity: float,
    expected: str,
) -> None:
    row = pd.Series(
        {
            "criticality": criticality,
            "lifecycle_status": lifecycle,
            "platform_type": platform_type,
            "annual_cost_usd": cost,
        }
    )

    assert recommend_6r(row, debt, complexity) == expected


def test_oracle_is_selected_candidate(assessment: pd.DataFrame) -> None:
    candidate = select_modernization_candidate(assessment)

    assert candidate["platform_name"] == "Oracle Customer Analytics Warehouse"
    assert candidate["migration_wave"] == "Wave 1"


def test_hermes_recommendation_uses_assessment_evidence(assessment: pd.DataFrame) -> None:
    candidate = select_modernization_candidate(assessment)
    recommendation = consulting_recommendation(candidate)

    assert "Oracle Customer Analytics Warehouse" in recommendation
    assert candidate["six_r_recommendation"] in recommendation


def test_assessment_artifact_is_stored(
    assessment: pd.DataFrame, tmp_path: Path
) -> None:
    artifact = store_assessment_artifact(assessment, tmp_path, "APEX-AERO-001")

    assert artifact.is_file()
    assert '"calculation_owner": "Python deterministic assessment engine"' in (
        artifact.read_text(encoding="utf-8")
    )


def test_empty_portfolio_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty portfolio"):
        assess_portfolio(pd.DataFrame())
