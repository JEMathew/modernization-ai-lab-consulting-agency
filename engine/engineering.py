"""Deterministic Modernization Engineering Engagement for the Oracle candidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from .data_loader import DataLoadError, load_json_safely, load_portfolio


CANDIDATE_ID = "APX-PLT-001"
CANDIDATE_NAME = "Oracle Customer Analytics Warehouse"

TARGET_LAYERS = [
    {
        "sequence": 1,
        "component": "Oracle",
        "role": "System of record during transition",
        "why": "Preserves the governed production source while change-data capture and reconciliation establish migration confidence.",
    },
    {
        "sequence": 2,
        "component": "Cloud Storage Landing",
        "role": "Immutable ingestion and replay boundary",
        "why": "Decouples extraction from warehouse loading, retains source snapshots, and supports controlled replay and audit evidence.",
    },
    {
        "sequence": 3,
        "component": "BigQuery",
        "role": "Serverless analytical warehouse",
        "why": "Provides elastic SQL analytics, separates storage from compute, and removes Oracle infrastructure administration for the target workload.",
    },
    {
        "sequence": 4,
        "component": "Dataform",
        "role": "Versioned transformation and testing layer",
        "why": "Moves warehouse transformations into reviewable SQL assets with dependency management, assertions, and repeatable deployment.",
    },
    {
        "sequence": 5,
        "component": "Dataplex",
        "role": "Governance, catalog, quality, and lineage",
        "why": "Applies enterprise ownership, classification, lineage, and quality controls across landing and curated data products.",
    },
    {
        "sequence": 6,
        "component": "Looker",
        "role": "Governed semantic and consumption layer",
        "why": "Provides reusable business measures and controlled self-service access without embedding metric logic in individual reports.",
    },
]


def load_engineering_inputs(base_directory: str | Path) -> dict[str, object]:
    """Load and validate every source artifact required by Engagement 3."""

    base = Path(base_directory)
    inventory = load_json_safely(base / "engineering_inventory.json")
    metadata = load_json_safely(base / "detailed_metadata.json")
    pipeline = load_json_safely(base / "etl" / "representative_pipeline.json")
    portfolio = load_portfolio(base / "portfolio.csv")

    try:
        dependencies = pd.read_csv(base / "dependencies.csv")
        mappings = pd.read_csv(base / "source_target_mapping.csv")
        oracle_sql = (base / "sql" / "representative_query.sql").read_text(
            encoding="utf-8"
        )
    except FileNotFoundError as exc:
        raise DataLoadError(f"Engineering source file was not found: {exc.filename}") from exc
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise DataLoadError(f"Unable to load engineering source data: {exc}") from exc

    if not isinstance(inventory, dict) or inventory.get("platform_id") != CANDIDATE_ID:
        raise DataLoadError("Engineering inventory does not describe the selected Oracle candidate.")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("platforms"), list):
        raise DataLoadError("Detailed metadata must contain a platforms list.")
    if not isinstance(pipeline, dict) or not isinstance(pipeline.get("steps"), list):
        raise DataLoadError("Representative ETL pipeline must contain a steps list.")
    if dependencies.empty or mappings.empty or not oracle_sql.strip():
        raise DataLoadError("Engineering source artifacts must not be empty.")

    return {
        "inventory": inventory,
        "metadata": metadata,
        "pipeline": pipeline,
        "portfolio": portfolio,
        "dependencies": dependencies,
        "mappings": mappings,
        "oracle_sql": oracle_sql,
    }


def metadata_discovery(inputs: dict[str, object]) -> dict[str, object]:
    inventory = dict(inputs["inventory"])
    required = {
        "schemas",
        "tables",
        "views",
        "stored_procedures",
        "etl_jobs",
        "reports",
        "data_volume_tb",
        "owners",
    }
    missing = sorted(required.difference(inventory))
    if missing:
        raise DataLoadError(f"Engineering inventory is missing: {', '.join(missing)}")
    return {key: inventory[key] for key in required}


def dependency_analysis(inputs: dict[str, object]) -> dict[str, object]:
    dependencies = inputs["dependencies"].copy()
    portfolio = inputs["portfolio"]
    names = dict(zip(portfolio["platform_id"], portfolio["platform_name"]))
    related = dependencies[
        (dependencies["upstream_platform_id"] == CANDIDATE_ID)
        | (dependencies["downstream_platform_id"] == CANDIDATE_ID)
    ].copy()
    related["upstream"] = related["upstream_platform_id"].map(names)
    related["downstream"] = related["downstream_platform_id"].map(names)
    related["business_impact"] = related.apply(
        lambda row: (
            f"{row['business_process']} is a {str(row['criticality']).lower()} "
            f"{str(row['frequency']).lower()} service; interruption would delay customer "
            "analytics ingestion or executive reporting."
        ),
        axis=1,
    )
    critical = related[related["criticality"].isin(["Critical", "High"])]

    graph_lines = ["digraph dependencies {", '  rankdir="LR";']
    for _, row in related.iterrows():
        upstream = str(row["upstream"]).replace('"', "'")
        downstream = str(row["downstream"]).replace('"', "'")
        color = "#d62728" if row["criticality"] == "Critical" else "#f59f00"
        graph_lines.append(
            f'  "{upstream}" -> "{downstream}" '
            f'[label="{row["interface_type"]} / {row["frequency"]}", color="{color}"];'
        )
    graph_lines.append("}")

    display_columns = [
        "upstream",
        "downstream",
        "interface_type",
        "frequency",
        "criticality",
        "business_process",
        "business_impact",
    ]
    return {
        "upstream": sorted(
            related.loc[related["downstream_platform_id"] == CANDIDATE_ID, "upstream"].unique()
        ),
        "downstream": sorted(
            related.loc[related["upstream_platform_id"] == CANDIDATE_ID, "downstream"].unique()
        ),
        "critical_dependencies": critical[display_columns].reset_index(drop=True),
        "dependencies": related[display_columns].reset_index(drop=True),
        "graph_dot": "\n".join(graph_lines),
        "business_impact": related["business_impact"].tolist(),
    }


def target_architecture() -> dict[str, object]:
    return {
        "layers": pd.DataFrame(TARGET_LAYERS),
        "flow": "Oracle → Cloud Storage Landing → BigQuery → Dataform → Dataplex → Looker",
        "explanation": (
            "This architecture separates ingestion, analytical storage, transformation, "
            "governance, and consumption into independently controlled layers. It supports "
            "replayable migration, reconciled cutover, versioned transformations, governed "
            "data products, and a consistent semantic layer while keeping Oracle authoritative "
            "until validation and business acceptance are complete."
        ),
        "narrative_source": "Deterministic fallback",
    }


def source_target_mapping(inputs: dict[str, object]) -> pd.DataFrame:
    mappings = inputs["mappings"].copy()

    def datatype(rule: str) -> str:
        normalized = rule.casefold()
        if "number(18 2)" in normalized:
            return "NUMBER(18,2) → NUMERIC"
        if "number" in normalized and "int64" in normalized:
            return "NUMBER → INT64"
        if "date" in normalized:
            return "DATE → TIMESTAMP"
        if "timestamp" in normalized:
            return "TIMESTAMP → TIMESTAMP"
        return "VARCHAR2 → STRING"

    result = pd.DataFrame(
        {
            "Source Table": mappings["source_object"],
            "Source Column": mappings["source_column"],
            "Target Table": mappings["target_object"],
            "Target Column": mappings["target_column"],
            "Datatype Mapping": mappings["transformation_rule"].map(datatype),
            "Transformation Rule": mappings["transformation_rule"],
            "Data Classification": mappings["data_classification"],
        }
    )
    return result


def modernize_sql(oracle_sql: str) -> dict[str, object]:
    """Translate the representative known workload into deterministic BigQuery SQL."""

    required_tokens = ["TRUNC(", "ADD_MONTHS(", "SYSDATE", "customer_dim", "order_fact"]
    missing = [token for token in required_tokens if token not in oracle_sql]
    if missing:
        raise ValueError(f"Representative Oracle SQL is missing expected constructs: {missing}")

    bigquery_sql = """-- BigQuery Standard SQL
SELECT
  c.customer_id,
  c.customer_name,
  TIMESTAMP_TRUNC(o.order_date, MONTH) AS order_month,
  COUNT(DISTINCT o.order_id) AS order_count,
  SUM(o.net_amount) AS net_revenue,
  MAX(s.event_timestamp) AS latest_service_event
FROM `apex_customer_analytics.customer_dim` AS c
JOIN `apex_customer_analytics.order_fact` AS o
  ON o.customer_key = c.customer_key
LEFT JOIN `apex_customer_analytics.service_event_fact` AS s
  ON s.customer_key = c.customer_key
WHERE o.order_date >= TIMESTAMP_SUB(
  TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH), INTERVAL 12 MONTH
)
  AND c.customer_status = 'ACTIVE'
GROUP BY
  c.customer_id,
  c.customer_name,
  order_month
ORDER BY
  order_month DESC,
  net_revenue DESC;
"""
    target_ddl = """-- BigQuery Standard SQL target DDL
CREATE SCHEMA IF NOT EXISTS `apex_customer_analytics`
OPTIONS(location = 'US');

CREATE TABLE IF NOT EXISTS `apex_customer_analytics.customer_dim` (
  customer_key INT64 NOT NULL,
  customer_id INT64 NOT NULL,
  customer_name STRING,
  email_address STRING,
  customer_status STRING,
  effective_timestamp TIMESTAMP
)
CLUSTER BY customer_id;

CREATE TABLE IF NOT EXISTS `apex_customer_analytics.order_fact` (
  order_id INT64 NOT NULL,
  customer_key INT64 NOT NULL,
  order_date TIMESTAMP NOT NULL,
  net_amount NUMERIC
)
PARTITION BY DATE(order_date)
CLUSTER BY customer_key;

CREATE TABLE IF NOT EXISTS `apex_customer_analytics.service_event_fact` (
  customer_key INT64 NOT NULL,
  serial_number STRING,
  event_timestamp TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY customer_key, serial_number;
"""
    assumptions = [
        "Oracle DATE values are normalized to UTC BigQuery TIMESTAMP values before load.",
        "Oracle NUMBER identifiers fit within signed BigQuery INT64 range.",
        "NET_AMOUNT precision fits BigQuery NUMERIC; out-of-range values require manual review.",
        "The target dataset is deployed in an approved US region for this synthetic scenario.",
        "Customer keys remain stable through cutover and preserve referential integrity.",
        "CURRENT_TIMESTAMP is an acceptable deterministic replacement for Oracle SYSDATE semantics.",
    ]
    return {
        "source_sql": oracle_sql,
        "bigquery_sql": bigquery_sql,
        "target_ddl": target_ddl,
        "assumptions": assumptions,
    }


ETL_TRANSLATIONS = {
    "Incremental database extract": (
        "Datastream change data capture → Cloud Storage raw zone",
        "Capture committed inserts and updates with source timestamps, persist immutable "
        "Avro objects, and retain checkpoints for replay without querying the full source.",
    ),
    "Secure API ingestion": (
        "Cloud Run ingestion service → Pub/Sub → Cloud Storage raw zone",
        "Authenticate to the service API, validate the message envelope, publish durable "
        "events, and archive the original payload before transformation.",
    ),
    "Lookup and survivorship transformation": (
        "Dataform incremental model in BigQuery",
        "Standardize customer identifiers, apply deterministic match precedence, reject "
        "ambiguous identities, and record survivorship decisions in an audit table.",
    ),
    "Transactional warehouse load": (
        "Dataform dependency graph → partitioned BigQuery tables",
        "Build dimensions before facts, use idempotent MERGE statements, enforce unique keys, "
        "and publish only after Dataform assertions pass.",
    ),
    "Control totals and audit report": (
        "Cloud Composer orchestration → BigQuery validation → Cloud Monitoring",
        "Compare source and target counts, checksums, and business rules; block publication "
        "on failure and emit an auditable run result with alerting.",
    ),
}


def modernize_etl(pipeline: dict[str, object]) -> dict[str, object]:
    translated_steps = []
    for step in pipeline["steps"]:
        operation = step["operation"]
        target, explanation = ETL_TRANSLATIONS.get(
            operation,
            (
                "Cloud Composer managed task",
                "Preserve source ordering, inputs, outputs, retry behavior, and audit metadata.",
            ),
        )
        translated_steps.append(
            {
                "Sequence": step["sequence"],
                "Source Step": step["name"],
                "Informatica Operation": operation,
                "Cloud-native Implementation": target,
                "Transformation Explanation": explanation,
            }
        )
    return {
        "pipeline_name": pipeline["pipeline_name"],
        "target_pipeline": "Customer Analytics Cloud-Native Incremental Load",
        "orchestration": "Cloud Composer coordinates Datastream, Cloud Run, Dataform, BigQuery, and validation tasks.",
        "schedule": pipeline["schedule"],
        "service_level_target": pipeline["service_level_target"],
        "steps": pd.DataFrame(translated_steps),
        "failure_policy": (
            "Retry transient tasks twice, stop downstream publication on validation failure, "
            "alert Data Operations, and restart from the last durable checkpoint."
        ),
        "explanation": (
            "The translation preserves the source pipeline's sequence and service objective "
            "while separating capture, durable landing, transformation, publication, and "
            "validation into observable managed services."
        ),
        "narrative_source": "Deterministic fallback",
    }


def validation_plan() -> dict[str, object]:
    controls = pd.DataFrame(
        [
            {
                "Validation Type": "Row Count Validation",
                "Scope": "Each table and business date partition",
                "Pass Criterion": "Source count equals accepted target rows plus quarantined rows",
                "Automation": "Oracle count extract compared with BigQuery INFORMATION_SCHEMA results",
            },
            {
                "Validation Type": "Checksum Validation",
                "Scope": "Business keys and material measures",
                "Pass Criterion": "Canonical SHA-256 aggregates match for every validation partition",
                "Automation": "Normalize nulls and datatypes then compare ordered field hashes",
            },
            {
                "Validation Type": "Business Rule Validation",
                "Scope": "Customer orders revenue and service events",
                "Pass Criterion": "All defined assertions pass with zero unexplained exceptions",
                "Automation": "Dataform assertions and scheduled BigQuery validation queries",
            },
        ]
    )
    business_rules = [
        "Every order references an existing customer key.",
        "Net revenue by month reconciles to Oracle within USD 0.01 rounding tolerance.",
        "Active customers have a non-null customer identifier and status.",
        "Service-event timestamps are not later than the validation run timestamp.",
        "Customer email values are either null or conform to the approved format.",
    ]
    manual_review_items = [
        "Confirm Oracle session timezone and daylight-saving behavior before timestamp conversion.",
        "Review NUMERIC overflow candidates and agree a BIGNUMERIC exception policy.",
        "Approve handling of duplicate customer identities rejected by survivorship logic.",
        "Validate Looker measures with Customer Experience and Finance report owners.",
        "Witness rollback and replay procedures during the production cutover rehearsal.",
        "Approve access controls for Customer PII and export-controlled serial numbers.",
    ]
    return {
        "controls": controls,
        "business_rules": business_rules,
        "manual_review_items": manual_review_items,
    }


def implementation_backlog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("ENG3-001", "Foundation", "Create approved landing bucket and BigQuery datasets", "Cloud Platform", "Encryption, retention, regions, and service accounts pass policy checks"),
            ("ENG3-002", "Discovery", "Baseline Oracle schemas, tables, views, procedures, and jobs", "Data Engineering", "Catalog counts reconcile to the approved inventory"),
            ("ENG3-003", "Ingestion", "Configure Datastream and immutable landing conventions", "Data Engineering", "CDC records land with checkpoints and replay evidence"),
            ("ENG3-004", "Warehouse", "Deploy BigQuery DDL, partitioning, and clustering", "Analytics Engineering", "DDL deploys and mapped datatypes pass test loads"),
            ("ENG3-005", "Transformation", "Implement Dataform dimensions, facts, and assertions", "Analytics Engineering", "All models and assertions pass in the non-production environment"),
            ("ENG3-006", "Governance", "Register assets, ownership, classifications, and lineage in Dataplex", "Data Governance", "PII and commercial classifications are searchable and enforced"),
            ("ENG3-007", "Consumption", "Validate Looker semantic measures and report parity", "Business Intelligence", "Business owners approve revenue and service measures"),
            ("ENG3-008", "Validation", "Automate row counts, checksums, and business rules", "Quality Engineering", "Validation report contains no unexplained exceptions"),
            ("ENG3-009", "Cutover", "Execute rehearsal, rollback test, and production readiness review", "Program Delivery", "Owners approve go/no-go evidence and rollback timing"),
        ],
        columns=["ID", "Workstream", "Backlog Item", "Owner", "Acceptance Criterion"],
    )


def build_engineering_engagement(base_directory: str | Path) -> dict[str, object]:
    inputs = load_engineering_inputs(base_directory)
    sql = modernize_sql(inputs["oracle_sql"])
    return {
        "candidate": CANDIDATE_NAME,
        "metadata": metadata_discovery(inputs),
        "dependencies": dependency_analysis(inputs),
        "architecture": target_architecture(),
        "mapping": source_target_mapping(inputs),
        "sql": sql,
        "etl": modernize_etl(inputs["pipeline"]),
        "validation": validation_plan(),
        "backlog": implementation_backlog(),
        "assumptions": sql["assumptions"]
        + [
            "Oracle remains the production system of record until cutover approval.",
            "The representative SQL and ETL pipeline are sufficient starter-package exemplars, not a complete estate conversion.",
            "All services use approved private connectivity and least-privilege service identities.",
        ],
        "decision_log": [
            "Use Cloud Storage as an immutable landing and replay boundary.",
            "Use BigQuery as the target analytical warehouse.",
            "Use Dataform for versioned SQL transformation and assertions.",
            "Use Dataplex for catalog, lineage, quality, and governance controls.",
            "Use Looker as the governed semantic consumption layer.",
            "Require reconciliation and business-owner acceptance before Oracle cutover.",
        ],
        "executive_summary": (
            "Apex Aerospace should implement the Oracle Customer Analytics Warehouse "
            "modernization through a controlled, replayable migration to BigQuery. The "
            "starter package establishes the target architecture, eight source-to-target "
            "mappings, representative SQL and DDL, a cloud-native ETL translation, validation "
            "controls, delivery backlog, assumptions, and decisions. Oracle remains authoritative "
            "until automated reconciliation and business acceptance are complete."
        ),
        "narrative_source": "Deterministic fallback",
    }


def _markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) + "\n"


def _dataframe_markdown(dataframe: pd.DataFrame) -> str:
    """Render tabular evidence without optional formatting dependencies."""

    return "```csv\n" + dataframe.to_csv(index=False) + "```\n"


def generate_implementation_package(
    engagement: dict[str, object], output_directory: str | Path
) -> Path:
    """Generate and persist the implementation-ready ZIP package."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc)
    package_id = f"APEX-ORACLE-BQ-{timestamp:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    package_path = output / f"{package_id}.zip"

    architecture = engagement["architecture"]
    etl = engagement["etl"]
    validation = engagement["validation"]
    architecture_md = (
        "# Target Architecture\n\n"
        f"**Flow:** {architecture['flow']}\n\n{architecture['explanation']}\n\n"
        + _dataframe_markdown(architecture["layers"])
    )
    etl_md = (
        "# ETL Translation\n\n"
        f"**Target pipeline:** {etl['target_pipeline']}\n\n{etl['explanation']}\n\n"
        + _dataframe_markdown(etl["steps"])
        + f"\n\n**Failure policy:** {etl['failure_policy']}\n"
    )
    validation_md = (
        "# Validation Report\n\n"
        + _dataframe_markdown(validation["controls"])
        + "\n\n## Business Rules\n\n"
        + _markdown_list(validation["business_rules"])
        + "\n## Manual Review Items\n\n"
        + _markdown_list(validation["manual_review_items"])
    )
    decision_md = "# Decision Log\n\n" + "\n".join(
        f"{index}. {decision}" for index, decision in enumerate(engagement["decision_log"], 1)
    )

    manifest = {
        "package_id": package_id,
        "created_at": timestamp.isoformat(),
        "candidate": engagement["candidate"],
        "calculation_owner": "Python deterministic engineering engine",
        "narrative_source": engagement["narrative_source"],
    }
    files = {
        "Executive_Summary.md": "# Executive Summary\n\n" + engagement["executive_summary"] + "\n",
        "Architecture.md": architecture_md,
        "Source_Target_Mapping.csv": engagement["mapping"].to_csv(index=False),
        "Converted_SQL.sql": engagement["sql"]["bigquery_sql"],
        "Target_DDL.sql": engagement["sql"]["target_ddl"],
        "ETL_Translation.md": etl_md,
        "Validation_Report.md": validation_md,
        "Implementation_Backlog.csv": engagement["backlog"].to_csv(index=False),
        "Assumptions.md": "# Assumptions\n\n" + _markdown_list(engagement["assumptions"]),
        "Decision_Log.md": decision_md + "\n",
        "manifest.json": json.dumps(manifest, indent=2),
    }

    try:
        with ZipFile(package_path, "w", compression=ZIP_DEFLATED) as package:
            for filename, content in files.items():
                package.writestr(filename, content)
    except OSError as exc:
        raise RuntimeError(f"Unable to generate implementation package: {exc}") from exc
    return package_path


def package_bytes(package_path: str | Path) -> bytes:
    path = Path(package_path)
    try:
        return BytesIO(path.read_bytes()).getvalue()
    except OSError as exc:
        raise RuntimeError(f"Unable to read implementation package: {exc}") from exc
