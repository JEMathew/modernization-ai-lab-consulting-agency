from pathlib import Path

import pytest

from engine.data_loader import (
    DataLoadError,
    REQUIRED_PORTFOLIO_COLUMNS,
    load_enterprise_profile,
    load_json_safely,
    load_portfolio,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
APEX_DATA_DIR = ROOT_DIR / "demo_data" / "apex_aerospace"


def test_enterprise_profile_loads_successfully() -> None:
    profile = load_enterprise_profile(APEX_DATA_DIR / "enterprise_profile.json")

    assert profile.enterprise_name == "Apex Aerospace Manufacturing"
    assert profile.industry == "Aerospace Manufacturing"


def test_portfolio_loads_successfully() -> None:
    portfolio = load_portfolio(APEX_DATA_DIR / "portfolio.csv")

    assert not portfolio.empty


def test_portfolio_contains_at_least_six_platforms() -> None:
    portfolio = load_portfolio(APEX_DATA_DIR / "portfolio.csv")

    assert len(portfolio) >= 6


def test_oracle_customer_analytics_warehouse_exists() -> None:
    portfolio = load_portfolio(APEX_DATA_DIR / "portfolio.csv")

    assert "Oracle Customer Analytics Warehouse" in portfolio["platform_name"].values


def test_required_portfolio_columns_exist() -> None:
    portfolio = load_portfolio(APEX_DATA_DIR / "portfolio.csv")

    assert REQUIRED_PORTFOLIO_COLUMNS.issubset(portfolio.columns)


def test_missing_file_raises_controlled_error(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.json"

    with pytest.raises(DataLoadError, match="not found"):
        load_json_safely(missing_file)


def test_malformed_json_raises_controlled_error(tmp_path: Path) -> None:
    malformed_file = tmp_path / "malformed.json"
    malformed_file.write_text('{"enterprise_id": ', encoding="utf-8")

    with pytest.raises(DataLoadError, match="Malformed JSON"):
        load_json_safely(malformed_file)
