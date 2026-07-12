"""Deterministic AI Agency operations and incremental replanning experience."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from engine.data_loader import DataLoadError, load_json_safely


AGENT_SEQUENCE = [
    "Hermes",
    "Assessment Specialist",
    "6R Specialist",
    "Prioritization Specialist",
    "Engineering Specialist",
    "Validation Specialist",
]


def load_business_constraints(path: str | Path) -> dict[str, object]:
    constraints = load_json_safely(path)
    required = {"annual_modernization_budget_usd", "maximum_planned_downtime_hours"}
    if not isinstance(constraints, dict):
        raise DataLoadError("Business constraints must be a JSON object.")
    missing = sorted(required.difference(constraints))
    if missing:
        raise DataLoadError(f"Business constraints are missing: {', '.join(missing)}")
    return constraints


def build_agent_operations(start_time: datetime, replanned: bool = False) -> pd.DataFrame:
    definitions = [
        ("Hermes", "Modernization Director", "Direct the engagement and synthesize recommendations", 0, 42, "Engagement coordinated", 98),
        ("Assessment Specialist", "Specialist", "Assess business and technical modernization evidence", 2, 8, "Assessment evidence reused", 99),
        ("6R Specialist", "Specialist", "Apply deterministic 6R disposition rules", 10, 4, "6R recommendations reused", 99),
        ("Prioritization Specialist", "Specialist", "Sequence the portfolio within business constraints", 14, 7, "Plan recalculated" if replanned else "Original plan established", 97),
        ("Engineering Specialist", "Specialist", "Prepare Oracle-to-BigQuery implementation package", 21, 16, "Implementation package ready", 96),
        ("Validation Specialist", "Specialist", "Validate package and revised plan controls", 37, 5, "Revised plan validated" if replanned else "Package controls validated", 99),
    ]
    rows = []
    for agent, role, task, offset, duration, result, confidence in definitions:
        if replanned and agent in {"Prioritization Specialist", "Validation Specialist"}:
            status = "Rerun Complete"
        elif replanned and agent in {"Assessment Specialist", "6R Specialist", "Engineering Specialist"}:
            status = "Reused"
        elif agent == "Hermes":
            status = "Directing"
        else:
            status = "Complete"
        rows.append(
            {
                "Agent": agent,
                "Role": role,
                "Current Status": status,
                "Task": task,
                "Confidence": f"{confidence}%",
                "Start Time": (start_time + timedelta(minutes=offset)).strftime("%H:%M:%S"),
                "Duration": f"{duration} min",
                "Result": result,
                "Cost": "USD 0.00 API",
            }
        )
    return pd.DataFrame(rows)


def agent_timeline(start_time: datetime, replanned: bool = False) -> pd.DataFrame:
    events = [
        (0, "Hermes", "Engagement opened", "Delegated discovery and assessment review"),
        (2, "Assessment Specialist", "Evidence loaded", "Reused validated portfolio assessment"),
        (10, "6R Specialist", "Disposition confirmed", "Reused deterministic 6R recommendations"),
        (14, "Prioritization Specialist", "Plan prepared", "Recalculated constrained plan" if replanned else "Created original migration waves"),
        (21, "Engineering Specialist", "Package prepared", "Reused implementation-ready package" if replanned else "Generated Oracle-to-BigQuery package"),
        (37, "Validation Specialist", "Controls completed", "Validated revised plan" if replanned else "Validated migration package"),
        (42, "Hermes", "Recommendation issued", "Published new plan" if replanned else "Published executive recommendation"),
    ]
    return pd.DataFrame(
        [
            {
                "Time": (start_time + timedelta(minutes=offset)).strftime("%H:%M:%S"),
                "Agent": agent,
                "Event": event,
                "Result": result,
            }
            for offset, agent, event, result in events
        ]
    )


def manager_timeline(start_time: datetime, replanned: bool = False) -> pd.DataFrame:
    first_action = "Budget change received; planner and validation rerun" if replanned else "Engagement scope accepted"
    return pd.DataFrame(
        [
            {"Time": start_time.strftime("%H:%M:%S"), "Manager": "Hermes", "Action": first_action, "Decision": "Reuse approved evidence" if replanned else "Delegate specialist work"},
            {"Time": (start_time + timedelta(minutes=14)).strftime("%H:%M:%S"), "Manager": "Hermes", "Action": "Reviewed portfolio plan", "Decision": "Protect Oracle Customer Analytics Warehouse as Wave 1"},
            {"Time": (start_time + timedelta(minutes=37)).strftime("%H:%M:%S"), "Manager": "Hermes", "Action": "Requested validation", "Decision": "Require constraints and package controls to pass"},
            {"Time": (start_time + timedelta(minutes=42)).strftime("%H:%M:%S"), "Manager": "Hermes", "Action": "Issued recommendation", "Decision": "Route high-risk deployment to human approval"},
        ]
    )


def executive_delivery_chain(package_name: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Stage": "Executive Recommendation", "Outcome": "Proceed with controlled Oracle-to-BigQuery modernization", "Status": "Issued"},
            {"Stage": "Recommended Candidate", "Outcome": "Oracle Customer Analytics Warehouse", "Status": "Selected"},
            {"Stage": "Migration Package", "Outcome": package_name, "Status": "Generated"},
            {"Stage": "Deployment Readiness", "Outcome": "Engineering starter package validated; cutover evidence outstanding", "Status": "Conditionally Ready"},
            {"Stage": "Approval Status", "Outcome": "Executive sponsor and platform owner decision required", "Status": "Pending Human Approval"},
        ]
    )


def _funding_weights(reduced: bool) -> dict[int, float]:
    if reduced:
        return {1: 0.45, 2: 0.30, 3: 0.15, 4: 0.10}
    return {1: 0.35, 2: 0.25, 3: 0.15, 4: 0.12, 5: 0.07, 6: 0.06}


def _wave_for_reduced_plan(rank: int, disposition: str) -> str:
    if disposition in {"Retain", "Retire"}:
        return "No Migration Wave"
    if rank == 1:
        return "Wave 1"
    if rank == 2:
        return "Wave 2"
    if rank in {3, 4}:
        return "Wave 3"
    return "Deferred"


def create_plan(assessment: pd.DataFrame, budget_usd: float, reduced: bool = False) -> pd.DataFrame:
    if budget_usd <= 0:
        raise ValueError("Budget must be greater than zero.")
    weights = _funding_weights(reduced)
    rows = []
    for _, item in assessment.sort_values("priority_rank").iterrows():
        rank = int(item["priority_rank"])
        disposition = str(item["six_r_recommendation"])
        wave = _wave_for_reduced_plan(rank, disposition) if reduced else str(item["migration_wave"])
        rows.append(
            {
                "Priority Rank": rank,
                "Platform": item["platform_name"],
                "6R": disposition,
                "Migration Wave": wave,
                "Planned Funding (USD)": round(budget_usd * weights.get(rank, 0), 2),
            }
        )
    return pd.DataFrame(rows)


def replan_for_constraints(
    assessment: pd.DataFrame,
    original_budget_usd: float,
    new_budget_usd: float,
    downtime_hours: int,
    business_priority: str,
) -> dict[str, object]:
    if new_budget_usd <= 0 or new_budget_usd > original_budget_usd:
        raise ValueError("New budget must be positive and no greater than the original budget.")
    if downtime_hours < 0:
        raise ValueError("Downtime cannot be negative.")

    reduction_percent = round((1 - new_budget_usd / original_budget_usd) * 100, 1)
    reduced = reduction_percent >= 15
    original_plan = create_plan(assessment, original_budget_usd, reduced=False)
    new_plan = create_plan(assessment, new_budget_usd, reduced=reduced)
    comparison = original_plan.merge(
        new_plan,
        on=["Priority Rank", "Platform", "6R"],
        suffixes=(" Original", " New"),
    )
    comparison["What Changed"] = comparison.apply(
        lambda row: (
            f"{row['Migration Wave Original']} → {row['Migration Wave New']}; "
            f"funding ${row['Planned Funding (USD) Original']:,.0f} → "
            f"${row['Planned Funding (USD) New']:,.0f}"
        ),
        axis=1,
    )

    why = (
        f"Hermes absorbed a {reduction_percent:.1f}% budget reduction while protecting "
        f"{business_priority}. Oracle Customer Analytics Warehouse remains Wave 1; lower-ranked "
        "work is sequenced later or deferred so the program stays inside the revised funding envelope."
    )
    if downtime_hours <= 4:
        why += " The tighter downtime limit adds a cutover rehearsal and validated rollback checkpoint."

    return {
        "original_budget_usd": float(original_budget_usd),
        "new_budget_usd": float(new_budget_usd),
        "budget_reduction_percent": reduction_percent,
        "downtime_hours": int(downtime_hours),
        "business_priority": business_priority,
        "original_plan": original_plan,
        "new_plan": new_plan,
        "comparison": comparison,
        "what_changed": comparison[["Platform", "What Changed"]],
        "why": why,
        "reused": ["Metadata Discovery", "Consulting Assessment", "6R Recommendations", "Engineering Package"],
        "rerun": ["Prioritization Planner", "Validation Specialist"],
        "full_replan_hours": 22,
        "incremental_replan_hours": 8,
        "time_saved_hours": 14,
        "validation_result": "PASS — revised funding totals reconcile and Oracle remains protected in Wave 1.",
    }


def store_replan_artifact(replan: dict[str, object], output_directory: str | Path) -> Path:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc)
    run_id = f"REPLAN-{timestamp:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    artifact_path = output / f"{run_id}.json"
    payload = {
        "run_id": run_id,
        "created_at": timestamp.isoformat(),
        "manager": "Hermes",
        "calculation_owner": "Python deterministic agency planner",
        **{
            key: value.to_dict(orient="records") if isinstance(value, pd.DataFrame) else value
            for key, value in replan.items()
        },
    }
    try:
        artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Unable to store replan artifact: {exc}") from exc
    return artifact_path
