"""Optional market-data calibration with a documented offline fallback."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MarketCalibration:
    data_status: str
    observation_count: int
    start_date: str
    end_date: str
    shell_market_beta: float
    cheniere_market_beta: float
    shell_annualized_volatility: float
    cheniere_annualized_volatility: float
    return_correlation: float
    note: str

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(self)])


def _fallback(config: dict[str, Any], note: str) -> MarketCalibration:
    companies = config["companies"]
    return MarketCalibration(
        data_status="configured_fallback",
        observation_count=0,
        start_date="not_available",
        end_date="not_available",
        shell_market_beta=float(companies["Shell"]["fallback_market_beta"]),
        cheniere_market_beta=float(companies["Cheniere"]["fallback_market_beta"]),
        shell_annualized_volatility=float(
            companies["Shell"]["fallback_annualized_volatility"]
        ),
        cheniere_annualized_volatility=float(
            companies["Cheniere"]["fallback_annualized_volatility"]
        ),
        return_correlation=float(config["model"]["residual_return_correlation"]),
        note=note,
    )


def _beta(asset: pd.Series, market: pd.Series) -> float:
    aligned = pd.concat([asset, market], axis=1).dropna()
    if len(aligned) < 30 or aligned.iloc[:, 1].var() == 0:
        raise ValueError("Insufficient aligned observations for beta.")
    return float(aligned.cov().iloc[0, 1] / aligned.iloc[:, 1].var())


def calibrate_market_data(
    config: dict[str, Any],
    cache_dir: Path,
    offline: bool,
) -> MarketCalibration:
    """Calibrate weekly equity betas and volatility when yfinance is available."""
    if offline:
        return _fallback(config, "Offline mode requested; configuration values used.")

    try:
        import yfinance as yf
    except ImportError:
        return _fallback(
            config,
            "yfinance is not installed; configuration values used.",
        )

    tickers = ["SHEL", "LNG", "SPY"]
    try:
        prices = yf.download(
            tickers=tickers,
            period="3y",
            interval="1wk",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if isinstance(prices.columns, pd.MultiIndex):
            prices = prices["Close"]
        elif "Close" in prices.columns:
            prices = prices[["Close"]].rename(columns={"Close": tickers[0]})
        prices = prices[tickers].dropna(how="all")
        returns = prices.pct_change(fill_method=None).dropna()
        if len(returns) < 30:
            raise ValueError("Fewer than 30 weekly return observations.")

        cache_dir.mkdir(parents=True, exist_ok=True)
        prices.to_csv(cache_dir / "market_prices_weekly.csv", index_label="date")
        returns.to_csv(cache_dir / "market_returns_weekly.csv", index_label="date")

        shell_vol = float(returns["SHEL"].std(ddof=1) * np.sqrt(52))
        cheniere_vol = float(returns["LNG"].std(ddof=1) * np.sqrt(52))
        return MarketCalibration(
            data_status="live",
            observation_count=int(len(returns)),
            start_date=str(returns.index.min().date()),
            end_date=str(returns.index.max().date()),
            shell_market_beta=_beta(returns["SHEL"], returns["SPY"]),
            cheniere_market_beta=_beta(returns["LNG"], returns["SPY"]),
            shell_annualized_volatility=shell_vol,
            cheniere_annualized_volatility=cheniere_vol,
            return_correlation=float(returns[["SHEL", "LNG"]].corr().iloc[0, 1]),
            note="Weekly adjusted-close calibration from yfinance.",
        )
    except Exception as exc:
        return _fallback(
            config,
            f"Live calibration failed ({type(exc).__name__}); configuration values used.",
        )

