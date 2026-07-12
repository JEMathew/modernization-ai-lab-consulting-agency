# Codex Engineering Instructions

## Mission

Build the smallest reliable Track 3 demo for Modernization AI Lab.

## Stack

- Python
- Streamlit
- Pandas
- SQLite
- Pydantic
- OpenAI Python SDK
- Pytest

Do not introduce React, FastAPI, Docker, Kubernetes, or cloud databases unless
the existing application requires them.

## Product rules

- This is an AI agency, not a chatbot.
- All enterprise data is synthetic.
- Numeric scores must be calculated by Python.
- LLMs explain results but do not invent numeric scores.
- Every assessment run must create stored artifacts.
- High-risk decisions require human approval.
- The app must work without an OpenAI call by using a deterministic fallback.
- Preserve a working happy path after every change.
- Add tests for scoring, 6R, prioritization, and replanning.
- Do not expose API keys.
- Do not implement features outside the current work packet.

## MVP scenario

Apex Aerospace Manufacturing has multiple legacy platforms. The app must
select the Oracle Customer Analytics Warehouse and generate an
Oracle-to-BigQuery implementation-ready starter package.

## Definition of done

A packet is done only when:

1. The app starts.
2. Required tests pass.
3. The feature is visible in the UI.
4. Generated output is stored.
5. Error states are handled.
6. Existing features still work.

## Completion report

After each packet, create a report in work_results containing:

- files changed
- commands run
- tests run
- test results
- acceptance criteria met
- known issues
- demo steps
