> This file mirrors `.github/copilot-instructions.md`; keep both in sync when either changes.

# CLAUDE.md — Shell-Cheniere Global LNG Shock Relative-Value Model

## Purpose
Scenario and Monte Carlo model comparing Shell and Cheniere under global LNG supply disruption.

## Tech stack
- Python; dependencies in `requirements.txt`
- Key libraries: `numpy`, `pandas`, `matplotlib`, `reportlab`, `yfinance`

## Folder structure
- `config/` (2 files)
- `data/` (1 files)
- `outputs/` (6 files)
- `src/` (5 files)
- `tests/` (1 files)
- `.gitattributes`
- `CITATION.cff`
- `METHODOLOGY.md`
- `MODEL_CARD.md`
- `README.md`
- `main.py`
- `pyproject.toml`
- `requirements.txt`

## Setup, run, test
Commands documented in README.md (referenced files exist):
```bash
python -m venv .venv
pip install -r requirements.txt
python main.py
python main.py --offline
python main.py --scenario "Infrastructure Damage" --draws 25000 --seed 42
python -m unittest discover -s tests -v
```
- Tests: 1 Python test file(s) under `tests/`; framework appears to be unittest. Add/update tests with any logic change.

## Conventions observed
- Functions use type hints; keep annotating new code.
- Uses `dataclasses` for structured config/results.
- Config lives in: `pyproject.toml`, `src/config.py`; avoid hardcoding parameters elsewhere.
- Random seeds are set for reproducibility (Monte Carlo/simulation); keep seeded, deterministic runs.
- Public data sources referenced: yfinance.
- Write paths relative to the repo root (no absolute local paths).

## Output artifacts
- Generated outputs go to: `outputs/charts/`
- A PDF report is produced with `reportlab`; keep it in sync with model changes.
- Charts are generated with matplotlib.

## Guardrails
- Never commit secrets, API keys, tokens, or `.env` files.
- Do not commit large raw datasets or binaries; keep data fetched or documented with its source.
- Keep analysis source-backed: cite data sources and assumptions; label scenario/forecast outputs as model estimates, not facts.
- Preserve reproducibility: no unseeded randomness, no hidden manual steps.
