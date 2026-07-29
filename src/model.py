"""Scenario, Monte Carlo, and threshold engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .market_data import MarketCalibration


@dataclass(frozen=True)
class Transmission:
    net_supply_gap_pct: np.ndarray
    jkm_price_shock_pct: np.ndarray
    ttf_price_shock_pct: np.ndarray
    hh_price_shock_pct: np.ndarray
    duration_weight: np.ndarray


def _arr(value: Any) -> np.ndarray:
    return np.asarray(value, dtype=float)


def commodity_transmission(
    loss: Any,
    duration_days: Any,
    replacement: Any,
    demand_destruction: Any,
    model_config: dict[str, Any],
) -> Transmission:
    """Translate physical supply loss into regional gas-price shocks."""
    loss = np.clip(_arr(loss), 0.0, 0.60)
    duration = np.clip(_arr(duration_days), 1.0, 730.0)
    replacement = np.clip(_arr(replacement), 0.0, 1.0)
    demand_destruction = np.clip(_arr(demand_destruction), 0.0, 1.0)

    net_gap = loss * (1.0 - replacement) * (1.0 - demand_destruction)
    duration_weight = np.clip(duration / 365.0, 0.0, 1.50)
    persistence = np.clip(np.sqrt(duration / 120.0), 0.35, 1.60)
    coefficient = float(model_config["price_elasticity_coefficient"])
    exponent = float(model_config["price_elasticity_exponent"])
    benchmark_gap = float(model_config["benchmark_gap_pct"])

    scaled_gap = np.maximum(net_gap / benchmark_gap, 0.0)
    jkm = coefficient * np.power(scaled_gap, exponent) * persistence
    jkm = np.clip(jkm, 0.0, 3.0)
    ttf = np.clip(
        jkm * float(model_config["ttf_to_jkm_pass_through"]),
        0.0,
        2.5,
    )
    hh = np.clip(
        jkm * float(model_config["hh_to_jkm_pass_through"])
        + 0.05 * loss * replacement,
        0.0,
        0.90,
    )
    return Transmission(net_gap, jkm, ttf, hh, duration_weight)


def _company_impacts(
    loss: Any,
    duration_days: Any,
    replacement: Any,
    demand_destruction: Any,
    route_cost: Any,
    risk_premium: Any,
    config: dict[str, Any],
    shell_price_capture_multiplier: Any = 1.0,
    shell_flexibility_multiplier: Any = 1.0,
    cheniere_price_capture_multiplier: Any = 1.0,
) -> dict[str, np.ndarray]:
    """Calculate company-level cash-flow and equity transmission components."""
    model_cfg = config["model"]
    shell = config["companies"]["Shell"]
    cheniere = config["companies"]["Cheniere"]
    t = commodity_transmission(
        loss, duration_days, replacement, demand_destruction, model_cfg
    )

    loss = np.clip(_arr(loss), 0.0, 0.60)
    replacement = np.clip(_arr(replacement), 0.0, 1.0)
    demand_destruction = np.clip(_arr(demand_destruction), 0.0, 1.0)
    route_cost = np.clip(_arr(route_cost), 0.0, 1.50)
    risk_premium = np.clip(_arr(risk_premium), 0.0, 0.50)

    shell_flex = np.clip(
        float(shell["portfolio_flexibility"])
        * _arr(shell_flexibility_multiplier),
        0.0,
        0.95,
    )
    shell_price_capture = np.clip(
        float(shell["price_capture"]) * _arr(shell_price_capture_multiplier),
        0.05,
        1.0,
    )

    shell_volume_loss = (
        loss
        * float(shell["gulf_volume_dependency"])
        * (1.0 - shell_flex)
    )
    shell_price_effect = (
        (
            t.jkm_price_shock_pct * float(shell["spot_price_exposure"])
            + t.ttf_price_shock_pct * 0.10
        )
        * shell_price_capture
        * t.duration_weight
    )
    shell_trading_effect = (
        np.minimum(t.jkm_price_shock_pct, 1.50)
        * float(shell["trading_optionality"])
        * t.duration_weight
    )
    shell_volume_effect = -2.0 * shell_volume_loss * t.duration_weight
    shell_freight_effect = (
        -route_cost * float(shell["freight_cost_exposure"]) * t.duration_weight
    )
    shell_working_capital_effect = (
        -t.jkm_price_shock_pct
        * float(shell["working_capital_intensity"])
        * np.sqrt(np.minimum(t.duration_weight, 1.0))
    )
    shell_demand_effect = (
        -loss
        * demand_destruction
        * float(shell["demand_destruction_exposure"])
        * t.duration_weight
    )
    shell_segment_delta = (
        shell_price_effect
        + shell_trading_effect
        + shell_volume_effect
        + shell_freight_effect
        + shell_working_capital_effect
        + shell_demand_effect
    )
    shell_company_cashflow_delta = (
        shell_segment_delta * float(shell["integrated_gas_group_weight"])
    )
    shell_equity_return = (
        shell_company_cashflow_delta
        * float(shell["cashflow_to_equity_multiplier"])
        - risk_premium * float(shell["geopolitical_discount_beta"])
    )

    base_util = float(cheniere["baseline_utilization"])
    capacity = float(cheniere["annual_lng_capacity_mtpa"])
    global_trade = float(model_cfg["global_lng_trade_mtpa"])
    replacement_demand_mtpa = loss * replacement * global_trade
    spare_capacity_mtpa = capacity * (1.0 - base_util)
    incremental_mtpa = np.minimum(replacement_demand_mtpa, spare_capacity_mtpa)
    volume_gain_pct = incremental_mtpa / (capacity * base_util)
    resulting_util = np.clip(
        base_util + incremental_mtpa / capacity,
        base_util,
        1.0,
    )

    cheniere_price_capture = np.clip(
        float(cheniere["international_price_capture"])
        * _arr(cheniere_price_capture_multiplier),
        0.02,
        0.70,
    )
    cheniere_price_effect = (
        t.jkm_price_shock_pct
        * (1.0 - float(cheniere["contracted_volume_share"]))
        * cheniere_price_capture
        * t.duration_weight
    )
    cheniere_volume_effect = 1.70 * volume_gain_pct * t.duration_weight
    cheniere_feedgas_effect = (
        -t.hh_price_shock_pct
        * float(cheniere["feedgas_cost_exposure"])
        * t.duration_weight
    )
    cheniere_freight_effect = (
        -route_cost
        * float(cheniere["freight_cost_exposure"])
        * t.duration_weight
    )
    cheniere_working_capital_effect = (
        -t.jkm_price_shock_pct
        * float(cheniere["working_capital_intensity"])
        * np.sqrt(np.minimum(t.duration_weight, 1.0))
    )
    strain = np.maximum(resulting_util - 0.96, 0.0)
    cheniere_strain_effect = (
        -strain
        * float(cheniere["operational_strain_coefficient"])
        * t.duration_weight
    )
    cheniere_cashflow_delta = (
        cheniere_price_effect
        + cheniere_volume_effect
        + cheniere_feedgas_effect
        + cheniere_freight_effect
        + cheniere_working_capital_effect
        + cheniere_strain_effect
    )
    cheniere_equity_return = (
        cheniere_cashflow_delta
        * float(cheniere["cashflow_to_equity_multiplier"])
        - risk_premium * float(cheniere["geopolitical_discount_beta"])
    )

    return {
        "net_supply_gap_pct": t.net_supply_gap_pct,
        "jkm_price_shock_pct": t.jkm_price_shock_pct,
        "ttf_price_shock_pct": t.ttf_price_shock_pct,
        "hh_price_shock_pct": t.hh_price_shock_pct,
        "shell_price_effect": shell_price_effect,
        "shell_trading_effect": shell_trading_effect,
        "shell_volume_effect": shell_volume_effect,
        "shell_freight_effect": shell_freight_effect,
        "shell_working_capital_effect": shell_working_capital_effect,
        "shell_demand_effect": shell_demand_effect,
        "shell_cashflow_delta_pct": shell_company_cashflow_delta,
        "shell_equity_return_pct": shell_equity_return,
        "cheniere_price_effect": cheniere_price_effect,
        "cheniere_volume_effect": cheniere_volume_effect,
        "cheniere_feedgas_effect": cheniere_feedgas_effect,
        "cheniere_freight_effect": cheniere_freight_effect,
        "cheniere_working_capital_effect": cheniere_working_capital_effect,
        "cheniere_strain_effect": cheniere_strain_effect,
        "cheniere_cashflow_delta_pct": cheniere_cashflow_delta,
        "cheniere_equity_return_pct": cheniere_equity_return,
        "cheniere_utilization_pct": resulting_util,
    }


def run_scenarios(
    scenarios: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Run deterministic scenarios and return a presentation-ready table."""
    rows: list[dict[str, Any]] = []
    for scenario in scenarios.to_dict(orient="records"):
        impacts = _company_impacts(
            scenario["global_supply_loss_pct"],
            scenario["duration_days"],
            scenario["non_gulf_replacement_pct"],
            scenario["demand_destruction_pct_of_gap"],
            scenario["route_cost_shock_pct"],
            scenario["geopolitical_risk_premium_pct"],
            config,
        )
        scalar = {key: float(np.asarray(value)) for key, value in impacts.items()}
        rows.append(
            {
                **scenario,
                **scalar,
                "cheniere_minus_shell_return_pct": (
                    scalar["cheniere_equity_return_pct"]
                    - scalar["shell_equity_return_pct"]
                ),
                "preferred_exposure": (
                    "Cheniere"
                    if scalar["cheniere_equity_return_pct"]
                    > scalar["shell_equity_return_pct"]
                    else "Shell"
                ),
            }
        )
    return pd.DataFrame(rows)


def _truncated_normal(
    rng: np.random.Generator,
    mean: float,
    relative_sd: float,
    low: float,
    high: float,
    size: int,
) -> np.ndarray:
    sd = max(abs(mean) * relative_sd, 0.005)
    return np.clip(rng.normal(mean, sd, size), low, high)


def run_monte_carlo(
    scenario: pd.Series,
    config: dict[str, Any],
    calibration: MarketCalibration,
    draws: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run vectorized Monte Carlo simulation for one selected scenario."""
    rng = np.random.default_rng(seed)
    loss = _truncated_normal(
        rng, float(scenario["global_supply_loss_pct"]), 0.22, 0.0, 0.60, draws
    )
    duration = _truncated_normal(
        rng, float(scenario["duration_days"]), 0.25, 7.0, 730.0, draws
    )
    replacement = _truncated_normal(
        rng,
        float(scenario["non_gulf_replacement_pct"]),
        0.18,
        0.0,
        1.0,
        draws,
    )
    demand = _truncated_normal(
        rng,
        float(scenario["demand_destruction_pct_of_gap"]),
        0.25,
        0.0,
        0.95,
        draws,
    )
    route = _truncated_normal(
        rng, float(scenario["route_cost_shock_pct"]), 0.25, 0.0, 1.50, draws
    )
    risk = _truncated_normal(
        rng,
        float(scenario["geopolitical_risk_premium_pct"]),
        0.25,
        0.0,
        0.50,
        draws,
    )
    shell_capture = np.clip(rng.normal(1.0, 0.15, draws), 0.55, 1.45)
    shell_flex = np.clip(rng.normal(1.0, 0.12, draws), 0.60, 1.35)
    cheniere_capture = np.clip(rng.normal(1.0, 0.18, draws), 0.50, 1.50)

    impacts = _company_impacts(
        loss,
        duration,
        replacement,
        demand,
        route,
        risk,
        config,
        shell_capture,
        shell_flex,
        cheniere_capture,
    )

    correlation = float(np.clip(calibration.return_correlation, -0.95, 0.95))
    z1 = rng.standard_normal(draws)
    z2 = correlation * z1 + np.sqrt(1.0 - correlation**2) * rng.standard_normal(
        draws
    )
    horizon_years = np.minimum(duration, 365.0) / 365.0
    noise_scale = 0.35
    shell_noise = (
        z1
        * calibration.shell_annualized_volatility
        * np.sqrt(horizon_years)
        * noise_scale
    )
    cheniere_noise = (
        z2
        * calibration.cheniere_annualized_volatility
        * np.sqrt(horizon_years)
        * noise_scale
    )
    shell_return = impacts["shell_equity_return_pct"] + shell_noise
    cheniere_return = impacts["cheniere_equity_return_pct"] + cheniere_noise
    spread = cheniere_return - shell_return

    draws_frame = pd.DataFrame(
        {
            "scenario": scenario["scenario"],
            "draw": np.arange(1, draws + 1),
            "global_supply_loss_pct": loss,
            "duration_days": duration,
            "non_gulf_replacement_pct": replacement,
            "demand_destruction_pct_of_gap": demand,
            "route_cost_shock_pct": route,
            "geopolitical_risk_premium_pct": risk,
            "net_supply_gap_pct": impacts["net_supply_gap_pct"],
            "jkm_price_shock_pct": impacts["jkm_price_shock_pct"],
            "shell_cashflow_delta_pct": impacts["shell_cashflow_delta_pct"],
            "cheniere_cashflow_delta_pct": impacts[
                "cheniere_cashflow_delta_pct"
            ],
            "shell_equity_return_pct": shell_return,
            "cheniere_equity_return_pct": cheniere_return,
            "cheniere_minus_shell_return_pct": spread,
            "cheniere_outperforms": spread > 0,
        }
    )

    def stats(company: str, values: np.ndarray) -> dict[str, Any]:
        return {
            "scenario": scenario["scenario"],
            "metric": company,
            "mean": float(np.mean(values)),
            "p10": float(np.quantile(values, 0.10)),
            "p50": float(np.quantile(values, 0.50)),
            "p90": float(np.quantile(values, 0.90)),
            "probability_negative": float(np.mean(values < 0)),
        }

    summary_rows = [
        stats("Shell equity return", shell_return),
        stats("Cheniere equity return", cheniere_return),
        stats("Cheniere minus Shell", spread),
    ]
    for row in summary_rows:
        row["probability_cheniere_outperforms"] = float(np.mean(spread > 0))
        row["draws"] = draws
        row["seed"] = seed
    return draws_frame, pd.DataFrame(summary_rows)


def run_threshold_analysis(
    config: dict[str, Any],
    reference_scenario: pd.Series,
) -> tuple[pd.DataFrame, float | None]:
    """Sweep loss severity and estimate where relative preference changes."""
    loss_grid = np.linspace(0.0, 0.40, 81)
    reference_loss = max(
        float(reference_scenario["global_supply_loss_pct"]),
        0.01,
    )
    severity_scale = np.clip(loss_grid / reference_loss, 0.0, 2.0)
    impacts = _company_impacts(
        loss_grid,
        float(reference_scenario["duration_days"]),
        float(reference_scenario["non_gulf_replacement_pct"]),
        float(reference_scenario["demand_destruction_pct_of_gap"]),
        float(reference_scenario["route_cost_shock_pct"]) * severity_scale,
        float(reference_scenario["geopolitical_risk_premium_pct"])
        * severity_scale,
        config,
    )
    spread = (
        impacts["cheniere_equity_return_pct"]
        - impacts["shell_equity_return_pct"]
    )
    threshold = None
    changes = np.where(spread[:-1] * spread[1:] < 0)[0]
    if len(changes):
        i = int(changes[0])
        x0, x1 = loss_grid[i], loss_grid[i + 1]
        y0, y1 = spread[i], spread[i + 1]
        if y1 != y0:
            threshold = float(x0 - y0 * (x1 - x0) / (y1 - y0))

    frame = pd.DataFrame(
        {
            "global_supply_loss_pct": loss_grid,
            "shell_equity_return_pct": impacts["shell_equity_return_pct"],
            "cheniere_equity_return_pct": impacts[
                "cheniere_equity_return_pct"
            ],
            "cheniere_minus_shell_return_pct": spread,
        }
    )
    return frame, threshold
