#!/usr/bin/env python3
"""Weekly trading bot V2 with optional local Ollama/Qwen support.

This script builds on the existing weekly trend-following strategy in
tradingbot_weekly.py and adds an optional local AI layer for signal scoring
and strategy summary.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from tradingbot_weekly import (
    StrategyConfig,
    build_strategy_config,
    create_requests_session,
    ensure_output_dir,
    filter_symbols,
    latest_signals,
    load_symbols_file,
    market_filter,
    parse_symbols,
    performance_summary,
    prepare_symbol_frame,
    print_summary,
    run_backtest,
)

DEFAULT_OLLAMA_URL = "http://192.168.1.122:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "qwen3.6:35b-a3b-q4_K_M"
DEFAULT_LLM_LIMIT = 20
DEFAULT_LLM_TIMEOUT = 90


def build_llm_prompt(symbol: str, row: pd.Series, metadata: dict[str, Any]) -> str:
    return f"""You are a professional equity analyst. Score this symbol from 0 to 100 based on quality, momentum, and risk for a weekly trend-following strategy.

Respond only in valid JSON with keys: score, reason.

Symbol: {symbol}
Current close: {row['Close']:.2f}
Weekly signal: {metadata['Signal']}
Market status: {'OK' if metadata['MarketOk'] else 'NOT OK'}

Technical indicators:
- SMA30: {row['SMA30']:.2f}
- SMA30 slope: {row['SMA30_Slope']:.4f}
- Breakout 20w high: {row['HH20']:.2f}
- 10w low: {row['LL10']:.2f}
- TRIX: {row['TRIX']:.4f}
- TRIX signal: {row['TRIX_SIGNAL']:.4f}
- ATR: {row['ATR']:.4f}
- 12w ROC: {row['ROC12']:.4f}
- Avg weekly volume: {metadata['AvgVolume']:.0f}
- Annualized volatility: {metadata['Volatility']:.4f}

Notes:
- The strategy is weekly, entry on breakout and momentum confirmation.
- Do not use any outside information beyond the data provided here.
"""


def ollama_generate(prompt: str, base_url: str, model: str, timeout: float = DEFAULT_LLM_TIMEOUT) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(base_url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data["response"]


def parse_llm_score(raw: str) -> tuple[float, str]:
    text = raw.strip()
    try:
        candidate = json.loads(text)
        score = float(candidate.get("score", 0.0))
        return score, str(candidate.get("reason", ""))
    except json.JSONDecodeError:
        text = text.replace("'", '"')
        try:
            candidate = json.loads(text)
            score = float(candidate.get("score", 0.0))
            return score, str(candidate.get("reason", ""))
        except Exception:
            match = re.search(r"(\d+(?:\.\d+)?)", text)
            score = float(match.group(1)) if match else 0.0
            return score, text


def normalize_score(score: float) -> float:
    return max(0.0, min(100.0, score))


def score_symbol_with_ollama(
    symbol: str,
    row: pd.Series,
    metadata: dict[str, Any],
    ollama_url: str,
    ollama_model: str,
) -> tuple[float, str, str]:
    prompt = build_llm_prompt(symbol, row, metadata)
    raw = ollama_generate(prompt, ollama_url, ollama_model)
    score, reason = parse_llm_score(raw)
    return normalize_score(score), reason, raw


def latest_signals_with_ai(
    symbol_frames: dict[str, pd.DataFrame],
    spy_filter: pd.DataFrame,
    cfg: StrategyConfig,
    ollama_url: str,
    ollama_model: str,
    llm_limit: int,
) -> pd.DataFrame:
    signals = latest_signals(symbol_frames, spy_filter, cfg)
    signals["LLMScore"] = float("nan")
    signals["LLMReason"] = ""

    if signals.empty:
        return signals

    candidate_symbols = signals.sort_values(["Signal", "ROC12"], ascending=[True, False]).head(llm_limit)["Symbol"].tolist()
    print(f"AI scoring top {len(candidate_symbols)} symbols using Ollama...")

    for symbol in candidate_symbols:
        frame = symbol_frames[symbol]
        if frame.empty:
            continue
        row = frame.iloc[-1]
        avg_volume = frame["Volume"].mean()
        returns = frame["Close"].pct_change().dropna()
        volatility = float(returns.std() * math.sqrt(52)) if not returns.empty else 0.0
        metadata = {
            "Signal": "BUY" if row["Close"] > row["HH20"] and row["TRIX"] > row["TRIX_SIGNAL"] else "WAIT",
            "MarketOk": bool(spy_filter.set_index("Date").loc[row["Date"], "MARKET_OK"] if row["Date"] in spy_filter["Date"].values else False),
            "AvgVolume": avg_volume,
            "Volatility": volatility,
        }
        try:
            score, reason, raw = score_symbol_with_ollama(symbol, row, metadata, ollama_url, ollama_model)
            signals.loc[signals["Symbol"] == symbol, "LLMScore"] = score
            signals.loc[signals["Symbol"] == symbol, "LLMReason"] = reason
            print(f"{symbol}: score={score:.1f}")
        except Exception as exc:
            print(f"Ollama scoring failed for {symbol}: {exc}")

    return signals


def generate_llm_strategy_report(
    summary: dict[str, float],
    top_signals: pd.DataFrame,
    ollama_url: str,
    ollama_model: str,
    output_path: Path,
) -> None:
    metrics = json.dumps(summary, indent=2)
    symbol_list = top_signals.head(10).to_dict(orient="records")
    prompt = f"""You are an expert quantitative trader.

Here is a backtest summary for a weekly trend-following system:
{metrics}

Top signals:
{json.dumps(symbol_list, indent=2, default=str)}

Write a short, practical evaluation of this strategy, including:
- the main strengths
- main weaknesses
- one realistic improvement to test next

Respond in plain text."""
    try:
        report = ollama_generate(prompt, ollama_url, ollama_model)
        output_path.write_text(report, encoding="utf-8")
        print(f"Saved AI strategy report to: {output_path}")
    except Exception as exc:
        print(f"Failed to generate AI report: {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weekly trend-following trading bot V2 with local Ollama support")
    parser.add_argument("--symbols", default="AAPL,MSFT,NVDA,AMZN,GOOGL,META", help="Comma-separated stock symbols")
    parser.add_argument("--symbols-file", default="symbols.txt", help="Path to a file containing one symbol per line")
    parser.add_argument("--benchmark", default="SPY", help="Benchmark / market filter symbol")
    parser.add_argument("--years", type=int, default=8, help="Years of daily history to download")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital")
    parser.add_argument("--risk", type=float, default=0.01, help="Risk per trade, e.g. 0.01 for 1%%")
    parser.add_argument("--max-positions", type=int, default=5, help="Maximum simultaneous positions")
    parser.add_argument("--strategy", choices=["default", "aggressive"], default="default", help="Strategy profile for weekly trading")
    parser.add_argument("--volume-min", type=int, default=100000, help="Minimum average weekly volume to include symbol")
    parser.add_argument("--volatility-max", type=float, default=0.8, help="Maximum historical volatility (annualized) to include symbol")
    parser.add_argument("--output-dir", default="output", help="Where CSV exports are written")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Local Ollama server URL")
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL, help="Ollama model name")
    parser.add_argument("--llm-enable", action="store_true", help="Enable Ollama scoring and strategy summary generation")
    parser.add_argument("--llm-limit", type=int, default=DEFAULT_LLM_LIMIT, help="Maximum symbols to score with Ollama")
    parser.add_argument("--llm-report", default="output/llm_strategy_report.txt", help="Path to save AI strategy report")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = build_strategy_config(args)

    end_date = dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)
    start_date = end_date - dt.timedelta(days=365 * args.years)
    if args.symbols_file:
        symbols = load_symbols_file(args.symbols_file)
    else:
        symbols = parse_symbols(args.symbols)

    output_dir = ensure_output_dir(args.output_dir)
    llm_report_path = Path(args.llm_report)
    llm_report_path.parent.mkdir(parents=True, exist_ok=True)

    with create_requests_session() as session:
        spy_weekly = prepare_symbol_frame(args.benchmark, start=start_date, end=end_date, cfg=cfg, session=session)
        spy_filter = market_filter(spy_weekly, cfg)

        symbol_frames: dict[str, pd.DataFrame] = {}
        for symbol in symbols:
            try:
                symbol_frames[symbol] = prepare_symbol_frame(symbol, start=start_date, end=end_date, cfg=cfg, session=session)
                print(f"Loaded {symbol}: {len(symbol_frames[symbol])} weekly bars")
            except Exception as exc:
                print(f"Skipping {symbol}: {exc}")

    if not symbol_frames:
        raise SystemExit("No symbol data could be loaded.")

    symbol_frames = filter_symbols(symbol_frames, args.volume_min, args.volatility_max)
    if not symbol_frames:
        raise SystemExit("No symbols passed quality filters.")

    trades_df, equity_df = run_backtest(symbol_frames, spy_filter, cfg)
    signals_df = latest_signals(symbol_frames, spy_filter, cfg)

    if args.llm_enable:
        signals_df = latest_signals_with_ai(
            symbol_frames,
            spy_filter,
            cfg,
            args.ollama_url,
            args.ollama_model,
            args.llm_limit,
        )

    summary = performance_summary(trades_df, equity_df, cfg)

    export_dir = Path(output_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    trades_df.to_csv(export_dir / "trades_v2.csv", index=False)
    equity_df.to_csv(export_dir / "equity_curve_v2.csv", index=False)
    signals_df.to_csv(export_dir / "latest_signals_v2.csv", index=False)
    pd.DataFrame([summary]).to_csv(export_dir / "summary_v2.csv", index=False)

    print_summary(summary)
    print("\n=== Latest Signals ===")
    print(signals_df.head(20).to_string(index=False))
    print(f"\nCSV files written to: {export_dir.resolve()}")

    if args.llm_enable:
        generate_llm_strategy_report(summary, signals_df, args.ollama_url, args.ollama_model, llm_report_path)


if __name__ == "__main__":
    main()
