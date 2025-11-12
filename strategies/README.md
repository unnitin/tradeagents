# Trading Strategies

This directory contains algorithmic trading strategies implemented in Python. Each strategy generates buy/sell/hold signals based on technical indicators and can be tested using the comprehensive backtest module.

| Strategy | Category | Highlights |
| --- | --- | --- |
| `SMACrossover` | Technical trend | Fast/slow moving average crossovers. |
| `RSIReversion` | Technical mean reversion | Oversold/overbought thresholds. |
| `MACDCross` | Momentum | MACD vs signal line cross logic. |
| `BollingerBounce` | Volatility | Trades bounces at Bollinger Bands. |
| `ATRVolatilityFilter` | Filter | Volatility gate using ATR z-scores. |
| `SentimentLLMStrategy` | NLP / News agent | Uses FinBERT to convert headlines into signals. |
| `PoliticianFollowingStrategy` / `PelosiTrackingStrategy` / `CongressMomentumStrategy` | Alternative data | Mirror congressional trades or crowd momentum. |

Each class inherits from `Strategy` (`base.py`), meaning they all support filter attachments, symbol-specific filtering, and context-driven configuration. This aligns with the “Strategy Agents” portion of `spec.md`, enabling modular plug-and-play within the composer and agent layers.

## 🚀 **NEW: Backtest Integration**

All strategies are now fully integrated with the **comprehensive backtest module** for performance evaluation:

```python
# Example: Test any strategy with backtesting
from backtest import create_backtest_engine
from strategies import RSIReversion, SMACrossover

# Create backtest engine
engine = create_backtest_engine()

# Test individual strategy
strategy = RSIReversion(low_thresh=25, high_thresh=75)
results = engine.run_backtest(
    strategy=strategy,
    symbols=["AAPL", "MSFT"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# View performance metrics
print(f"Total Return: {results.metrics.total_return:.2%}")
print(f"Sharpe Ratio: {results.metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.metrics.max_drawdown:.2%}")
```

### **Strategy Combination Testing**
```python
# Test multiple strategies together using composer
results = engine.run_composer_backtest(
    combination_name="technical_ensemble",
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

---

## Strategies Overview

### 1. ATRVolatilityFilter ([atr_filter.py](./atr_filter.py))
- **Purpose:** Acts as a volatility filter using the Average True Range (ATR).
- **Parameters:**
  - `atr_col` (str): Name of the ATR column in the DataFrame. Default: `"atr_14"`.
  - `window` (int): Rolling window size for the mean ATR. Default: `50`.
- **Logic:**
  - Compares the current ATR value to its rolling mean over a window.
  - Returns 1 if volatility is high (ATR > rolling mean), else 0.
- **✅ Backtest Ready**: Fully tested with 99% test coverage

### 2. BollingerBounce ([bollinger_bounce.py](./bollinger_bounce.py))
- **Purpose:** Generates signals based on price bouncing off Bollinger Bands.
- **Parameters:**
  - `bb_window` (int): Window size for calculating Bollinger Bands. Default: `20`.
- **Logic:**
  - Returns 1 if the close price is below the lower Bollinger Band (potential buy).
  - Returns -1 if the close price is above the upper Bollinger Band (potential sell).
  - Returns 0 otherwise.
- **✅ Backtest Ready**: Supports filtering and performance analysis

### 3. MACDCross ([macd_cross.py](./macd_cross.py))
- **Purpose:** Uses MACD indicator crossovers for signals.
- **Parameters:**
  - `macd_col` (str): Name of the MACD column in the DataFrame. Default: `"macd"`.
  - `signal_col` (str): Name of the MACD signal line column. Default: `"macd_signal"`.
- **Logic:**
  - Returns 1 when MACD crosses ABOVE the signal line (bullish crossover).
  - Returns -1 when MACD crosses BELOW the signal line (bearish crossover).
  - Returns 0 otherwise (no crossover).
- **✅ Backtest Ready**: Excellent for trend-following backtests

### 4. RSIReversion ([rsi_reversion.py](./rsi_reversion.py))
- **Purpose:** Mean reversion strategy using the Relative Strength Index (RSI).
- **Parameters:**
  - `rsi_col` (str): Name of the RSI column in the DataFrame. Default: `"rsi_14"`.
  - `low_thresh` (float): Lower threshold for RSI (oversold). Default: `30`.
  - `high_thresh` (float): Upper threshold for RSI (overbought). Default: `70`.
- **Logic:**
  - Returns 1 if RSI is below a low threshold (oversold).
  - Returns -1 if RSI is above a high threshold (overbought).
  - Returns 0 otherwise.
- **✅ Backtest Ready**: Popular for mean-reversion backtests

### 5. SMACrossover ([sma_crossover.py](./sma_crossover.py))
- **Purpose:** Simple Moving Average crossover strategy.
- **Parameters:**
  - `fast` (int): Window size for the fast SMA. Default: `20`.
  - `slow` (int): Window size for the slow SMA. Default: `50`.
- **Logic:**
  - Returns 1 when the fast SMA crosses ABOVE the slow SMA (bullish crossover).
  - Returns -1 when the fast SMA crosses BELOW the slow SMA (bearish crossover).
  - Returns 0 otherwise (no crossover).
- **✅ Backtest Ready**: Classic trend-following strategy

### 6. SentimentLLM ([sentiment_llm.py](./sentiment_llm.py))
- **Purpose:** AI-powered sentiment analysis for trading signals.
- **Features:** Uses LLM models to analyze market sentiment and news
- **✅ Backtest Ready**: Advanced AI-driven strategy testing

### 7. PoliticianFollowing ([politician_following.py](./politician_following.py))
- **Purpose:** Follows politician trading patterns from SEC filings.
- **Features:** Tracks congressional trades with configurable following strategies
- **✅ Backtest Ready**: Test political trade following strategies

---

## 📊 **Backtest Performance Examples**

### **Individual Strategy Performance**
```python
# Compare multiple strategies
from backtest import create_backtest_engine
from strategies import RSIReversion, SMACrossover, MACDCross

engine = create_backtest_engine()
strategies = [
    RSIReversion(low_thresh=30, high_thresh=70),
    SMACrossover(fast=20, slow=50),
    MACDCross()
]

results = {}
for strategy in strategies:
    result = engine.run_backtest(
        strategy=strategy,
        symbols="AAPL",
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    results[strategy.__class__.__name__] = result

# Compare performance
for name, result in results.items():
    print(f"{name}: {result.metrics.total_return:.2%} return, "
          f"{result.metrics.sharpe_ratio:.2f} Sharpe")
```

### **Advanced Filtering and Analysis**
```python
# Use advanced filters
from filters import StockFilter, TimeFilter

# Filter for high-volume, stable stocks
stock_filter = StockFilter(
    min_volume=2000000,      # High volume
    min_price=50,            # Avoid penny stocks  
    max_volatility=0.3       # Limit volatility
)

# Exclude earnings periods and holidays
time_filter = TimeFilter(
    exclude_earnings_periods=True,
    exclude_market_holidays=True,
    min_trading_days=200     # Ensure sufficient data
)

# Run filtered backtest
results = engine.run_backtest(
    strategy=RSIReversion(),
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    stock_filter=stock_filter,
    time_filter=time_filter
)
```

---

## 🎼 **Strategy Combination with Composer**

All strategies can be combined using the composer module:

```python
# Create strategy ensemble
from composer import create_composer

composer = create_composer("config/strategies.yaml")

# Test ensemble performance
results = engine.run_composer_backtest(
    combination_name="technical_ensemble",
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# Compare individual vs ensemble
print(f"Ensemble Return: {results.metrics.total_return:.2%}")
print(f"Ensemble Sharpe: {results.metrics.sharpe_ratio:.2f}")
```

---

## 🏛️ Politician Tracking Strategies

### Overview
Politician tracking strategies follow the trading activity of elected officials based on their public SEC filings. For complete setup instructions, implementation examples, and API integration, see the **[🏛️ Politician Trade Tracking](../README.md#-politician-trade-tracking)** section in the main README.

### **Backtest Integration**
```python
# Test politician following strategy
from strategies import PoliticianFollowing

politician_strategy = PoliticianFollowing(
    politicians=['Pelosi', 'AOC', 'Cruz'],
    delay_days=45,  # SEC filing delay
    min_trade_value=10000
)

results = engine.run_backtest(
    strategy=politician_strategy,
    symbols=["AAPL", "NVDA", "TSLA"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

### Quick Start
1. **Twitter Method (Free)**: Follow @PelosiTracker for real-time alerts
2. **API Method ($10/month)**: Use Quiver Quantitative for automated tracking
3. **Hybrid Approach**: Combine both for comprehensive coverage

### Implementation Files
- `../data/politician_trades_live.py`: Live API integration
- `../data/twitter_politician_tracker.py`: Twitter monitoring
- `../examples/politician_tracking_example.py`: Complete examples

---

## 🧪 **Testing and Examples**

### **Run Strategy Tests**
```bash
# Test all strategies
python -m pytest tests/unit_test/test_strategies.py -v

# Test specific strategy integration
python tests/test_backtest_runner.py

# Run backtest examples
python examples/backtest_example.py
python examples/backtest_comprehensive_example.py
```

### **Performance Analysis**
Each strategy includes comprehensive performance metrics:
- **Return Metrics**: Total, annualized, benchmark comparison
- **Risk Metrics**: Volatility, Sharpe ratio, max drawdown, VaR
- **Trade Metrics**: Win rate, profit factor, trade frequency
- **Statistical Tests**: Significance testing, correlation analysis

---

For implementation details and advanced usage, see each respective Python file and the comprehensive backtest documentation.
