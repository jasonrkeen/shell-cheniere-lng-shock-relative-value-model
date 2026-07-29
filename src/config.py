"""Configuration loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_SCENARIO_COLUMNS = {
    "scenario",
    "global_supply_loss_pct",
    "duration_days",
    "non_gulf_replacement_pct",
    "demand_destruction_pct_of_gap",
    "route_cost_shock_pct",
    "geopolitical_risk_premium_pct",
    "description",
}


def load_model_config(path: Path) -> dict[str, Any]:
    """Load and minimally validate model configuration."""
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if "model" not in config or "companies" not in config:
        raise ValueError("Configuration must contain 'model' and 'companies'.")
    if set(config["companies"]) != {"Shell", "Cheniere"}:
        raise ValueError("Configuration must contain Shell and Cheniere.")
    return config


def load_scenarios(path: Path) -> pd.DataFrame:
    """Load scenario definitions and enforce valid probability ranges."""
    scenarios = pd.read_csv(path)
    missing = REQUIRED_SCENARIO_COLUMNS.difference(scenarios.columns)
    if missing:
        raise ValueError(f"Scenario file is missing columns: {sorted(missing)}")

    probability_columns = [
        "global_supply_loss_pct",
        "non_gulf_replacement_pct",
        "demand_destruction_pct_of_gap",
        "route_cost_shock_pct",
        "geopolitical_risk_premium_pct",
    ]
    for column in probability_columns:
        if not scenarios[column].between(0, 1).all():
            raise ValueError(f"{column} must be between zero and one.")
    if (scenarios["duration_days"] <= 0).any():
        raise ValueError("Scenario duration must be positive.")
    if scenarios["scenario"].duplicated().any():
        raise ValueError("Scenario names must be unique.")
    return scenarios

