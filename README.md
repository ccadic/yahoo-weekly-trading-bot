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

Performance Summary (5-Year Backtest)
Based on a diversified universe of approximately 80 global stocks (US, Europe, Asia), filtered for liquidity (>100k average weekly volume) and volatility (<0.8 annualized):

Annualized Return: 15.37%
Max Drawdown: -16.41%
Total Trades: 187 (approximately 37 per year)
Win Rate: 46.52%
Profit Factor: 2.55
Sharpe Ratio: 1.18
The strategy demonstrates consistent outperformance compared to buy-and-hold in trending markets, with controlled risk and no curve-fitting. Results may vary depending on market conditions and symbol selection.

Description de l'algorithme (en anglais)
Algorithm Overview
This weekly trading bot implements a trend-following swing strategy inspired by classic approaches like Turtle Trading and CAN SLIM, adapted for modern portfolio backtesting.

Data Processing
Fetches daily OHLCV data directly from Yahoo Finance's chart API using requests (no yfinance dependency).
Aggregates daily bars into weekly OHLCV candles locally for consistency and reliability.
Applies quality filters: minimum average weekly volume (default 100k) and maximum annualized volatility (default 0.8) to exclude illiquid or overly risky assets.
Indicators and Signals
Market Filter: SPY (benchmark) must be above its 30-week SMA to ensure bullish market conditions.
Trend Confirmation: Stock close > 30-week SMA with positive SMA slope.
Entry Signal: Breakout above the 20-week high, confirmed by TRIX oscillator (length 15, signal 9) where TRIX > TRIX signal.
Exit Signals:
Trend reversal: Close < 10-week EMA.
Breakout failure: Close < 10-week low.
Stop loss: ATR-based (2x ATR multiple below entry price).
Momentum: TRIX (triple exponential moving average) for short-term momentum confirmation.
Risk Management
Position sizing: Risk 1-2% of capital per trade, calculated as (entry price - stop price) * shares.
Max positions: 5-8 simultaneous holdings to diversify.
Aggressive mode: Shorter SMAs (20 weeks), faster breakouts (15 weeks), tighter exits for higher frequency in growth-oriented markets.
Backtesting Engine
Simulates weekly execution: Entries/exits at Friday close.
Tracks equity curve, trades, drawdowns, and performance metrics.
Outputs CSV files for detailed analysis (trades, equity, signals).
This algorithm is designed for long-term, low-frequency trading, balancing trend capture with risk control. It performs well in bull markets but may underperform in sideways or bearish conditions due to its trend-following nature.
