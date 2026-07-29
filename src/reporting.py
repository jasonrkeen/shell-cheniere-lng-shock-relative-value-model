"""Charts, decision brief, and PDF report generation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/shell_cheniere_matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


SHELL_COLOR = "#D71920"
CHENIERE_COLOR = "#1464A5"
NAVY = "#132A3A"
GOLD = "#E6A700"


def _pct(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def create_charts(
    scenario_results: pd.DataFrame,
    monte_carlo_draws: pd.DataFrame,
    threshold: pd.DataFrame,
    chart_dir: Path,
) -> list[Path]:
    chart_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    created: list[Path] = []

    x = np.arange(len(scenario_results))
    width = 0.36
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.bar(
        x - width / 2,
        scenario_results["shell_equity_return_pct"] * 100,
        width,
        label="Shell",
        color=SHELL_COLOR,
    )
    ax.bar(
        x + width / 2,
        scenario_results["cheniere_equity_return_pct"] * 100,
        width,
        label="Cheniere",
        color=CHENIERE_COLOR,
    )
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(x, scenario_results["scenario"], rotation=18, ha="right")
    ax.set_ylabel("Model-implied equity return")
    ax.set_title("Scenario-Conditioned Relative Equity Response")
    ax.legend(frameon=False)
    fig.tight_layout()
    path = chart_dir / "scenario_equity_returns.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    created.append(path)

    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    ax.hist(
        monte_carlo_draws["shell_equity_return_pct"] * 100,
        bins=55,
        alpha=0.62,
        label="Shell",
        color=SHELL_COLOR,
        density=True,
    )
    ax.hist(
        monte_carlo_draws["cheniere_equity_return_pct"] * 100,
        bins=55,
        alpha=0.62,
        label="Cheniere",
        color=CHENIERE_COLOR,
        density=True,
    )
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Simulated equity return (%)")
    ax.set_ylabel("Density")
    ax.set_title(
        f"Monte Carlo Return Distribution - "
        f"{monte_carlo_draws['scenario'].iloc[0]}"
    )
    ax.legend(frameon=False)
    fig.tight_layout()
    path = chart_dir / "monte_carlo_return_distribution.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    created.append(path)

    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    ax.plot(
        threshold["global_supply_loss_pct"] * 100,
        threshold["shell_equity_return_pct"] * 100,
        label="Shell",
        color=SHELL_COLOR,
        linewidth=2.4,
    )
    ax.plot(
        threshold["global_supply_loss_pct"] * 100,
        threshold["cheniere_equity_return_pct"] * 100,
        label="Cheniere",
        color=CHENIERE_COLOR,
        linewidth=2.4,
    )
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Global LNG supply loss (%)")
    ax.set_ylabel("Model-implied equity return (%)")
    ax.set_title("Relative-Value Threshold Sweep")
    ax.legend(frameon=False)
    fig.tight_layout()
    path = chart_dir / "relative_value_threshold.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    created.append(path)
    return created


def build_decision_brief(
    scenario_results: pd.DataFrame,
    mc_summary: pd.DataFrame,
    threshold_value: float | None,
    calibration_status: str,
    output_path: Path,
) -> None:
    severe = scenario_results.loc[
        scenario_results["scenario"] == "Severe LNG Shock"
    ].iloc[0]
    spread = mc_summary.loc[
        mc_summary["metric"] == "Cheniere minus Shell"
    ].iloc[0]
    threshold_text = (
        f"{threshold_value * 100:.1f}%"
        if threshold_value is not None
        else "not identified within the 0-40% sweep"
    )
    content = f"""# Executive Decision Brief

## Decision question

Under a global LNG supply disruption, does Shell's portfolio flexibility and
trading optionality produce better equity resilience than Cheniere's
U.S.-anchored liquefaction platform?

## Severe LNG Shock result

- Net modeled supply gap: **{_pct(severe['net_supply_gap_pct'])}**
- JKM-equivalent price shock: **{_pct(severe['jkm_price_shock_pct'])}**
- Shell modeled equity response: **{_pct(severe['shell_equity_return_pct'])}**
- Cheniere modeled equity response: **{_pct(severe['cheniere_equity_return_pct'])}**
- Deterministic preferred exposure: **{severe['preferred_exposure']}**

## Monte Carlo result

- Expected Cheniere-minus-Shell spread: **{_pct(spread['mean'])}**
- 10th-90th percentile spread: **{_pct(spread['p10'])} to {_pct(spread['p90'])}**
- Probability Cheniere outperforms: **{_pct(spread['probability_cheniere_outperforms'])}**
- Relative-value crossover: **{threshold_text} global supply loss**, holding
  the Severe LNG Shock scenario's other assumptions constant.

## Interpretation

Cheniere's non-Gulf location creates substitution value, but its volume upside
is capped by available liquefaction capacity and contracted-volume economics.
Shell receives diversified price and trading benefits, while also bearing
Gulf-linked volume, freight, working-capital, and demand-destruction effects.
The preferred exposure therefore depends on shock severity, duration, the
replacement response, and the amount of international price upside each
company can retain.

## Governance

Market calibration status: **{calibration_status}**. Results are conditional
scenario estimates, not forecasts or investment advice. Company exposures that
are not publicly disclosed are transparent assumptions in
`config/model_config.json` and should be sensitivity-tested before use.
"""
    output_path.write_text(content, encoding="utf-8")


def _table(data: list[list[Any]], widths: list[float]) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C1C8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F4F6")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def build_pdf_report(
    scenario_results: pd.DataFrame,
    mc_summary: pd.DataFrame,
    threshold_value: float | None,
    calibration: Any,
    chart_paths: list[Path],
    source_register: pd.DataFrame,
    config: dict[str, Any],
    output_path: Path,
) -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor(NAVY),
            fontSize=20,
            leading=24,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            textColor=colors.HexColor(NAVY),
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=8,
            leading=11,
        )
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Shell-Cheniere Global LNG Shock Relative-Value Model",
        author="Jason Keen",
    )
    story: list[Any] = []
    story.append(
        Paragraph(
            "Shell-Cheniere Global LNG Shock<br/>Relative-Value Model",
            styles["TitleCenter"],
        )
    )
    story.append(
        Paragraph(
            "Physical disruption -> regional gas prices -> company cash flow -> equity response",
            ParagraphStyle(
                "Subtitle",
                parent=styles["BodyText"],
                alignment=TA_CENTER,
                textColor=colors.HexColor("#4A5963"),
                fontSize=10,
                spaceAfter=12,
            ),
        )
    )

    severe = scenario_results.loc[
        scenario_results["scenario"] == "Severe LNG Shock"
    ].iloc[0]
    spread = mc_summary.loc[
        mc_summary["metric"] == "Cheniere minus Shell"
    ].iloc[0]
    finding = (
        f"In the Severe LNG Shock calibration, the deterministic model "
        f"modestly favors <b>{severe['preferred_exposure']}</b>. "
        f"The Monte Carlo simulation assigns a "
        f"<b>{_pct(spread['probability_cheniere_outperforms'])}</b> "
        f"probability that Cheniere outperforms Shell, indicating a narrow "
        f"and assumption-sensitive relative edge."
    )
    story.append(
        Table(
            [[Paragraph(finding, styles["BodyText"])]],
            colWidths=[7.3 * inch],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4D1")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(GOLD)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        )
    )
    story.append(Spacer(1, 8))
    story.append(Paragraph("Decision question", styles["Section"]))
    story.append(
        Paragraph(
            "When Gulf LNG supplies are disrupted, which business model "
            "delivers stronger equity resilience: Shell's diversified LNG "
            "portfolio and trading optionality, or Cheniere's U.S.-anchored "
            "liquefaction platform?",
            styles["BodyText"],
        )
    )
    story.append(Paragraph("Scenario results", styles["Section"]))
    scenario_table = [
        ["Scenario", "Net gap", "JKM shock", "Shell", "Cheniere", "Preferred"]
    ]
    for _, row in scenario_results.iterrows():
        scenario_table.append(
            [
                row["scenario"],
                _pct(row["net_supply_gap_pct"]),
                _pct(row["jkm_price_shock_pct"]),
                _pct(row["shell_equity_return_pct"]),
                _pct(row["cheniere_equity_return_pct"]),
                row["preferred_exposure"],
            ]
        )
    story.append(
        _table(
            scenario_table,
            [1.55 * inch, 0.72 * inch, 0.85 * inch, 0.8 * inch, 0.85 * inch, 0.9 * inch],
        )
    )
    story.append(Spacer(1, 8))
    story.append(Image(str(chart_paths[0]), width=7.15 * inch, height=4.0 * inch))

    story.append(PageBreak())
    story.append(Paragraph("Monte Carlo risk distribution", styles["Section"]))
    story.append(
        Paragraph(
            f"The model ran {int(spread['draws']):,} simulations around the "
            f"Severe LNG Shock scenario. Physical severity, duration, "
            f"replacement supply, demand destruction, freight costs, price "
            f"capture, and residual equity returns vary jointly.",
            styles["BodyText"],
        )
    )
    mc_table = [["Metric", "Mean", "P10", "Median", "P90", "P(negative)"]]
    for _, row in mc_summary.iterrows():
        mc_table.append(
            [
                row["metric"],
                _pct(row["mean"]),
                _pct(row["p10"]),
                _pct(row["p50"]),
                _pct(row["p90"]),
                _pct(row["probability_negative"]),
            ]
        )
    story.append(
        _table(
            mc_table,
            [1.65 * inch, 0.76 * inch, 0.76 * inch, 0.76 * inch, 0.76 * inch, 0.9 * inch],
        )
    )
    story.append(Spacer(1, 8))
    story.append(Image(str(chart_paths[1]), width=7.15 * inch, height=4.05 * inch))

    story.append(PageBreak())
    story.append(Paragraph("Relative-value threshold", styles["Section"]))
    threshold_text = (
        f"The first modelled preference crossover occurs near "
        f"<b>{threshold_value * 100:.1f}% global LNG supply loss</b>, with "
        f"the remaining Severe LNG Shock assumptions held constant."
        if threshold_value is not None
        else "No preference crossover appears inside the 0-40% global LNG "
        "supply-loss sweep under the reference assumptions."
    )
    story.append(Paragraph(threshold_text, styles["BodyText"]))
    story.append(Spacer(1, 8))
    story.append(Image(str(chart_paths[2]), width=7.15 * inch, height=4.05 * inch))
    story.append(Paragraph("Transmission logic", styles["Section"]))
    transmission = [
        ["Layer", "Shell", "Cheniere"],
        ["Physical", "Gulf-linked volumes; global portfolio", "U.S. Gulf Coast capacity ceiling"],
        ["Price", "JKM/TTF exposure plus contract lags", "International upside constrained by contracts"],
        ["Costs", "Freight, replacement cargoes, working capital", "Henry Hub feed gas, utilization strain"],
        ["Financial", "Integrated Gas weighted within diversified group", "Higher direct LNG cash-flow sensitivity"],
    ]
    story.append(
        _table(transmission, [0.9 * inch, 3.0 * inch, 3.0 * inch])
    )

    story.append(PageBreak())
    story.append(Paragraph("Methodology and governance", styles["Section"]))
    story.append(
        Paragraph(
            "The model estimates conditional changes from a baseline; it does "
            "not forecast absolute share prices. Reported operational facts "
            "anchor the configuration. Non-public contract, trading, cargo, "
            "and price-capture exposures are explicit assumptions. The "
            "commodity engine converts the net supply gap into nonlinear JKM, "
            "TTF, and Henry Hub shocks. Company modules then apply volume, "
            "margin, freight, feed-gas, working-capital, utilization, and "
            "geopolitical valuation effects.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 6))
    calibration_table = [
        ["Calibration item", "Value"],
        ["Status", calibration.data_status],
        ["Observations", str(calibration.observation_count)],
        ["Shell market beta", f"{calibration.shell_market_beta:.2f}"],
        ["Cheniere market beta", f"{calibration.cheniere_market_beta:.2f}"],
        ["Shell annualized volatility", _pct(calibration.shell_annualized_volatility)],
        ["Cheniere annualized volatility", _pct(calibration.cheniere_annualized_volatility)],
        ["Return correlation", f"{calibration.return_correlation:.2f}"],
    ]
    story.append(_table(calibration_table, [2.4 * inch, 3.9 * inch]))
    story.append(Paragraph("Core limitations", styles["Section"]))
    limitations = [
        "Scenario outputs are sensitive to price elasticity and company price-capture assumptions.",
        "Shell trading and optimization economics are not publicly observable at cargo level.",
        "Cheniere contract structures reduce direct spot-price exposure and differ by agreement.",
        "The model does not include taxes, FX, derivatives, financing changes, or every segment interaction.",
        "Monte Carlo distributions describe model uncertainty, not objective investment probabilities.",
    ]
    for item in limitations:
        story.append(Paragraph(f"- {item}", styles["Small"]))

    story.append(Paragraph("Source register", styles["Section"]))
    source_table = [["ID", "Source", "Publisher", "Use"]]
    for _, row in source_register.iterrows():
        source_table.append(
            [
                row["source_id"],
                Paragraph(str(row["source_name"]), styles["Small"]),
                Paragraph(str(row["publisher"]), styles["Small"]),
                Paragraph(str(row["model_use"]), styles["Small"]),
            ]
        )
    story.append(
        _table(source_table, [0.55 * inch, 2.05 * inch, 1.55 * inch, 2.75 * inch])
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            f"Model version {config['model']['version']}. For research and "
            "educational use only; not investment advice.",
            styles["Small"],
        )
    )
    def add_footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#C8D0D5"))
        canvas.setLineWidth(0.4)
        canvas.line(0.55 * inch, 0.42 * inch, 7.95 * inch, 0.42 * inch)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#5E6B73"))
        canvas.drawString(
            0.55 * inch,
            0.25 * inch,
            f"Jason Keen | Model v{config['model']['version']}",
        )
        canvas.drawRightString(
            7.95 * inch,
            0.25 * inch,
            f"Page {document.page}",
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
