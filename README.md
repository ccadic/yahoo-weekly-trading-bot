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

## Optional V2: Local Ollama AI Support

A second script, `tradingbot_weekly_V2.py`, extends the base strategy with optional local Ollama/Qwen AI integration for enhanced signal scoring and strategy analysis.

### Setup and Configuration

To use the AI features, you need a local Ollama server running with a compatible model. The script defaults are configured for:

```python
DEFAULT_OLLAMA_URL = "http://192.168.1.122:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "qwen3.6:35b-a3b-q4_K_M"
DEFAULT_LLM_LIMIT = 20
DEFAULT_LLM_TIMEOUT = 90
```

Adjust these constants in the code if your Ollama setup differs (e.g., different IP, port, or model name).

### Usage

```bash
python tradingbot_weekly_V2.py --symbols-file symbols.txt --strategy aggressive --risk 0.02 --max-positions 8 --llm-enable
```

The V2 script:
- Preserves the existing weekly strategy and backtest engine unchanged
- Adds optional AI scoring for top candidate symbols when `--llm-enable` is used
- Generates an AI-powered strategy summary report
- Writes outputs to `output/` with `_v2` suffixes

### How the AI Scoring Works

#### 1. Signal Generation First
The core algorithm runs a weekly trend-following strategy:
- Downloads 8 years of daily data from Yahoo Finance
- Converts to weekly bars (Friday close)
- Calculates technical indicators:
  - **SMA30**: 30-week simple moving average
  - **SMA30 Slope**: Rate of change in the moving average
  - **HH20**: 20-week high (breakout level)
  - **LL10**: 10-week low (stop level)
  - **TRIX**: Triple exponential moving average (momentum)
  - **TRIX_SIGNAL**: Signal line for TRIX
  - **ATR**: Average True Range (volatility measure)
  - **ROC12**: 12-week rate of change (momentum)
- Generates BUY signals when: `Close > HH20` AND `TRIX > TRIX_SIGNAL`
- Filters for volume (>100k average weekly) and volatility (<80% annualized)

#### 2. AI Evaluation Layer
For the top 20 signals (sorted by signal priority + ROC12 momentum), the script sends this data to your local Ollama model:

**Prompt Structure:**
- Symbol basics (current close, signal status, market OK/NOT OK)
- All technical indicators listed above
- Average weekly volume and annualized volatility
- Instructions: "Score this symbol from 0 to 100 based on quality, momentum, and risk for a weekly trend-following strategy. Respond only in valid JSON with keys: score, reason."

**What the AI Considers:**
- **Quality**: Liquidity (volume), appropriate volatility
- **Momentum**: Strength of breakout, TRIX confirmation, ROC trends
- **Risk**: Distance from stops, volatility levels, market conditions

#### 3. Score Interpretation
- **80-100**: Excellent setup - strong momentum, good risk/reward, high conviction
- **60-79**: Good setup - solid signals but some caution needed
- **40-59**: Moderate - mixed signals, higher risk
- **20-39**: Weak - questionable momentum or high risk
- **0-19**: Poor - avoid, likely false signal or high risk

#### 4. Integration with Backtest
- AI scores are added as a new column `LLMScore` in the signals output
- They don't change the backtest results (which use pure technical rules)
- You can use them to prioritize which signals to act on in real trading
- The strategy report also receives AI-generated analysis

**Example Scores:**
- 5803.T (score=76.0): Strong setup - likely good momentum confirmation with reasonable risk
- MTZ (score=82.0): Excellent setup - high conviction signal with favorable technicals

The AI acts as a "second opinion" layer, potentially catching nuances that the rules-based system might miss, while keeping the core strategy intact for backtesting integrity.

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

Then run the bot without specifying `--symbols`:

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

