"""Streamlit entry point for the Modernization AI Lab consulting engagement."""

from datetime import datetime, timezone
from html import escape
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import streamlit as st
from dotenv import load_dotenv

from engine.agency import (
    agent_timeline,
    build_agent_operations,
    create_plan,
    executive_delivery_chain,
    load_business_constraints,
    manager_timeline,
    replan_for_constraints,
    store_replan_artifact,
)
from engine.assessment import (
    assess_portfolio,
    consulting_recommendation,
    select_modernization_candidate,
    store_assessment_artifact,
)
from engine.data_loader import DataLoadError, load_enterprise_profile, load_portfolio
from engine.engineering import (
    build_engineering_engagement,
    generate_implementation_package,
    package_bytes,
)


ROOT_DIR = REPOSITORY_ROOT
APEX_DATA_DIR = ROOT_DIR / "demo_data" / "apex_aerospace"
ASSESSMENT_OUTPUT_DIR = ROOT_DIR / "generated_packages" / "assessments"
IMPLEMENTATION_OUTPUT_DIR = ROOT_DIR / "generated_packages" / "implementation"
REPLAN_OUTPUT_DIR = ROOT_DIR / "generated_packages" / "replans"


def request_agency_replan() -> None:
    st.session_state["agency_replan_requested"] = True


def apply_thirty_percent_reduction() -> None:
    st.session_state["agency_budget"] = round(
        float(st.session_state["agency_original_budget"]) * 0.70, 2
    )
    st.session_state["agency_replan_requested"] = True


def render_agent_cards(operations) -> None:
    icons = ["◆", "◈", "◇", "◉", "⬡", "✓"]
    columns = st.columns(3)
    for index, (_, agent) in enumerate(operations.iterrows()):
        status_class = "status-active" if agent["Current Status"] == "Directing" else "status-ready"
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="agent-card">
                    <div class="agent-card-top">
                        <span class="agent-icon">{icons[index]}</span>
                        <span class="agent-status {status_class}">{escape(str(agent['Current Status']))}</span>
                    </div>
                    <div class="agent-name">{escape(str(agent['Agent']))}</div>
                    <div class="agent-role">{escape(str(agent['Role']))}</div>
                    <div class="agent-task">{escape(str(agent['Task']))}</div>
                    <div class="agent-meta">
                        <span>Confidence <strong>{escape(str(agent['Confidence']))}</strong></span>
                        <span>{escape(str(agent['Duration']))}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_timeline(events) -> None:
    timeline_parts = ['<div class="agency-timeline">']
    for _, event in events.iterrows():
        timeline_parts.append(
            f'<div class="timeline-event"><div class="timeline-marker"></div>'
            f'<div class="timeline-time">{escape(str(event["Time"]))}</div>'
            f'<div class="timeline-copy"><strong>{escape(str(event["Agent"]))}</strong>'
            f'<span>{escape(str(event["Event"]))} · {escape(str(event["Result"]))}</span>'
            f'</div></div>'
        )
    timeline_parts.append("</div>")
    st.markdown("".join(timeline_parts), unsafe_allow_html=True)


def render_deliverable_cards(deliverables) -> None:
    icons = ["✦", "◎", "▣", "◒", "✓"]
    columns = st.columns(5)
    for index, (_, deliverable) in enumerate(deliverables.iterrows()):
        with columns[index]:
            st.markdown(
                f"""
                <div class="deliverable-card">
                    <div class="deliverable-icon">{icons[index]}</div>
                    <div class="deliverable-stage">{escape(str(deliverable['Stage']))}</div>
                    <div class="deliverable-status">{escape(str(deliverable['Status']))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

load_dotenv(ROOT_DIR / ".env")

st.set_page_config(page_title="Modernization AI Lab", page_icon="🏭", layout="wide")

st.markdown(
    """
    <style>
        :root {
            --ink: #15233b;
            --muted: #61708a;
            --navy: #0b1f3a;
            --blue: #2563eb;
            --teal: #0f9f8f;
            --purple: #7057d9;
            --surface: #f6f8fc;
            --line: #dfe6f1;
        }
        .stApp { background: linear-gradient(180deg, #f8faff 0%, #ffffff 34rem); color: var(--ink); }
        .block-container { max-width: 1500px; padding-top: 2rem; padding-bottom: 5rem; }
        h1, h2, h3 { color: var(--navy); letter-spacing: -0.02em; }
        h2 { margin-top: 2.5rem !important; }
        [data-testid="stMetric"] {
            background: rgba(255,255,255,.9); border: 1px solid var(--line);
            border-radius: 14px; padding: 1rem 1.1rem; box-shadow: 0 8px 24px rgba(26,54,93,.06);
        }
        [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
        [data-testid="stStatusWidget"], [data-testid="stAlert"] { border-radius: 14px; }
        .stButton > button, .stDownloadButton > button { border-radius: 10px; font-weight: 650; }
        .hero-panel {
            background: linear-gradient(125deg, #0b1f3a 0%, #153f71 58%, #0f766e 120%);
            border-radius: 22px; padding: 2.1rem 2.3rem; color: white;
            box-shadow: 0 20px 50px rgba(11,31,58,.18); margin-bottom: 1rem;
        }
        .hero-kicker { color: #7dd3fc; font-size: .78rem; font-weight: 750; letter-spacing: .16em; text-transform: uppercase; }
        .hero-title { font-size: 2.45rem; font-weight: 760; letter-spacing: -.04em; margin: .35rem 0 .25rem; }
        .hero-subtitle { color: #d8e8f8; font-size: 1.08rem; max-width: 780px; }
        .disclaimer-panel { border-left: 3px solid var(--teal); background: #eefbf8; color: #28544e; padding: .8rem 1rem; border-radius: 0 10px 10px 0; margin: 1rem 0 1.25rem; }
        .stage-card { min-height: 88px; border: 1px solid var(--line); border-radius: 13px; background: white; padding: .8rem; box-shadow: 0 5px 18px rgba(27,51,84,.05); }
        .stage-card.complete { border-color: #a7e2d8; background: #f0fdfa; }
        .stage-card.current { border-color: #8eb1ff; background: #eff6ff; box-shadow: 0 8px 24px rgba(37,99,235,.12); }
        .stage-number { color: var(--blue); font-size: .72rem; font-weight: 800; letter-spacing: .12em; }
        .stage-label { color: var(--navy); font-size: .9rem; font-weight: 700; margin-top: .35rem; line-height: 1.25; }
        .section-eyebrow { color: var(--blue); font-size: .74rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; margin-bottom: -.6rem; }
        .summary-card { background: linear-gradient(135deg, #eff6ff, #f5f3ff); border: 1px solid #cbd9f5; border-radius: 18px; padding: 1.5rem 1.7rem; box-shadow: 0 10px 32px rgba(55,78,132,.08); }
        .summary-label { color: var(--purple); font-size: .75rem; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
        .summary-title { color: var(--navy); font-size: 1.28rem; font-weight: 750; margin: .35rem 0 .5rem; }
        .summary-body { color: #40516d; line-height: 1.65; }
        .agent-card { min-height: 218px; background: white; border: 1px solid var(--line); border-radius: 16px; padding: 1.15rem; margin-bottom: 1rem; box-shadow: 0 8px 26px rgba(22,45,78,.07); }
        .agent-card-top { display: flex; align-items: center; justify-content: space-between; }
        .agent-icon { color: var(--teal); font-size: 1.4rem; }
        .agent-status { font-size: .7rem; font-weight: 800; padding: .25rem .5rem; border-radius: 999px; text-transform: uppercase; letter-spacing: .05em; }
        .status-active { color: #1d4ed8; background: #dbeafe; }
        .status-ready { color: #087568; background: #d9f7f1; }
        .agent-name { color: var(--navy); font-weight: 760; font-size: 1.05rem; margin-top: .85rem; }
        .agent-role { color: var(--purple); font-size: .78rem; font-weight: 700; margin-top: .15rem; }
        .agent-task { color: var(--muted); font-size: .86rem; line-height: 1.45; margin: .8rem 0; min-height: 52px; }
        .agent-meta { border-top: 1px solid #edf1f7; padding-top: .7rem; display: flex; justify-content: space-between; color: var(--muted); font-size: .76rem; }
        .agency-timeline { border-left: 2px solid #bfdbfe; margin: .6rem 0 1.25rem 5rem; padding-left: 1.4rem; }
        .timeline-event { position: relative; display: grid; grid-template-columns: 80px 1fr; gap: .75rem; padding: 0 0 1.15rem; }
        .timeline-marker { position: absolute; width: 12px; height: 12px; border-radius: 50%; background: var(--blue); border: 3px solid #dbeafe; left: -1.82rem; top: .2rem; }
        .timeline-time { color: var(--blue); font-size: .76rem; font-weight: 750; }
        .timeline-copy { display: flex; flex-direction: column; color: var(--navy); font-size: .88rem; }
        .timeline-copy span { color: var(--muted); font-size: .8rem; margin-top: .15rem; }
        .deliverable-card { min-height: 150px; background: white; border: 1px solid var(--line); border-top: 3px solid var(--teal); border-radius: 14px; padding: 1rem; box-shadow: 0 7px 22px rgba(24,50,82,.06); }
        .deliverable-icon { color: var(--teal); font-size: 1.25rem; }
        .deliverable-stage { color: var(--navy); font-size: .82rem; font-weight: 750; margin-top: .65rem; line-height: 1.3; }
        .deliverable-status { color: var(--purple); font-size: .72rem; font-weight: 750; margin-top: .55rem; }
        @media (max-width: 900px) { .hero-title { font-size: 2rem; } .deliverable-card { min-height: auto; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-panel">
        <div class="hero-kicker">Enterprise AI Consulting Engagement</div>
        <div class="hero-title">Modernization AI Lab</div>
        <div class="hero-subtitle">AI Modernization Agency for Enterprise Data Platforms</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="disclaimer-panel">◌ All organizations, systems, volumes, costs, and recommendations shown are synthetic and created solely for demonstration.</div>
    """,
    unsafe_allow_html=True,
)

stages = [
    "Intake",
    "Consulting Assessment",
    "Recommended Modernization Candidate",
    "Implementation Ready Package",
    "Executive Review",
]
completed_stage = 0
if "enterprise_profile" in st.session_state:
    completed_stage = 1
if "assessment" in st.session_state:
    completed_stage = 3
if "engineering_engagement" in st.session_state:
    completed_stage = 4

stage_columns = st.columns(len(stages))
for index, (column, stage) in enumerate(zip(stage_columns, stages), start=1):
    stage_class = "complete" if index <= completed_stage else "current" if index == completed_stage + 1 else ""
    column.markdown(
        f"""
        <div class="stage-card {stage_class}">
            <div class="stage-number">0{index}</div>
            <div class="stage-label">{escape(stage)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.progress(completed_stage / len(stages), text=f"Engagement progress · {completed_stage} of {len(stages)} stages complete")

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
            st.session_state.pop("engineering_engagement", None)
            st.session_state.pop("implementation_package", None)
            st.session_state.pop("agency_replan", None)
            st.session_state.pop("agency_replan_artifact", None)
            st.rerun()
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
            st.session_state.pop("engineering_engagement", None)
            st.session_state.pop("implementation_package", None)
            st.session_state.pop("agency_replan", None)
            st.session_state.pop("agency_replan_artifact", None)
            st.rerun()
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

    st.divider()
    st.header("Modernization Engineering Engagement")
    st.write(
        "Prepare the implementation-ready starter package for the selected Oracle Customer "
        "Analytics Warehouse modernization to BigQuery."
    )
    st.caption(
        "Engineering mappings, conversions, controls, and package artifacts are generated "
        "deterministically. Narrative sections use the offline deterministic fallback."
    )
    if st.button("Prepare Implementation Ready Package", type="primary"):
        try:
            engineering_engagement = build_engineering_engagement(APEX_DATA_DIR)
            implementation_package = generate_implementation_package(
                engineering_engagement, IMPLEMENTATION_OUTPUT_DIR
            )
            st.session_state["engineering_engagement"] = engineering_engagement
            st.session_state["implementation_package"] = str(implementation_package)
            st.session_state.pop("agency_replan", None)
            st.session_state.pop("agency_replan_artifact", None)
            st.rerun()
        except (DataLoadError, RuntimeError, ValueError) as exc:
            st.session_state.pop("engineering_engagement", None)
            st.session_state.pop("implementation_package", None)
            st.error(f"The implementation package could not be prepared. {exc}")

if "engineering_engagement" in st.session_state:
    engineering = st.session_state["engineering_engagement"]
    package_path = Path(st.session_state["implementation_package"])

    st.success(
        "Implementation-ready package generated and stored as "
        f"`{package_path.name}`."
    )

    st.header("1. Metadata Discovery")
    metadata = engineering["metadata"]
    metadata_columns = st.columns(4)
    metadata_columns[0].metric("Schemas", f"{metadata['schemas']:,}")
    metadata_columns[1].metric("Tables", f"{metadata['tables']:,}")
    metadata_columns[2].metric("Views", f"{metadata['views']:,}")
    metadata_columns[3].metric("Stored Procedures", f"{metadata['stored_procedures']:,}")
    metadata_columns = st.columns(4)
    metadata_columns[0].metric("ETL Jobs", f"{metadata['etl_jobs']:,}")
    metadata_columns[1].metric("Reports", f"{metadata['reports']:,}")
    metadata_columns[2].metric("Data Volume", f"{metadata['data_volume_tb']:,} TB")
    metadata_columns[3].metric("Named Owners", f"{len(metadata['owners']):,}")
    st.subheader("Owners")
    owner_rows = [
        {"Accountability": role.replace("_", " ").title(), "Owner": owner}
        for role, owner in metadata["owners"].items()
    ]
    st.dataframe(owner_rows, width="stretch", hide_index=True)

    st.header("2. Dependency Analysis")
    dependencies = engineering["dependencies"]
    dependency_columns = st.columns(2)
    with dependency_columns[0]:
        st.subheader("Upstream")
        for upstream in dependencies["upstream"]:
            st.write(f"- {upstream}")
    with dependency_columns[1]:
        st.subheader("Downstream")
        for downstream in dependencies["downstream"]:
            st.write(f"- {downstream}")
    st.subheader("Critical Dependencies")
    st.dataframe(
        dependencies["critical_dependencies"].rename(
            columns={
                "upstream": "Upstream",
                "downstream": "Downstream",
                "interface_type": "Interface",
                "frequency": "Frequency",
                "criticality": "Criticality",
                "business_process": "Business Process",
                "business_impact": "Business Impact",
            }
        ),
        width="stretch",
        hide_index=True,
    )
    st.subheader("Dependency Graph")
    st.graphviz_chart(dependencies["graph_dot"], width="stretch")
    st.subheader("Business Impact")
    for impact in dependencies["business_impact"]:
        st.write(f"- {impact}")

    st.header("3. Target Architecture")
    architecture = engineering["architecture"]
    st.markdown(f"### {architecture['flow']}")
    st.dataframe(
        architecture["layers"].rename(
            columns={
                "sequence": "Sequence",
                "component": "Component",
                "role": "Role",
                "why": "Why",
            }
        ),
        width="stretch",
        hide_index=True,
    )
    st.markdown("**Why this architecture**")
    st.write(architecture["explanation"])
    st.caption(f"Narrative source: {architecture['narrative_source']}")

    st.header("4. Source-to-Target Mapping")
    st.dataframe(engineering["mapping"], width="stretch", hide_index=True)

    st.header("5. SQL Modernization")
    sql_tabs = st.tabs(["Oracle Source SQL", "BigQuery SQL", "Target DDL", "Assumptions"])
    with sql_tabs[0]:
        st.code(engineering["sql"]["source_sql"], language="sql")
    with sql_tabs[1]:
        st.code(engineering["sql"]["bigquery_sql"], language="sql")
    with sql_tabs[2]:
        st.code(engineering["sql"]["target_ddl"], language="sql")
    with sql_tabs[3]:
        for assumption in engineering["sql"]["assumptions"]:
            st.write(f"- {assumption}")

    st.header("6. ETL Modernization")
    etl = engineering["etl"]
    st.write(f"**Informatica pipeline:** {etl['pipeline_name']}")
    st.write(f"**Cloud-native pipeline:** {etl['target_pipeline']}")
    st.write(f"**Orchestration:** {etl['orchestration']}")
    st.write(etl["explanation"])
    st.dataframe(etl["steps"], width="stretch", hide_index=True)
    st.write(f"**Failure policy:** {etl['failure_policy']}")
    st.caption(f"Narrative source: {etl['narrative_source']}")

    st.header("7. Validation")
    validation = engineering["validation"]
    st.dataframe(validation["controls"], width="stretch", hide_index=True)
    validation_columns = st.columns(2)
    with validation_columns[0]:
        st.subheader("Business Rule Validation")
        for rule in validation["business_rules"]:
            st.write(f"- {rule}")
    with validation_columns[1]:
        st.subheader("Manual Review Items")
        for item in validation["manual_review_items"]:
            st.write(f"- {item}")

    st.header("8. Implementation Ready Package")
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">Executive Summary</div>
            <div class="summary-title">Oracle Customer Analytics Warehouse → BigQuery</div>
            <div class="summary-body">{escape(str(engineering['executive_summary']))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Executive summary source: {engineering['narrative_source']}")
    st.download_button(
        "Download Implementation Ready Package",
        data=package_bytes(package_path),
        file_name=package_path.name,
        mime="application/zip",
        type="primary",
    )
    st.write(
        "Package contents: Executive Summary, Architecture, Source Target Mapping, "
        "Converted SQL, Target DDL, ETL Translation, Validation Report, Implementation "
        "Backlog, Assumptions, Decision Log, and manifest."
    )
    st.subheader("Implementation Backlog")
    st.dataframe(engineering["backlog"], width="stretch", hide_index=True)
    package_columns = st.columns(2)
    with package_columns[0]:
        st.subheader("Assumptions")
        for assumption in engineering["assumptions"]:
            st.write(f"- {assumption}")
    with package_columns[1]:
        st.subheader("Decision Log")
        for index, decision in enumerate(engineering["decision_log"], start=1):
            st.write(f"{index}. {decision}")

    st.divider()
    st.header("AI Agency Operations")
    st.caption(
        "This is the operating view of the AI consulting agency—not an executive dashboard. "
        "Hermes directs specialists, reuses approved evidence, and routes high-risk decisions "
        "to human approval."
    )

    constraints = load_business_constraints(APEX_DATA_DIR / "business_constraints.json")
    original_budget = float(constraints["annual_modernization_budget_usd"])
    original_downtime = int(constraints["maximum_planned_downtime_hours"])
    if "agency_original_budget" not in st.session_state:
        st.session_state["agency_original_budget"] = original_budget
    if "agency_budget" not in st.session_state:
        st.session_state["agency_budget"] = original_budget
    if "agency_downtime" not in st.session_state:
        st.session_state["agency_downtime"] = original_downtime
    if "agency_business_priority" not in st.session_state:
        st.session_state["agency_business_priority"] = "Customer Analytics Continuity"
    if "agency_start_time" not in st.session_state:
        st.session_state["agency_start_time"] = datetime.now(timezone.utc).isoformat()
    if "agency_replan_requested" not in st.session_state:
        st.session_state["agency_replan_requested"] = False

    agency_start = datetime.fromisoformat(st.session_state["agency_start_time"])
    replanned = "agency_replan" in st.session_state
    phase = "Adaptive Replanning Complete" if replanned else "Implementation Package Prepared"

    with st.status(
        f"Hermes is directing the agency · Current Engagement Phase: {phase}",
        expanded=True,
        state="complete",
    ):
        st.write("Specialists are coordinated through deterministic handoffs and stored artifacts.")
        st.progress(1.0, text="Agency delivery evidence synchronized")

    st.markdown('<div class="section-eyebrow">Agency Roster</div>', unsafe_allow_html=True)
    st.subheader("Agent Cards")
    operations = build_agent_operations(agency_start, replanned=replanned)
    render_agent_cards(operations)
    with st.expander("View complete agent operating details"):
        st.dataframe(operations, width="stretch", hide_index=True)

    timeline_tabs = st.tabs(["Agent Timeline", "Manager Timeline"])
    with timeline_tabs[0]:
        agent_events = agent_timeline(agency_start, replanned=replanned)
        render_timeline(agent_events)
        st.dataframe(
            agent_events,
            width="stretch",
            hide_index=True,
        )
    with timeline_tabs[1]:
        st.dataframe(
            manager_timeline(agency_start, replanned=replanned),
            width="stretch",
            hide_index=True,
        )

    st.markdown('<div class="section-eyebrow">Live Engagement</div>', unsafe_allow_html=True)
    st.subheader("Current Engagement Status")
    status_columns = st.columns(3)
    status_columns[0].metric("Current Phase", phase)
    status_columns[1].metric("Active Manager", "Hermes")
    status_columns[2].metric("Approval", "Pending Human Approval")

    st.markdown('<div class="section-eyebrow">Consulting Outputs</div>', unsafe_allow_html=True)
    st.subheader("Consulting Deliverables")
    delivery_chain = executive_delivery_chain(package_path.name)
    render_deliverable_cards(delivery_chain)
    st.dataframe(
        delivery_chain,
        width="stretch",
        hide_index=True,
    )

    st.divider()
    st.header("Business Constraints — Live Replanning")
    st.write(
        "Change a constraint and Hermes will preserve completed evidence, rerun only the "
        "planner and validation specialist, and publish a revised plan."
    )
    constraint_columns = st.columns(3)
    with constraint_columns[0]:
        st.number_input(
            "Budget (USD)",
            min_value=1_000_000.0,
            max_value=original_budget,
            step=50_000.0,
            key="agency_budget",
            on_change=request_agency_replan,
        )
    with constraint_columns[1]:
        st.slider(
            "Downtime (hours)",
            min_value=0,
            max_value=24,
            key="agency_downtime",
            on_change=request_agency_replan,
        )
    with constraint_columns[2]:
        st.selectbox(
            "Business Priority",
            (
                "Customer Analytics Continuity",
                "Supply Chain Resilience",
                "Operating Cost Reduction",
            ),
            key="agency_business_priority",
            on_change=request_agency_replan,
        )

    st.button(
        "Apply 30% Budget Reduction",
        type="primary",
        on_click=apply_thirty_percent_reduction,
    )

    if st.session_state["agency_replan_requested"]:
        replan_completed = False
        try:
            agency_replan = replan_for_constraints(
                assessment,
                original_budget_usd=original_budget,
                new_budget_usd=float(st.session_state["agency_budget"]),
                downtime_hours=int(st.session_state["agency_downtime"]),
                business_priority=st.session_state["agency_business_priority"],
            )
            replan_artifact = store_replan_artifact(agency_replan, REPLAN_OUTPUT_DIR)
            st.session_state["agency_replan"] = agency_replan
            st.session_state["agency_replan_artifact"] = str(replan_artifact)
            replan_completed = True
        except (RuntimeError, ValueError) as exc:
            st.session_state.pop("agency_replan", None)
            st.session_state.pop("agency_replan_artifact", None)
            st.error(f"Hermes could not create the revised plan. {exc}")
        finally:
            st.session_state["agency_replan_requested"] = False
        if replan_completed:
            st.rerun()

    st.subheader("Original Plan")
    original_plan = create_plan(assessment, original_budget)
    st.dataframe(original_plan, width="stretch", hide_index=True)

    if "agency_replan" in st.session_state:
        agency_replan = st.session_state["agency_replan"]
        st.success(
            f"Hermes created a new plan for a "
            f"{agency_replan['budget_reduction_percent']:.1f}% budget reduction and stored "
            f"`{Path(st.session_state['agency_replan_artifact']).name}`."
        )
        reuse_columns = st.columns(2)
        with reuse_columns[0]:
            st.markdown("**Reused—no rerun**")
            for item in agency_replan["reused"]:
                st.write(f"- {item}")
        with reuse_columns[1]:
            st.markdown("**Rerun by Hermes**")
            for item in agency_replan["rerun"]:
                st.write(f"- {item}")

        st.subheader("New Plan")
        st.dataframe(agency_replan["new_plan"], width="stretch", hide_index=True)
        st.subheader("What Changed")
        st.dataframe(agency_replan["what_changed"], width="stretch", hide_index=True)
        st.subheader("Why")
        st.write(agency_replan["why"])

        value_columns = st.columns(3)
        value_columns[0].metric(
            "Full Replan Effort", f"{agency_replan['full_replan_hours']} hours"
        )
        value_columns[1].metric(
            "Incremental Replan", f"{agency_replan['incremental_replan_hours']} hours"
        )
        value_columns[2].metric(
            "Time Saved", f"{agency_replan['time_saved_hours']} hours", delta="64% faster"
        )
        st.write(f"**Validation result:** {agency_replan['validation_result']}")
