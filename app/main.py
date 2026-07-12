"""Streamlit entry point for the Modernization AI Lab Sprint 1 demo."""

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from engine.data_loader import DataLoadError, load_enterprise_profile, load_portfolio


ROOT_DIR = Path(__file__).resolve().parents[1]
APEX_DATA_DIR = ROOT_DIR / "demo_data" / "apex_aerospace"

load_dotenv(ROOT_DIR / ".env")

st.set_page_config(page_title="Modernization AI Lab", page_icon="🏭", layout="wide")

st.title("Modernization AI Lab")
st.subheader("AI Modernization Agency for Enterprise Data Platforms")
st.info(
    "All organizations, systems, volumes, costs, and recommendations shown are "
    "synthetic and created solely for demonstration."
)

stages = ["Intake", "Assessment", "Candidate", "Migration Package", "Executive Review"]
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
