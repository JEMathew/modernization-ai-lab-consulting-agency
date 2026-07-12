"""Streamlit entry point for the Modernization AI Lab consulting engagement."""

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from engine.assessment import (
    assess_portfolio,
    consulting_recommendation,
    select_modernization_candidate,
    store_assessment_artifact,
)
from engine.data_loader import DataLoadError, load_enterprise_profile, load_portfolio


ROOT_DIR = Path(__file__).resolve().parents[1]
APEX_DATA_DIR = ROOT_DIR / "demo_data" / "apex_aerospace"
ASSESSMENT_OUTPUT_DIR = ROOT_DIR / "generated_packages" / "assessments"

load_dotenv(ROOT_DIR / ".env")

st.set_page_config(page_title="Modernization AI Lab", page_icon="🏭", layout="wide")

st.title("Modernization AI Lab")
st.subheader("AI Modernization Agency for Enterprise Data Platforms")
st.info(
    "All organizations, systems, volumes, costs, and recommendations shown are "
    "synthetic and created solely for demonstration."
)

stages = [
    "Intake",
    "Consulting Assessment",
    "Recommended Modernization Candidate",
    "Implementation Ready Package",
    "Executive Review",
]
stage_columns = st.columns(len(stages))
for index, (column, stage) in enumerate(zip(stage_columns, stages), start=1):
    column.markdown(f"**{index}. {stage}**")

st.divider()
st.header("Intake")
intake_choice = st.radio(
    "Choose an intake method",
    ("Load Apex Aerospace Demo", "Upload Enterprise Package"),
    horizontal=True,
)

if intake_choice == "Upload Enterprise Package":
    st.file_uploader(
        "Upload Enterprise Package",
        type=("zip", "json", "csv"),
        help="Upload processing will be added in a future sprint.",
    )
    st.caption("Upload processing is not available in Sprint 1.")
else:
    if st.button("Load Apex Aerospace Demo", type="primary"):
        try:
            st.session_state["enterprise_profile"] = load_enterprise_profile(
                APEX_DATA_DIR / "enterprise_profile.json"
            )
            st.session_state["portfolio"] = load_portfolio(APEX_DATA_DIR / "portfolio.csv")
            st.session_state.pop("assessment", None)
            st.session_state.pop("assessment_artifact", None)
        except DataLoadError as exc:
            st.session_state.pop("enterprise_profile", None)
            st.session_state.pop("portfolio", None)
            st.error(f"Apex demo could not be loaded. {exc}")

if "enterprise_profile" in st.session_state and "portfolio" in st.session_state:
    profile = st.session_state["enterprise_profile"]
    portfolio = st.session_state["portfolio"]

    st.success("Apex Aerospace demo loaded successfully.")
    st.subheader(profile.enterprise_name)
    st.write(f"**Industry:** {profile.industry}")
    st.write(f"**Modernization objective:** {profile.modernization_objective}")

    metric_columns = st.columns(3)
    metric_columns[0].metric("Platforms", f"{len(portfolio):,}")
    metric_columns[1].metric(
        "Total annual platform cost",
        f"${portfolio['annual_cost_usd'].sum():,.0f}",
    )
    critical_count = portfolio["criticality"].str.casefold().eq("critical").sum()
    metric_columns[2].metric("Critical platforms", f"{critical_count:,}")

    st.subheader("Enterprise Platform Portfolio")
    st.dataframe(
        portfolio,
        width="stretch",
        hide_index=True,
        column_config={
            "annual_cost_usd": st.column_config.NumberColumn(
                "Annual Cost (USD)", format="$%d"
            ),
            "data_volume_tb": st.column_config.NumberColumn("Data Volume (TB)", format="%.0f"),
        },
    )

    st.divider()
    st.header("Consulting Assessment")
    st.write(
        "Evaluate the portfolio using a transparent consulting model for business value, "
        "technical health, modernization readiness, delivery complexity, migration risk, "
        "and operating-cost pressure."
    )
    st.caption(
        "Python owns every numeric calculation, priority rank, 6R disposition, and "
        "migration-wave assignment. No AI is used for calculations."
    )

    if st.button("Run Modernization Assessment", type="primary"):
        try:
            assessment = assess_portfolio(portfolio)
            artifact_path = store_assessment_artifact(
                assessment,
                ASSESSMENT_OUTPUT_DIR,
                profile.enterprise_id,
            )
            st.session_state["assessment"] = assessment
            st.session_state["assessment_artifact"] = str(artifact_path)
        except (RuntimeError, ValueError) as exc:
            st.session_state.pop("assessment", None)
            st.session_state.pop("assessment_artifact", None)
            st.error(f"The consulting assessment could not be completed. {exc}")

if "assessment" in st.session_state:
    assessment = st.session_state["assessment"]
    candidate = select_modernization_candidate(assessment)

    st.success(
        "Consulting assessment completed and stored as "
        f"`{Path(st.session_state['assessment_artifact']).name}`."
    )

    assessment_display = assessment.rename(
        columns={
            "priority_rank": "Priority Rank",
            "platform_name": "Platform",
            "business_value": "Business Value",
            "technical_debt": "Technical Debt",
            "cloud_readiness": "Cloud Readiness",
            "ai_readiness": "AI Readiness",
            "complexity": "Complexity",
            "migration_risk": "Risk",
            "operating_cost_usd": "Operating Cost (USD)",
            "priority_score": "Priority",
            "six_r_recommendation": "6R",
            "migration_wave": "Migration Wave",
        }
    )[
        [
            "Priority Rank",
            "Platform",
            "Business Value",
            "Technical Debt",
            "Cloud Readiness",
            "AI Readiness",
            "Complexity",
            "Risk",
            "Operating Cost (USD)",
            "Priority",
            "6R",
            "Migration Wave",
        ]
    ]

    def highlight_candidate(row):
        if row["Platform"] == "Oracle Customer Analytics Warehouse":
            return ["background-color: #fff3bf; font-weight: 600"] * len(row)
        return [""] * len(row)

    st.dataframe(
        assessment_display.style.apply(highlight_candidate, axis=1),
        width="stretch",
        hide_index=True,
        column_config={
            "Operating Cost (USD)": st.column_config.NumberColumn(format="$%d"),
            "Business Value": st.column_config.NumberColumn(format="%.1f"),
            "Technical Debt": st.column_config.NumberColumn(format="%.1f"),
            "Cloud Readiness": st.column_config.NumberColumn(format="%.1f"),
            "AI Readiness": st.column_config.NumberColumn(format="%.1f"),
            "Complexity": st.column_config.NumberColumn(format="%.1f"),
            "Risk": st.column_config.NumberColumn(format="%.1f"),
            "Priority": st.column_config.NumberColumn(format="%.1f"),
        },
    )

    st.header("Recommended Modernization Candidate")
    st.success("Oracle Customer Analytics Warehouse")
    candidate_metrics = st.columns(5)
    candidate_metrics[0].metric("Business Value", f"{candidate['business_value']:.1f}")
    candidate_metrics[1].metric("Complexity", f"{candidate['complexity']:.1f}")
    candidate_metrics[2].metric("Risk", f"{candidate['migration_risk']:.1f}")
    candidate_metrics[3].metric("Priority", f"{candidate['priority_score']:.1f}")
    candidate_metrics[4].metric("Migration Wave", candidate["migration_wave"])
    st.write(f"**Deterministic 6R recommendation:** {candidate['six_r_recommendation']}")

    st.subheader("Hermes — Modernization Director")
    st.markdown("**Consulting Recommendation**")
    st.write(consulting_recommendation(candidate))
