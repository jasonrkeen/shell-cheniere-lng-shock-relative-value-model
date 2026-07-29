"""Run the Shell–Cheniere global LNG shock relative-value pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.config import load_model_config, load_scenarios
from src.market_data import calibrate_market_data
from src.model import (
    run_monte_carlo,
    run_scenarios,
    run_threshold_analysis,
)
from src.reporting import (
    build_decision_brief,
    build_pdf_report,
    create_charts,
)


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Model Shell versus Cheniere under global LNG disruption."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live market downloads and use disclosed fallback calibration.",
    )
    parser.add_argument(
        "--draws",
        type=int,
        default=None,
        help="Monte Carlo draws; defaults to the model configuration.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed; defaults to the model configuration.",
    )
    parser.add_argument(
        "--scenario",
        default="Severe LNG Shock",
        help="Scenario used for Monte Carlo and threshold analysis.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_model_config(ROOT / "config" / "model_config.json")
    scenarios = load_scenarios(ROOT / "config" / "scenarios.csv")
    if args.scenario not in set(scenarios["scenario"]):
        choices = ", ".join(scenarios["scenario"])
        raise SystemExit(f"Unknown scenario '{args.scenario}'. Choices: {choices}")

    draws = args.draws or int(config["model"]["default_draws"])
    seed = args.seed if args.seed is not None else int(config["model"]["default_seed"])
    if draws < 1000:
        raise SystemExit("--draws must be at least 1,000.")

    outputs = ROOT / "outputs"
    chart_dir = outputs / "charts"
    cache_dir = ROOT / "data" / "cache"
    outputs.mkdir(parents=True, exist_ok=True)
    chart_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print("Shell-Cheniere Global LNG Shock Relative-Value Model")
    print("=" * 76)
    print("[1/8] Loading scenarios and source register...")
    source_register = pd.read_csv(ROOT / "data" / "source_register.csv")

    print("[2/8] Calibrating market-risk parameters...")
    calibration = calibrate_market_data(config, cache_dir, args.offline)
    calibration.to_frame().to_csv(
        outputs / "market_calibration.csv", index=False
    )

    print("[3/8] Running deterministic scenario engine...")
    scenario_results = run_scenarios(scenarios, config)
    scenario_results.to_csv(outputs / "scenario_results.csv", index=False)

    selected = scenarios.loc[scenarios["scenario"] == args.scenario].iloc[0]
    print(f"[4/8] Running {draws:,}-draw Monte Carlo simulation...")
    mc_draws, mc_summary = run_monte_carlo(
        selected, config, calibration, draws, seed
    )
    mc_draws.to_csv(outputs / "monte_carlo_draws.csv", index=False)
    mc_summary.to_csv(outputs / "monte_carlo_summary.csv", index=False)

    print("[5/8] Estimating relative-value crossover...")
    threshold, threshold_value = run_threshold_analysis(config, selected)
    threshold.to_csv(outputs / "threshold_analysis.csv", index=False)

    print("[6/8] Creating decision charts...")
    charts = create_charts(scenario_results, mc_draws, threshold, chart_dir)

    print("[7/8] Writing executive decision brief...")
    build_decision_brief(
        scenario_results,
        mc_summary,
        threshold_value,
        calibration.data_status,
        outputs / "executive_decision_brief.md",
    )

    print("[8/8] Building PDF report...")
    build_pdf_report(
        scenario_results,
        mc_summary,
        threshold_value,
        calibration,
        charts,
        source_register,
        config,
        outputs / "shell_cheniere_lng_shock_report.pdf",
    )

    severe = scenario_results.loc[
        scenario_results["scenario"] == args.scenario
    ].iloc[0]
    spread = mc_summary.loc[
        mc_summary["metric"] == "Cheniere minus Shell"
    ].iloc[0]
    print()
    print("Pipeline complete")
    print(f"Market data status: {calibration.data_status}")
    print(
        f"{args.scenario} preferred exposure: {severe['preferred_exposure']}"
    )
    print(
        "Probability Cheniere outperforms: "
        f"{spread['probability_cheniere_outperforms']:.1%}"
    )
    if threshold_value is not None:
        print(f"First crossover threshold: {threshold_value:.1%} supply loss")
    else:
        print("First crossover threshold: none within 0–40% sweep")
    print(f"Report: {outputs / 'shell_cheniere_lng_shock_report.pdf'}")


if __name__ == "__main__":
    main()
