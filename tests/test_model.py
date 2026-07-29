"""Unit tests for the LNG shock model."""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from src.config import load_model_config, load_scenarios
from src.market_data import MarketCalibration
from src.model import (
    commodity_transmission,
    run_monte_carlo,
    run_scenarios,
    run_threshold_analysis,
)


ROOT = Path(__file__).resolve().parents[1]


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_model_config(ROOT / "config" / "model_config.json")
        cls.scenarios = load_scenarios(ROOT / "config" / "scenarios.csv")
        cls.calibration = MarketCalibration(
            data_status="test",
            observation_count=100,
            start_date="2024-01-01",
            end_date="2026-01-01",
            shell_market_beta=0.8,
            cheniere_market_beta=1.0,
            shell_annualized_volatility=0.28,
            cheniere_annualized_volatility=0.36,
            return_correlation=0.45,
            note="Test calibration",
        )

    def test_scenario_table_runs(self) -> None:
        results = run_scenarios(self.scenarios, self.config)
        self.assertEqual(len(results), len(self.scenarios))
        self.assertTrue(
            np.isfinite(results["cheniere_minus_shell_return_pct"]).all()
        )

    def test_price_shock_increases_with_unreplaced_loss(self) -> None:
        transmission = commodity_transmission(
            loss=np.array([0.05, 0.10, 0.20]),
            duration_days=120,
            replacement=0.40,
            demand_destruction=0.20,
            model_config=self.config["model"],
        )
        self.assertTrue(np.all(np.diff(transmission.jkm_price_shock_pct) > 0))

    def test_replacement_reduces_net_gap(self) -> None:
        transmission = commodity_transmission(
            loss=0.20,
            duration_days=120,
            replacement=np.array([0.20, 0.50, 0.80]),
            demand_destruction=0.20,
            model_config=self.config["model"],
        )
        self.assertTrue(np.all(np.diff(transmission.net_supply_gap_pct) < 0))

    def test_monte_carlo_is_reproducible(self) -> None:
        scenario = self.scenarios.loc[
            self.scenarios["scenario"] == "Severe LNG Shock"
        ].iloc[0]
        first, first_summary = run_monte_carlo(
            scenario, self.config, self.calibration, 1500, 123
        )
        second, second_summary = run_monte_carlo(
            scenario, self.config, self.calibration, 1500, 123
        )
        np.testing.assert_allclose(
            first["cheniere_minus_shell_return_pct"],
            second["cheniere_minus_shell_return_pct"],
        )
        np.testing.assert_allclose(
            first_summary["mean"],
            second_summary["mean"],
        )

    def test_probability_bounds(self) -> None:
        scenario = self.scenarios.iloc[2]
        _, summary = run_monte_carlo(
            scenario, self.config, self.calibration, 1500, 456
        )
        probability = summary["probability_cheniere_outperforms"].iloc[0]
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)

    def test_threshold_starts_at_zero_shock(self) -> None:
        scenario = self.scenarios.loc[
            self.scenarios["scenario"] == "Severe LNG Shock"
        ].iloc[0]
        threshold, _ = run_threshold_analysis(self.config, scenario)
        self.assertAlmostEqual(
            float(threshold["shell_equity_return_pct"].iloc[0]),
            0.0,
            places=10,
        )
        self.assertAlmostEqual(
            float(threshold["cheniere_equity_return_pct"].iloc[0]),
            0.0,
            places=10,
        )


if __name__ == "__main__":
    unittest.main()

