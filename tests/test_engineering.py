from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest

from engine.engineering import (
    CANDIDATE_NAME,
    build_engineering_engagement,
    dependency_analysis,
    generate_implementation_package,
    load_engineering_inputs,
    modernize_etl,
    modernize_sql,
    package_bytes,
    source_target_mapping,
    target_architecture,
    validation_plan,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
APEX_DATA_DIR = ROOT_DIR / "demo_data" / "apex_aerospace"


@pytest.fixture
def inputs() -> dict[str, object]:
    return load_engineering_inputs(APEX_DATA_DIR)


@pytest.fixture
def engagement() -> dict[str, object]:
    return build_engineering_engagement(APEX_DATA_DIR)


def test_metadata_discovery_contains_required_inventory(
    engagement: dict[str, object]
) -> None:
    metadata = engagement["metadata"]

    assert metadata["schemas"] == 42
    assert metadata["tables"] == 1380
    assert metadata["views"] > 0
    assert metadata["stored_procedures"] > 0
    assert metadata["etl_jobs"] == 214
    assert metadata["reports"] > 0
    assert metadata["data_volume_tb"] == 185
    assert metadata["owners"]["business_owner"] == "VP Customer Experience"


def test_dependency_analysis_covers_upstream_downstream_and_impact(
    inputs: dict[str, object]
) -> None:
    analysis = dependency_analysis(inputs)

    assert "Informatica Enterprise ETL" in analysis["upstream"]
    assert "Cognos Executive BI" in analysis["downstream"]
    assert not analysis["critical_dependencies"].empty
    assert analysis["business_impact"]
    assert "digraph dependencies" in analysis["graph_dot"]


def test_target_architecture_has_required_order() -> None:
    architecture = target_architecture()

    assert architecture["layers"]["component"].tolist() == [
        "Oracle",
        "Cloud Storage Landing",
        "BigQuery",
        "Dataform",
        "Dataplex",
        "Looker",
    ]
    assert architecture["layers"]["why"].str.len().gt(20).all()


def test_mapping_has_required_display_columns(inputs: dict[str, object]) -> None:
    mapping = source_target_mapping(inputs)

    assert len(mapping) == 8
    assert {
        "Source Table",
        "Target Table",
        "Datatype Mapping",
        "Transformation Rule",
    }.issubset(mapping.columns)


def test_sql_is_converted_to_bigquery_and_ddl_is_generated(
    inputs: dict[str, object]
) -> None:
    result = modernize_sql(inputs["oracle_sql"])

    assert "TIMESTAMP_TRUNC" in result["bigquery_sql"]
    assert "TIMESTAMP_SUB" in result["bigquery_sql"]
    assert "SYSDATE" not in result["bigquery_sql"]
    assert "CREATE TABLE IF NOT EXISTS" in result["target_ddl"]
    assert "PARTITION BY DATE(order_date)" in result["target_ddl"]
    assert result["assumptions"]


def test_unexpected_oracle_sql_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing expected constructs"):
        modernize_sql("SELECT 1 FROM dual")


def test_every_informatica_step_has_cloud_translation(inputs: dict[str, object]) -> None:
    translation = modernize_etl(inputs["pipeline"])

    assert len(translation["steps"]) == len(inputs["pipeline"]["steps"])
    assert translation["steps"]["Cloud-native Implementation"].str.len().gt(0).all()
    assert translation["steps"]["Transformation Explanation"].str.len().gt(40).all()


def test_validation_includes_three_controls_and_manual_review() -> None:
    validation = validation_plan()

    assert set(validation["controls"]["Validation Type"]) == {
        "Row Count Validation",
        "Checksum Validation",
        "Business Rule Validation",
    }
    assert len(validation["manual_review_items"]) >= 5


def test_engagement_is_for_selected_oracle_candidate(
    engagement: dict[str, object]
) -> None:
    assert engagement["candidate"] == CANDIDATE_NAME
    assert engagement["narrative_source"] == "Deterministic fallback"


def test_implementation_package_contains_all_required_artifacts(
    engagement: dict[str, object], tmp_path: Path
) -> None:
    package_path = generate_implementation_package(engagement, tmp_path)
    expected_files = {
        "Executive_Summary.md",
        "Architecture.md",
        "Source_Target_Mapping.csv",
        "Converted_SQL.sql",
        "Target_DDL.sql",
        "ETL_Translation.md",
        "Validation_Report.md",
        "Implementation_Backlog.csv",
        "Assumptions.md",
        "Decision_Log.md",
        "manifest.json",
    }

    assert package_path.is_file()
    assert package_bytes(package_path)
    with ZipFile(package_path) as package:
        assert set(package.namelist()) == expected_files
        assert "Oracle Customer Analytics Warehouse" in package.read(
            "Executive_Summary.md"
        ).decode("utf-8")


def test_source_inputs_remain_dataframes(inputs: dict[str, object]) -> None:
    assert isinstance(inputs["portfolio"], pd.DataFrame)
    assert isinstance(inputs["dependencies"], pd.DataFrame)
    assert isinstance(inputs["mappings"], pd.DataFrame)
