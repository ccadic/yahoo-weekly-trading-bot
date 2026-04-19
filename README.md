# yahoo-weekly-trading-bot
Python-based weekly swing trading bot that fetches data from Yahoo Finance's chart API (without using yfinance) and applies a robust trend-following strategy with breakout and TRIX momentum indicators.

# Yahoo Weekly Trading Bot

A Python-based weekly swing trading bot that fetches data from Yahoo Finance's chart API (without using yfinance) and applies a robust trend-following strategy with breakout and TRIX momentum indicators.

## Features

- **Data Source**: Direct queries to Yahoo Finance chart endpoint for daily bars, rebuilt into weekly OHLCV locally.
- **Strategy**: Trend-following with market filter (SPY SMA), breakout entries (20-week highs), momentum confirmation (TRIX), and ATR-based stops.
- **Backtesting**: Simple portfolio simulation with risk management (position sizing, max positions).
- **Filters**: Liquidity (volume) and volatility filters to avoid illiquid or overly risky assets.
- **Output**: CSV exports for trades, equity curve, and latest signals.

## Strategy Details

- Market filter: SPY > SMA 30 weeks
- Trend: Close > SMA 30 weeks with positive slope
- Entry: Breakout above 20-week high + TRIX > signal
- Exit: Close < EMA 10 weeks, or < 10-week low, or ATR stop (2x multiple)
- Risk: 1-2% per trade, max 5-8 positions

## Requirements

- Python 3.10+
- pandas, numpy, requests

## Usage

```bash
python tradingbot_weekly.py --symbols-file symbols.txt --strategy aggressive --risk 0.02 --max-positions 8 --years 5
