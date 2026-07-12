# Sprint 01 Result: Runnable Foundation and Complete Apex Synthetic Data

## Files created or modified

- `requirements.txt`
- `README.md`
- `app/__init__.py`
- `app/main.py`
- `engine/__init__.py`
- `engine/data_loader.py`
- `tests/test_data_loader.py`
- `demo_data/apex_aerospace/enterprise_profile.json`
- `demo_data/apex_aerospace/portfolio.csv`
- `demo_data/apex_aerospace/business_constraints.json`
- `demo_data/apex_aerospace/detailed_metadata.json`
- `demo_data/apex_aerospace/dependencies.csv`
- `demo_data/apex_aerospace/source_target_mapping.csv`
- `demo_data/apex_aerospace/sql/representative_query.sql`
- `demo_data/apex_aerospace/etl/representative_pipeline.json`
- `work_results/SPRINT-01-result.md`

## Commands executed

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
PYTHONPYCACHEPREFIX=/tmp/modernization-ai-lab-pycache .venv/bin/python -m compileall -q app engine tests
.venv/bin/python -c "from pathlib import Path; from engine.data_loader import load_json_safely, load_portfolio; root=Path('demo_data/apex_aerospace'); [load_json_safely(p) for p in [root/'enterprise_profile.json', root/'business_constraints.json', root/'detailed_metadata.json', root/'etl'/'representative_pipeline.json']]; [load_portfolio(root/'portfolio.csv')]; print('Apex JSON and portfolio validation passed')"
.venv/bin/python -c "from pathlib import Path; import pandas as pd; root=Path('demo_data/apex_aerospace'); assert not pd.read_csv(root/'dependencies.csv').empty; assert not pd.read_csv(root/'source_target_mapping.csv').empty; assert (root/'sql'/'representative_query.sql').read_text().strip(); print('Supporting Apex CSV and SQL validation passed')"
.venv/bin/python -m streamlit run app/main.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
git diff --check
```

The dependency installation was retried with approved network access after the sandboxed attempt could not reach the package index. The first syntax-check attempt used the macOS default bytecode cache outside the workspace and was blocked by filesystem permissions; it was rerun successfully with `PYTHONPYCACHEPREFIX` pointing to `/tmp`.

## Test results

- Pytest: **7 passed** in 0.29 seconds on the final run.
- Python syntax check: **passed** for `app`, `engine`, and `tests`.
- Apex JSON and primary portfolio validation: **passed**.
- Supporting Apex CSV and SQL validation: **passed**.
- Streamlit startup: **passed** at `http://localhost:8501`; server stopped cleanly after verification.
- Rendered UI verification: **passed**. The demo action displayed Apex Aerospace Manufacturing, Aerospace Manufacturing, the modernization objective, 7 platforms, $12,510,000 total annual cost, 3 critical platforms, and the enterprise portfolio table.
- Diff whitespace validation: **passed**.

## Acceptance criteria completed

- [x] Created a runnable Streamlit application.
- [x] Added the required title, subtitle, and synthetic-data disclaimer.
- [x] Displayed Intake, Assessment, Candidate, Migration Package, and Executive Review as five visible stages.
- [x] Added both intake choices; upload is intentionally display-only in Sprint 1.
- [x] Loaded and displayed the Apex enterprise summary and full portfolio on button click.
- [x] Populated all eight required Apex data files with valid synthetic data.
- [x] Added seven portfolio platforms, including all six specifically required systems.
- [x] Identified Oracle Customer Analytics Warehouse descriptively as the future flagship without calculating or displaying priority.
- [x] Added controlled JSON and CSV loading errors, required-column validation, and empty-portfolio rejection.
- [x] Added all seven requested loader tests.
- [x] Documented exact environment, installation, test, and startup commands.
- [x] Created `.venv`, installed dependencies, ran tests and syntax checks, and verified Streamlit startup and rendered behavior.
- [x] Kept future-sprint functionality out of the implementation.

## Known issues

- Upload processing is not implemented by design for Sprint 1; the control is visible and labeled accordingly.
- The system Python 3.9 build uses LibreSSL 2.8.3, so `urllib3` emits a `NotOpenSSLWarning` when Streamlit starts. The Sprint 1 application is local and makes no network or OpenAI calls, so this warning does not affect the demonstrated functionality.
- Watchdog is not installed; Streamlit reports it only as an optional development-performance enhancement.

## Exact demo steps

1. Open a terminal at the repository root.
2. Run `source .venv/bin/activate`.
3. Run `python -m streamlit run app/main.py`.
4. Open the local URL printed by Streamlit.
5. Confirm the title, subtitle, disclaimer, and five stage labels are visible.
6. Keep **Load Apex Aerospace Demo** selected.
7. Click **Load Apex Aerospace Demo**.
8. Confirm the Apex enterprise name, industry, modernization objective, 7-platform count, $12,510,000 annual cost, 3 critical-platform count, and full portfolio table appear.
9. Select **Upload Enterprise Package** to confirm the display-only upload control and Sprint 1 scope message are visible.
