# Modernization AI Lab

Modernization AI Lab is a synthetic AI modernization consulting engagement. The application loads the Apex Aerospace Manufacturing enterprise portfolio and runs a deterministic modernization assessment that selects the Oracle Customer Analytics Warehouse as the recommended modernization candidate.

All organizations, systems, volumes, costs, and recommendations in this repository are synthetic and created solely for demonstration.

## Prerequisites

- Python 3.9 or newer
- A shell opened at the repository root

## Setup and run

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the test suite:

```bash
python -m pytest
```

Start Streamlit:

```bash
python -m streamlit run app/main.py
```

Open the local URL printed by Streamlit, select **Load Apex Aerospace Demo**, and click the button with the same name to display the enterprise summary and full portfolio. Click **Run Modernization Assessment** to calculate the portfolio assessment, store its JSON artifact, and view Hermes's consulting recommendation.

## Sprint 1 scope

This sprint includes safe JSON and CSV loading, required-column validation, the complete Apex synthetic dataset, and the Streamlit intake foundation. It intentionally excludes assessment scoring, 6R recommendations, prioritization, planning, migration conversion, package generation, approval workflows, and OpenAI calls.

## Engagement 2: Modernization Assessment

Engagement 2 adds a deterministic consulting assessment without changing the Engagement 1 synthetic dataset or loader behavior. Python calculates business value, technical debt, cloud readiness, AI readiness, complexity, migration risk, annual operating cost, priority, 6R disposition, rank, and migration wave. No AI service is used for calculations.

The priority score is a bounded 0–100 weighted calculation:

```text
25% business value
+ 15% technical debt
+ 15% cloud readiness
+ 15% AI readiness
+ 15% normalized operating-cost pressure
- 8% complexity
- 7% migration risk
```

Completed assessment runs are stored as JSON artifacts under `generated_packages/assessments/`. Runtime artifacts are intentionally excluded from Git.

## Engagement 3: Modernization Engineering

After the Oracle Customer Analytics Warehouse is selected, click **Prepare Implementation Ready Package** to run the engineering engagement. The application displays metadata discovery, dependency analysis and graph, the Oracle-to-Google-Cloud target architecture, source-to-target mappings, converted BigQuery SQL, target DDL, cloud-native ETL translation, validation controls, manual-review items, and an implementation backlog.

The resulting ZIP is stored under `generated_packages/implementation/` and can be downloaded in the application. It contains:

- Executive Summary
- Architecture
- Source Target Mapping
- Converted SQL
- Target DDL
- ETL Translation
- Validation Report
- Implementation Backlog
- Assumptions
- Decision Log
- Package manifest

All mappings, conversions, validations, and package contents are deterministic. Architecture, migration, and executive-summary narratives use the deterministic offline fallback; no OpenAI call is required.
