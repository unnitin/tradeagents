# 📊 Data Module

The `data/` module provides utilities for fetching, preprocessing, and engineering features from financial time-series data. It serves as the backbone of any strategy, backtest, or live trading system.

---

## Contents

- `fetch_data.py` – Historical data acquisition from Yahoo Finance.
- `preprocess.py` – Resampling of OHLCV time series.
- `features.py` – Core technical indicators used for feature engineering.
- `feature_pipeline.py` – Unified feature application pipeline.
- `constants.py` – Immutable mappings for safe and standardized transformations.

---

## 🔍 Feature Engineering Functions (in `features.py`)

### `add_sma(df, window=20)`
**Simple Moving Average**

- **What it does:** Adds a rolling average of the closing price over a fixed window.
- **Trading use:** Identify trend direction and crossover points.
- **How it is calculated:**  
  - `SMA_t = (Close_t + Close_{t-1} + ... + Close_{t-N+1}) / N`  
  - Uses `.rolling(window).mean()`

---

### `add_ema(df, window=20)`
**Exponential Moving Average**

- **What it does:** Weighted average that emphasizes more recent prices.
- **Trading use:** Faster than SMA, used in trend and momentum systems.
- **How it is calculated:**  
  - `EMA_t = Price_t * K + EMA_{t-1} * (1 – K)`  
  - `K = 2 / (N + 1)`  
  - Uses `.ewm(span=window, adjust=False).mean()`

---

### `add_rsi(df, window=14)`
**Relative Strength Index**

- **What it does:** Oscillator indicating momentum, highlighting overbought/oversold conditions.
- **Trading use:** Reversion setups; divergence signals.
- **How it is calculated:**  
  - Compute gains/losses over `N` periods  
  - `RS = avg_gain / avg_loss`  
  - `RSI = 100 - (100 / (1 + RS))`  
  - Smoothed with `.rolling(window).mean()`

---

### `add_bollinger_bands(df, window=20, num_std=2.0)`
**Bollinger Bands**

- **What it does:** Constructs upper/lower volatility bands around a moving average.
- **Trading use:** Detecting overextensions from mean; breakout detection.
- **How it is calculated:**  
  - `Middle Band = SMA(window)`  
  - `Upper Band = SMA + (std * num_std)`  
  - `Lower Band = SMA - (std * num_std)`

---

### `add_macd(df, fast=12, slow=26, signal=9)`
**MACD – Moving Average Convergence Divergence**

- **What it does:** Measures momentum via difference in fast vs slow EMAs.
- **Trading use:** Trend reversal and momentum-based entries.
- **How it is calculated:**  
  - `MACD Line = EMA(12) - EMA(26)`  
  - `Signal Line = EMA(9) of MACD Line`  
  - `Histogram = MACD - Signal`

---

### `add_atr(df, window=14)`
**ATR – Average True Range**

- **What it does:** Measures average daily volatility.
- **Trading use:** Stop placement, volatility filters.
- **How it is calculated:**  
  - `TR_t = max(High - Low, |High - PrevClose|, |Low - PrevClose|)`  
  - `ATR = rolling mean of TR over N periods`

---

## 🔁 `feature_pipeline.py`

### Function: `apply_feature_pipeline(df)`

- **What it does:** Applies all indicators in a single processing step.
- **Includes:**
  - `SMA_20`, `EMA_20`, `RSI_14`
  - `Bollinger Bands` (20, 2.0)
  - `MACD` (12/26/9)
  - `ATR_14`
- **Returns:** Feature-rich `DataFrame` ready for strategy execution.

---

## 🧠 Strategy Design Tip

Each indicator may serve as:
- A **signal generator** (e.g., RSI < 30 = buy)
- A **filter** (e.g., only trade when ATR > X)
- A **volatility gate** or **trend condition**

Combine multiple features for **robust** and **context-aware** strategies.

---

## 🛠️ How to Use

```python
from data.fetch_data import get_data
from data.feature_pipeline import apply_feature_pipeline

df = get_data("AAPL", interval="1m", start="2024-06-01", end="2024-06-07")
df = apply_feature_pipeline(df)
