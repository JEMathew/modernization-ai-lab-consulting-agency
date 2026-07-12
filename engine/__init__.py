"""Core data-loading utilities for Modernization AI Lab."""

from .assessment import (
    SCORE_COLUMNS,
    assess_portfolio,
    consulting_recommendation,
    recommend_6r,
    select_modernization_candidate,
    store_assessment_artifact,
)
from .data_loader import (
    DataLoadError,
    EnterpriseProfile,
    REQUIRED_PORTFOLIO_COLUMNS,
    load_enterprise_profile,
    load_json_safely,
    load_portfolio,
)
from .engineering import (
    build_engineering_engagement,
    generate_implementation_package,
    package_bytes,
)

__all__ = [
    "SCORE_COLUMNS",
    "assess_portfolio",
    "consulting_recommendation",
    "DataLoadError",
    "EnterpriseProfile",
    "REQUIRED_PORTFOLIO_COLUMNS",
    "load_enterprise_profile",
    "load_json_safely",
    "load_portfolio",
    "build_engineering_engagement",
    "generate_implementation_package",
    "package_bytes",
    "recommend_6r",
    "select_modernization_candidate",
    "store_assessment_artifact",
]
