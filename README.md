# Shell-Cheniere Global LNG Shock Relative-Value Model

## Overview

This project tests how a global LNG supply disruption could affect two
different energy business models:

- **Shell (SHEL):** a diversified integrated-energy company with a global LNG
  portfolio, contract lags, marketing, trading, and cargo-optimization
  capabilities.
- **Cheniere Energy (LNG):** a U.S.-anchored LNG producer and exporter whose
  substitution opportunity is constrained by contracted volumes and physical
  liquefaction capacity.

The central research question is:

> When Gulf LNG supply is disrupted, does Shell's portfolio flexibility
> outperform Cheniere's geographic advantage, or does U.S. liquefaction become
> the stronger relative exposure?

The project is designed as a follow-up to the **XOM Compound Oil Shock Equity
Stress Model** and the **BP Dual-Chokepoint Equity Stress Model**. It advances
that work from single-company stress testing into cross-company relative-value
analysis.

## Key contribution

Higher LNG prices do not automatically identify the winning equity. The model
separately accounts for:

- the physical supply loss;
- non-Gulf replacement production;
- demand destruction and fuel switching;
- JKM, TTF, and Henry Hub transmission;
- cargo-routing, freight, and insurance costs;
- Shell's trading optionality and Gulf-linked exposure;
- Cheniere's spare-capacity ceiling, feed-gas costs, and contract structure;
- working-capital pressure and geopolitical valuation discounts.

The main decision output is the **probability that Cheniere outperforms Shell**,
along with the disruption threshold at which the preferred exposure changes.

## Pipeline

```text
Scenario definitions
    -> physical LNG supply gap
    -> regional gas-price shocks
    -> company cash-flow bridges
    -> equity response
    -> 10,000-run Monte Carlo
    -> relative-value threshold
    -> charts, CSV outputs, decision brief, and PDF report
```

## Quick start

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

macOS or Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Run without attempting a market-data download:

```bash
python main.py --offline
```

Select a different Monte Carlo scenario or simulation size:

```bash
python main.py --scenario "Infrastructure Damage" --draws 25000 --seed 42
```

## Output files

The pipeline writes:

- `outputs/scenario_results.csv`
- `outputs/market_calibration.csv`
- `outputs/monte_carlo_draws.csv`
- `outputs/monte_carlo_summary.csv`
- `outputs/threshold_analysis.csv`
- `outputs/executive_decision_brief.md`
- `outputs/shell_cheniere_lng_shock_report.pdf`
- `outputs/charts/scenario_equity_returns.png`
- `outputs/charts/monte_carlo_return_distribution.png`
- `outputs/charts/relative_value_threshold.png`

## Scenario set

| Scenario | Global supply loss | Duration | Core interpretation |
|---|---:|---:|---|
| Normalization | 2% | 30 days | Rapid substitution and limited dislocation |
| Managed Disruption | 10% | 60 days | Material but contained interruption |
| Severe LNG Shock | 20% | 120 days | Major Gulf-equivalent loss with partial substitution |
| Infrastructure Damage | 30% | 365 days | Prolonged liquefaction/export impairment |
| Demand Destruction | 20% | 270 days | High prices trigger industrial curtailment and switching |

All scenario parameters are editable in `config/scenarios.csv`.

## Live-data behavior

When `yfinance` and external market access are available, the project
calibrates weekly SHEL and LNG volatility, correlation, and market beta using
SPY. If retrieval fails, or `--offline` is used, the pipeline completes with
the disclosed fallback values in `config/model_config.json`. The resulting
status is written to `outputs/market_calibration.csv` and the PDF report.

Market data calibrates residual equity uncertainty only. Physical LNG and
company-transmission assumptions remain transparent and reproducible.

## Validation

Run the standard-library test suite:

```bash
python -m unittest discover -s tests -v
```

Tests cover configuration validity, monotonic commodity transmission, scenario
execution, Monte Carlo reproducibility, output bounds, and threshold behavior.

## Research governance

- Reported company and market facts are listed in
  `data/source_register.csv`.
- Non-public exposures are identified as assumptions in
  `config/model_config.json`.
- `METHODOLOGY.md` documents the equations and interpretation.
- `MODEL_CARD.md` records intended use, limitations, and prohibited
  interpretations.
- Results are conditional scenario estimates, not share-price forecasts or
  investment recommendations.

## License

MIT License. See `LICENSE`.

