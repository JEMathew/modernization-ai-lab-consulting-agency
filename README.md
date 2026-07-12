# Modernization AI Lab

Modernization AI Lab is a synthetic AI modernization agency demonstration. Sprint 1 provides a runnable Streamlit intake experience that safely loads and displays the Apex Aerospace Manufacturing enterprise platform portfolio.

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

Open the local URL printed by Streamlit, select **Load Apex Aerospace Demo**, and click the button with the same name to display the enterprise summary and full portfolio.

## Sprint 1 scope

This sprint includes safe JSON and CSV loading, required-column validation, the complete Apex synthetic dataset, and the Streamlit intake foundation. It intentionally excludes assessment scoring, 6R recommendations, prioritization, planning, migration conversion, package generation, approval workflows, and OpenAI calls.
