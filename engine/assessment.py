"""Deterministic modernization consulting assessment engine.

Every score and recommendation in this module is calculated by Python. No AI
or external service participates in assessment decisions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd


SCORE_COLUMNS = (
    "business_value",
    "technical_debt",
    "cloud_readiness",
    "ai_readiness",
    "complexity",
    "migration_risk",
    "priority_score",
)

CRITICALITY_SCORE = {"critical": 90, "high": 76, "medium": 60, "low": 38}
LIFECYCLE_DEBT = {
    "end of support": 92,
    "extended support": 68,
    "vendor supported": 38,
    "strategic": 20,
}
PLATFORM_VALUE = {
    "data warehouse": 8,
    "data lake": 7,
    "data integration": 6,
    "business intelligence": 5,
    "operational reporting": 4,
    "data mart": 3,
}
PLATFORM_CLOUD_READINESS = {
    "data warehouse": 82,
    "data lake": 72,
    "data integration": 66,
    "business intelligence": 78,
    "operational reporting": 70,
    "data mart": 76,
}
PLATFORM_AI_READINESS = {
    "data warehouse": 86,
    "data lake": 90,
    "data integration": 68,
    "business intelligence": 72,
    "operational reporting": 60,
    "data mart": 64,
}
PLATFORM_COMPLEXITY = {
    "data warehouse": 18,
    "data lake": 24,
    "data integration": 22,
    "business intelligence": 12,
    "operational reporting": 14,
    "data mart": 10,
}


def _bounded(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _normalized(value: float) -> str:
    return str(value).strip().casefold()


def _business_value(row: pd.Series) -> float:
    criticality = CRITICALITY_SCORE.get(_normalized(row["criticality"]), 50)
    platform_value = PLATFORM_VALUE.get(_normalized(row["platform_type"]), 2)
    return _bounded(criticality + platform_value)


def _technical_debt(row: pd.Series) -> float:
    debt = LIFECYCLE_DEBT.get(_normalized(row["lifecycle_status"]), 50)
    technology = _normalized(row["primary_technology"])
    version = _normalized(row["version"])
    if any(term in technology for term in ("oracle", "teradata", "cloudera", "cognos")):
        debt += 7
    if version in {"12.2", "2016", "6.3", "11.1"}:
        debt += 5
    return _bounded(debt)


def _cloud_readiness(row: pd.Series) -> float:
    readiness = PLATFORM_CLOUD_READINESS.get(_normalized(row["platform_type"]), 65)
    if _normalized(row["hosting"]) == "on-premises":
        readiness -= 10
    readiness -= min(float(row["data_volume_tb"]) / 50, 20)
    return _bounded(readiness)


def _ai_readiness(row: pd.Series) -> float:
    readiness = PLATFORM_AI_READINESS.get(_normalized(row["platform_type"]), 55)
    description = _normalized(row["description"])
    if any(term in description for term in ("analytics", "telemetry", "customer")):
        readiness += 5
    if "reporting" in description:
        readiness -= 3
    return _bounded(readiness)


def _complexity(row: pd.Series) -> float:
    volume = float(row["data_volume_tb"])
    volume_component = min(45, 10 + volume / 20)
    platform_component = PLATFORM_COMPLEXITY.get(_normalized(row["platform_type"]), 15)
    criticality_component = {
        "critical": 18,
        "high": 12,
        "medium": 7,
        "low": 3,
    }.get(_normalized(row["criticality"]), 8)
    return _bounded(volume_component + platform_component + criticality_component)


def recommend_6r(row: pd.Series, technical_debt: float, complexity: float) -> str:
    """Return one of the six deterministic modernization dispositions."""

    criticality = _normalized(row["criticality"])
    lifecycle = _normalized(row["lifecycle_status"])
    platform_type = _normalized(row["platform_type"])

    if criticality == "low" and float(row["annual_cost_usd"]) > 0:
        return "Retire"
    if criticality == "medium" and lifecycle in {"vendor supported", "strategic"}:
        return "Retain"
    if platform_type in {"business intelligence", "data integration"} and technical_debt >= 35:
        return "Replace"
    if lifecycle == "end of support" or complexity >= 80:
        return "Refactor"
    if platform_type in {"data warehouse", "data lake"} or technical_debt >= 65:
        return "Replatform"
    return "Rehost"


def _migration_wave(priority_score: float, migration_risk: float, disposition: str) -> str:
    if disposition in {"Retain", "Retire"}:
        return "No Migration Wave"
    if priority_score >= 60 and migration_risk < 80:
        return "Wave 1"
    if priority_score >= 48:
        return "Wave 2"
    return "Wave 3"


def assess_portfolio(portfolio: pd.DataFrame) -> pd.DataFrame:
    """Calculate portfolio scores, 6R recommendation, rank, and migration wave."""

    if portfolio.empty:
        raise ValueError("Cannot assess an empty portfolio.")

    assessed_rows: list[dict[str, object]] = []
    maximum_cost = float(portfolio["annual_cost_usd"].max())

    for _, row in portfolio.iterrows():
        business_value = _business_value(row)
        technical_debt = _technical_debt(row)
        cloud_readiness = _cloud_readiness(row)
        ai_readiness = _ai_readiness(row)
        complexity = _complexity(row)
        criticality_score = CRITICALITY_SCORE.get(_normalized(row["criticality"]), 50)
        migration_risk = _bounded(
            complexity * 0.45 + technical_debt * 0.35 + criticality_score * 0.20
        )
        operating_cost = float(row["annual_cost_usd"])
        cost_pressure = operating_cost / maximum_cost * 100 if maximum_cost else 0
        priority_score = _bounded(
            business_value * 0.25
            + technical_debt * 0.15
            + cloud_readiness * 0.15
            + ai_readiness * 0.15
            + cost_pressure * 0.15
            - complexity * 0.08
            - migration_risk * 0.07
        )
        disposition = recommend_6r(row, technical_debt, complexity)

        assessed_rows.append(
            {
                "platform_id": row["platform_id"],
                "platform_name": row["platform_name"],
                "business_value": business_value,
                "technical_debt": technical_debt,
                "cloud_readiness": cloud_readiness,
                "ai_readiness": ai_readiness,
                "complexity": complexity,
                "migration_risk": migration_risk,
                "operating_cost_usd": operating_cost,
                "priority_score": priority_score,
                "six_r_recommendation": disposition,
                "migration_wave": _migration_wave(priority_score, migration_risk, disposition),
            }
        )

    assessment = pd.DataFrame(assessed_rows).sort_values(
        ["priority_score", "business_value", "platform_name"],
        ascending=[False, False, True],
    )
    assessment.insert(0, "priority_rank", range(1, len(assessment) + 1))
    return assessment.reset_index(drop=True)


def select_modernization_candidate(assessment: pd.DataFrame) -> pd.Series:
    """Select the highest-ranked migration candidate using deterministic results."""

    candidates = assessment[
        ~assessment["six_r_recommendation"].isin(["Retain", "Retire"])
    ]
    if candidates.empty:
        raise ValueError("Assessment contains no modernization candidates.")
    return candidates.sort_values("priority_rank").iloc[0]


def consulting_recommendation(candidate: pd.Series) -> str:
    """Produce Hermes's deterministic consulting recommendation."""

    return (
        f"Proceed with {candidate['platform_name']} as the recommended modernization "
        f"candidate in {candidate['migration_wave']}. The portfolio evidence supports a "
        f"{candidate['six_r_recommendation']} disposition, with business value "
        f"{candidate['business_value']:.1f}, priority {candidate['priority_score']:.1f}, "
        f"and migration risk {candidate['migration_risk']:.1f}. Establish an executive "
        "sponsor, confirm source-system owners, and validate operational constraints "
        "before implementation planning."
    )


def store_assessment_artifact(
    assessment: pd.DataFrame,
    output_directory: str | Path,
    enterprise_id: str,
) -> Path:
    """Persist a completed assessment as a timestamped JSON artifact."""

    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc)
    run_id = f"ASSESS-{timestamp:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    artifact_path = directory / f"{run_id}.json"
    payload = {
        "run_id": run_id,
        "enterprise_id": enterprise_id,
        "created_at": timestamp.isoformat(),
        "calculation_owner": "Python deterministic assessment engine",
        "assessment": assessment.to_dict(orient="records"),
    }
    try:
        artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Unable to store assessment artifact: {exc}") from exc
    return artifact_path
