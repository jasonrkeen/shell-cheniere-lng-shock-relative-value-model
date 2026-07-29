# Methodology

## 1. Model purpose

The model estimates **conditional changes from a baseline** under specified
global LNG disruptions. It does not estimate absolute fair value and does not
claim access to proprietary contracts, cargo schedules, trading positions, or
hedges.

Its primary comparison is:

```text
Cheniere modeled equity response - Shell modeled equity response
```

A positive spread favors Cheniere within the scenario; a negative spread favors
Shell.

## 2. Physical supply gap

For global supply loss \(L\), non-Gulf replacement share \(R\), and demand
destruction share \(D\), the residual gap is:

\[
G = L(1-R)(1-D)
\]

This structure prevents the headline physical loss from being treated as the
final market deficit. Replacement production and consumption adjustments
reduce the imbalance first.

## 3. Regional price transmission

The JKM-equivalent percentage shock is nonlinear:

\[
\Delta JKM =
\alpha
\left(\frac{G}{G_b}\right)^\gamma
\times P(T)
\]

where:

- \(\alpha\) is the configured price-elasticity coefficient;
- \(G_b\) is the benchmark supply gap;
- \(\gamma\) is the price-elasticity exponent;
- \(P(T)\) is a bounded duration-persistence multiplier.

TTF and Henry Hub shocks are modeled as configured pass-through fractions of
the JKM-equivalent shock. Henry Hub also receives a small incremental term from
replacement demand for U.S. LNG.

The equation is a scenario transmission function rather than an econometric
claim about a permanent structural elasticity.

## 4. Shell transmission

Shell's Integrated Gas shock bridge includes:

1. spot-linked JKM and TTF price capture;
2. trading and optimization optionality;
3. Gulf-linked volume loss after portfolio flexibility;
4. freight and route costs;
5. working-capital requirements;
6. demand destruction.

The resulting Integrated Gas impact is multiplied by the configured share of
group cash flow attributable to the segment. The equity response then applies a
cash-flow-to-equity multiplier and geopolitical valuation discount.

Shell's current marker structure is informed by its financial modelling
guidance, which identifies JKM/TTF spot exposure, oil-linked term contracts,
Henry Hub purchases, and LNG trading and optimization. The numerical exposure
coefficients remain explicit model assumptions.

## 5. Cheniere transmission

Cheniere's bridge includes:

1. additional throughput demanded from non-Gulf suppliers;
2. a hard ceiling based on disclosed liquefaction capacity and utilization;
3. limited international spot-price capture because most volume is contracted;
4. Henry Hub feed-gas cost pressure;
5. freight and working-capital costs;
6. operating strain above 96% utilization.

The model does not assume Cheniere receives the entire international price
shock. Its advantage is primarily geographic substitution plus available
capacity, not unlimited spot exposure.

## 6. Monte Carlo simulation

The default run uses 10,000 simulations around the selected scenario. The
following inputs vary:

- global supply loss;
- disruption duration;
- replacement supply;
- demand destruction;
- route and freight costs;
- geopolitical risk premium;
- Shell price capture and portfolio flexibility;
- Cheniere price capture;
- correlated residual equity returns.

The random seed is disclosed and configurable. Simulation output therefore
remains reproducible.

The probability that Cheniere outperforms is:

\[
P(R_{LNG} - R_{SHEL} > 0)
\]

This is a model-conditioned probability, not an objective probability of
future investment performance.

## 7. Relative-value threshold

The model sweeps global supply loss from 0% to 40%. Route costs and geopolitical
risk are scaled with disruption severity so the zero-loss case starts from a
zero shock. Other assumptions are held at the selected scenario's values.

The first interpolation point at which the relative-return spread changes sign
is reported as the preference crossover.

## 8. Calibration hierarchy

1. **Reported facts:** trade-flow shares, company capacity, reported volumes,
   segment structure, and public price-marker guidance.
2. **Model assumptions:** company exposure, price capture, portfolio
   flexibility, cash-flow multipliers, and cost intensities.
3. **Optional market calibration:** weekly beta, volatility, and return
   correlation.
4. **Fallback calibration:** disclosed values used when live data are
   unavailable.

## 9. Interpretation

The model is most useful for:

- comparing mechanisms across companies;
- identifying variables that change the preferred exposure;
- testing nonlinear capacity and demand effects;
- supporting an energy-security or risk-intelligence research brief.

It should not be used as a stand-alone trading signal.
