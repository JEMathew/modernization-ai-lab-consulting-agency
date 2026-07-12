"""Safe, explicit loaders for the synthetic enterprise demo data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, ValidationError


class DataLoadError(RuntimeError):
    """Raised when enterprise demo data cannot be loaded or validated."""


class EnterpriseProfile(BaseModel):
    """Validated enterprise information displayed during intake."""

    model_config = ConfigDict(extra="allow")

    enterprise_id: str
    enterprise_name: str
    industry: str
    description: str
    modernization_objective: str
    disclaimer: str


REQUIRED_PORTFOLIO_COLUMNS = {
    "platform_id",
    "platform_name",
    "platform_type",
    "primary_technology",
    "version",
    "hosting",
    "business_owner",
    "technical_owner",
    "annual_cost_usd",
    "data_volume_tb",
    "criticality",
    "lifecycle_status",
    "description",
}


def _existing_file(path: str | Path) -> Path:
    file_path = Path(path)
    if not file_path.is_file():
        raise DataLoadError(f"Data file was not found: {file_path}")
    return file_path


def load_json_safely(path: str | Path) -> Any:
    """Load JSON with controlled errors for missing, empty, or malformed files."""

    file_path = _existing_file(path)
    try:
        raw_content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DataLoadError(f"Unable to read JSON file {file_path}: {exc}") from exc

    if not raw_content.strip():
        raise DataLoadError(f"JSON file is empty: {file_path}")

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise DataLoadError(
            f"Malformed JSON in {file_path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def load_enterprise_profile(path: str | Path) -> EnterpriseProfile:
    """Load and validate the enterprise profile."""

    data = load_json_safely(path)
    if not isinstance(data, dict):
        raise DataLoadError(f"Enterprise profile must be a JSON object: {path}")
    try:
        return EnterpriseProfile.model_validate(data)
    except ValidationError as exc:
        raise DataLoadError(f"Invalid enterprise profile in {path}: {exc}") from exc


def load_portfolio(
    path: str | Path,
    required_columns: set[str] | None = None,
) -> pd.DataFrame:
    """Load a non-empty platform portfolio and validate its required columns."""

    file_path = _existing_file(path)
    expected_columns = required_columns or REQUIRED_PORTFOLIO_COLUMNS
    try:
        portfolio = pd.read_csv(file_path)
    except pd.errors.EmptyDataError as exc:
        raise DataLoadError(f"Portfolio CSV is empty: {file_path}") from exc
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise DataLoadError(f"Unable to read portfolio CSV {file_path}: {exc}") from exc

    missing_columns = sorted(expected_columns.difference(portfolio.columns))
    if missing_columns:
        raise DataLoadError(
            f"Portfolio CSV {file_path} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )
    if portfolio.empty:
        raise DataLoadError(f"Portfolio CSV contains no platform records: {file_path}")

    for column in ("annual_cost_usd", "data_volume_tb"):
        try:
            portfolio[column] = pd.to_numeric(portfolio[column], errors="raise")
        except (TypeError, ValueError) as exc:
            raise DataLoadError(
                f"Portfolio column '{column}' must contain numeric values: {file_path}"
            ) from exc

    return portfolio
