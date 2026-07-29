# Model Card

## Model

**Name:** Shell-Cheniere Global LNG Shock Relative-Value Model  
**Version:** 0.1.0  
**Owner:** Jason Keen  
**Type:** Scenario analysis and Monte Carlo decision-support model

## Intended use

- Energy-security and geopolitical-risk research
- LNG supply-disruption scenario analysis
- Company business-model comparison
- Portfolio and LinkedIn research demonstration
- Identification of key sensitivities and relative-value thresholds

## Out-of-scope use

- Automated trading
- Personalized investment recommendations
- Precise share-price targets
- Claims about undisclosed company contracts, hedges, or trading positions
- Operational decisions by energy infrastructure owners

## Inputs

- Five transparent disruption scenarios
- Global LNG trade and Hormuz exposure benchmarks
- Shell LNG volume and segment context
- Cheniere operating liquefaction capacity
- Configured company exposure coefficients
- Optional weekly market-price calibration

## Outputs

- Physical net supply gap
- JKM-, TTF-, and Henry Hub-equivalent shocks
- Company cash-flow changes
- Model-implied equity responses
- Cheniere-minus-Shell spread
- Probability of Cheniere outperformance
- Relative-value crossover threshold

## Key assumptions

- Regional LNG prices respond nonlinearly to the residual supply gap.
- Replacement supply and demand destruction occur within the scenario horizon.
- Shell's diversification and trading flexibility reduce physical volume loss
  and create volatility upside.
- Cheniere's incremental volume is capped by available liquefaction capacity.
- Contracted volume reduces Cheniere's direct exposure to international spot
  prices.
- Working-capital, freight, and risk-premium effects rise with disruption.

## Known limitations

- Cargo-level and contract-level company exposures are not public.
- The model uses reduced-form transmission rather than a global gas-market
  equilibrium.
- Tax, FX, detailed derivatives, financing changes, and all non-LNG business
  interactions are excluded.
- Company coefficients are research assumptions and require sensitivity
  testing.
- Historical equity calibration may not represent future crisis behavior.
- Simulation probabilities inherit the scenario and distribution assumptions.

## Data quality controls

- Scenario range and column validation
- Explicit live/fallback market-data status
- Fixed random seed by default
- Source register separating public evidence from assumptions
- Unit tests for monotonicity, bounds, reproducibility, and zero-shock behavior

## Ethical and financial-use statement

This is an educational research model. It is not investment advice, and its
outputs should not be presented as certain forecasts.

