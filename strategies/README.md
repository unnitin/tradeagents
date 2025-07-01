# Trading Strategies

This directory contains algorithmic trading strategies implemented in Python. Each strategy generates buy/sell/hold signals based on technical indicators.

## Strategies Overview

### 1. ATRVolatilityFilter ([atr_filter.py](./atr_filter.py))
- **Purpose:** Acts as a volatility filter using the Average True Range (ATR).
- **Parameters:**
  - `atr_col` (str): Name of the ATR column in the DataFrame. Default: `"atr_14"`.
  - `window` (int): Rolling window size for the mean ATR. Default: `50`.
- **Logic:**
  - Compares the current ATR value to its rolling mean over a window.
  - Returns 1 if volatility is high (ATR > rolling mean), else 0.

### 2. BollingerBounce ([bollinger_bounce.py](./bollinger_bounce.py))
- **Purpose:** Generates signals based on price bouncing off Bollinger Bands.
- **Parameters:**
  - `bb_window` (int): Window size for calculating Bollinger Bands. Default: `20`.
- **Logic:**
  - Returns 1 if the close price is below the lower Bollinger Band (potential buy).
  - Returns -1 if the close price is above the upper Bollinger Band (potential sell).
  - Returns 0 otherwise.

### 3. MACDCross ([macd_cross.py](./macd_cross.py))
- **Purpose:** Uses MACD indicator crossovers for signals.
- **Parameters:**
  - `macd_col` (str): Name of the MACD column in the DataFrame. Default: `"macd"`.
  - `signal_col` (str): Name of the MACD signal line column. Default: `"macd_signal"`.
- **Logic:**
  - Returns 1 when MACD crosses ABOVE the signal line (bullish crossover).
  - Returns -1 when MACD crosses BELOW the signal line (bearish crossover).
  - Returns 0 otherwise (no crossover).

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

### 5. SMACrossover ([sma_crossover.py](./sma_crossover.py))
- **Purpose:** Simple Moving Average crossover strategy.
- **Parameters:**
  - `fast` (int): Window size for the fast SMA. Default: `20`.
  - `slow` (int): Window size for the slow SMA. Default: `50`.
- **Logic:**
  - Returns 1 when the fast SMA crosses ABOVE the slow SMA (bullish crossover).
  - Returns -1 when the fast SMA crosses BELOW the slow SMA (bearish crossover).
  - Returns 0 otherwise (no crossover).

---

## 🏛️ Politician Tracking Strategies

### Overview
Politician tracking strategies follow the trading activity of elected officials based on their public SEC filings. For complete setup instructions, implementation examples, and API integration, see the **[🏛️ Politician Trade Tracking](../README.md#-politician-trade-tracking)** section in the main README.

### Quick Start
1. **Twitter Method (Free)**: Follow @PelosiTracker for real-time alerts
2. **API Method ($10/month)**: Use Quiver Quantitative for automated tracking
3. **Hybrid Approach**: Combine both for comprehensive coverage

### Implementation Files
- `../data/politician_trades_live.py`: Live API integration
- `../data/twitter_politician_tracker.py`: Twitter monitoring
- `../examples/easy_politician_tracking.py`: Complete examples

---

For implementation details, see each respective Python file.
