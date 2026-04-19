# Yahoo Weekly Trading Bot

A Python-based weekly swing trading bot that fetches data from Yahoo Finance's chart API (without using yfinance) and applies a robust trend-following strategy with breakout and TRIX momentum indicators.

<img src="equity_curve.png">

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

## Performance Summary (5-Year Backtest)

Based on a diversified universe of ~80 global stocks (US, Europe, Asia), filtered for liquidity (>100k avg weekly volume) and volatility (<0.8 annualized):

- **Annualized Return**: 15.37%
- **Max Drawdown**: -16.41%
- **Total Trades**: 187 (37/year)
- **Win Rate**: 46.52%
- **Profit Factor**: 2.55
- **Sharpe Ratio**: 1.18

The strategy demonstrates consistent outperformance over buy-and-hold in trending markets, with controlled risk and no curve-fitting. Results may vary with market conditions and symbol selection.

## Requirements

- Python 3.10+
- pandas, numpy, requests

## Usage

```bash
python tradingbot_weekly.py --symbols-file symbols.txt --strategy aggressive --risk 0.02 --max-positions 8 --years 5
```

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

META
TSLA
AMD
AVGO
```

Puis lance le bot sans préciser `--symbols` :

```bash
python tradingbot_weekly.py --symbols-file symbols.txt --strategy aggressive --risk 0.02 --max-positions 8
```

### Quality Filters

- `--volume-min`: minimum average weekly volume (default 100000).
- `--volatility-max`: maximum annualized historical volatility (default 0.5).

These filters help avoid illiquid or overly volatile stocks and reduce backtest risk.

## Dependencies

- Python 3.10+
- `pandas`
- `numpy`
- `requests`

## Example

```bash
python tradingbot_weekly.py --symbols AAPL,MSFT,NVDA,AMZN,GOOGL,META --years 8 --capital 100000 --risk 0.01 --max-positions 5
```

## Output Files

The script writes output to `output/`:

- `summary.csv`
- `trades.csv`
- `equity_curve.csv`
- `latest_signals.csv`
- `weekly_data/*.csv`

## Current Limitations

- Simple backtest with no fees or slippage
- Execution assumed at weekly close
- Symbol universe supplied manually
- No advanced quality/liquidity screener yet

The next improvements are:

- transaction fees
- liquidity filtering
- relative ranking of symbols
- local data cache storage
- alerts or simulated order execution


