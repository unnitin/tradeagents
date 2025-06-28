# Trading Strategies

This directory contains algorithmic trading strategies implemented in Python. Each strategy generates buy/sell/hold signals based on technical indicators.

## Strategies Overview

### 1. ATRVolatilityFilter (`atr_filter.py`)
- **Purpose:** Acts as a volatility filter using the Average True Range (ATR).
- **Parameters:**
  - `atr_col` (str): Name of the ATR column in the DataFrame. Default: `"atr_14"`.
  - `window` (int): Rolling window size for the mean ATR. Default: `50`.
- **Logic:**
  - Compares the current ATR value to its rolling mean over a window.
  - Returns 1 if volatility is high (ATR > rolling mean), else 0.

### 2. BollingerBounce (`bollinger_bounce.py`)
- **Purpose:** Generates signals based on price bouncing off Bollinger Bands.
- **Parameters:**
  - `bb_window` (int): Window size for calculating Bollinger Bands. Default: `20`.
- **Logic:**
  - Returns 1 if the close price is below the lower Bollinger Band (potential buy).
  - Returns -1 if the close price is above the upper Bollinger Band (potential sell).
  - Returns 0 otherwise.

### 3. MACDCross (`macd_cross.py`)
- **Purpose:** Uses MACD indicator crossovers for signals.
- **Parameters:**
  - `macd_signal` (int): Column index or name for the MACD signal line. Default: `10`.
- **Logic:**
  - Returns 1 if MACD is above the signal line.
  - Returns -1 if MACD is below the signal line.
  - Returns 0 otherwise.

### 4. RSIReversion (`rsi_reversion.py`)
- **Purpose:** Mean reversion strategy using the Relative Strength Index (RSI).
- **Parameters:**
  - `rsi_col` (str): Name of the RSI column in the DataFrame. Default: `"rsi_14"`.
  - `low_thresh` (float): Lower threshold for RSI (oversold). Default: `30`.
  - `high_thresh` (float): Upper threshold for RSI (overbought). Default: `70`.
- **Logic:**
  - Returns 1 if RSI is below a low threshold (oversold).
  - Returns -1 if RSI is above a high threshold (overbought).
  - Returns 0 otherwise.

### 5. SMACrossover (`sma_crossover.py`)
- **Purpose:** Simple Moving Average crossover strategy.
- **Parameters:**
  - `fast` (int): Window size for the fast SMA. Default: `20`.
  - `slow` (int): Window size for the slow SMA. Default: `50`.
- **Logic:**
  - Returns 1 if the fast SMA crosses above the slow SMA (bullish).
  - Returns -1 if the fast SMA crosses below the slow SMA (bearish).
  - Returns 0 otherwise.

---

For implementation details, see each respective Python file.
