# Strategy Composer Module

## Overview

The Strategy Composer module provides a flexible framework for combining and executing trading strategies. It serves as the orchestration layer that connects data processing, strategy execution, and downstream systems.

### Architecture & Flow

The composer follows this execution flow:
**data → composer (reading from config, strategies) → backtester → execution**

### Core Functionality

1. **Strategy Registration & Management**
   - Access the `strategies/` module and initiate objects of the classes
   - Read configurations from YAML files in `config/` directory
   - Support for individual and combined strategy execution

2. **Strategy Combination Methods**
   - Multiple methods to combine various strategies (majority vote, weighted average, unanimous)
   - Single strategy execution (e.g., quiver strategies that don't need combination)
   - Configurable filters and parameters

3. **Integration Points**
   - Plugs into backtesting systems
   - Connects to execution engines
   - Supports portfolio management integration

---

## Quick Start

```python
from composer import create_composer, get_signals
import pandas as pd

# Simple usage with convenience function
signals = get_signals('technical_ensemble', market_data_df)

# Or create a composer instance for more control
composer = create_composer()
signals = composer.execute_combination('technical_ensemble', market_data_df)
```

---

## Core Components

### 1. Configuration File (`config/strategies.yaml`)

The configuration file defines:
- **Individual strategies** with their parameters
- **Strategy combinations** with different methods
- **Global settings** for signal processing

```yaml
strategies:
  sma_crossover:
    class: SMACrossover
    parameters:
      fast: 20
      slow: 50
    enabled: true

combinations:
  technical_ensemble:
    strategies:
      - sma_crossover
      - rsi_reversion
    method: majority_vote
    filters:
      - atr_filter
```

### 2. Strategy Registration

The composer automatically discovers and initializes strategies:

```python
composer = StrategyComposer()
composer.register_strategies()  # Loads from config

# Access individual strategies
sma_strategy = composer.get_strategy('sma_crossover')
```

### 3. Strategy Combination Methods

#### Majority Vote
Combines signals based on majority agreement:
```yaml
method: majority_vote
```
- If more strategies signal BUY (1) than SELL (-1), output is BUY
- If more strategies signal SELL (-1) than BUY (1), output is SELL
- Otherwise, output is HOLD (0)

#### Weighted Average
Combines signals using configurable weights:
```yaml
method: weighted_average
weights:
  sma_crossover: 0.4
  rsi_reversion: 0.6
```
- Calculates weighted sum of all signals
- Applies threshold to convert to discrete signals
- Threshold configurable in global settings

#### Unanimous
Requires all strategies to agree:
```yaml
method: unanimous
```
- Output signal only when ALL strategies agree
- Very conservative approach
- Reduces false signals but may miss opportunities

#### Single Strategy
Executes individual strategies (like quiver strategies):
```yaml
method: single
strategies:
  - sentiment_llm
```

---

## Available Strategies

### Technical Indicators
- **SMACrossover**: Simple Moving Average crossover signals
- **RSIReversion**: RSI mean reversion signals  
- **MACDCross**: MACD line crossover signals
- **BollingerBounce**: Bollinger Band bounce signals

### Filters
- **ATRVolatilityFilter**: Filters signals based on volatility

### Alternative Data
- **SentimentLLMStrategy**: News sentiment-based signals

---

## Usage Examples

### Basic Combination Execution

```python
from composer import create_composer

# Initialize composer
composer = create_composer('config/strategies.yaml')

# Execute a specific combination
signals = composer.execute_combination('technical_ensemble', df)

# Analyze results
buy_signals = (signals == 1).sum()
sell_signals = (signals == -1).sum()
print(f"Generated {buy_signals} buy and {sell_signals} sell signals")
```

### Custom Configuration

```python
# Create custom config
custom_config = {
    'strategies': {
        'my_sma': {
            'class': 'SMACrossover',
            'parameters': {'fast': 10, 'slow': 30},
            'enabled': True
        }
    },
    'combinations': {
        'my_combo': {
            'strategies': ['my_sma'],
            'method': 'single'
        }
    }
}

# Save and use custom config
import yaml
with open('config/custom.yaml', 'w') as f:
    yaml.dump(custom_config, f)

composer = create_composer('config/custom.yaml')
```

### Working with Individual Strategies

```python
# Get individual strategy
rsi_strategy = composer.get_strategy('rsi_reversion')
rsi_signals = rsi_strategy.generate_signals(df)

# Apply filters separately
atr_filter = composer.get_filter('atr_filter')
filter_signals = atr_filter.generate_signals(df)
filtered_signals = rsi_signals * filter_signals
```

### Integration with Backtesting

```python
# Typical integration flow
def backtest_strategy(combination_name, data):
    """Example backtesting integration."""
    # Get signals from composer
    signals = get_signals(combination_name, data)
    
    # Your backtesting logic here
    portfolio_value = 100000
    positions = []
    
    for date, signal in signals.items():
        if signal == 1:  # Buy signal
            # Execute buy logic
            pass
        elif signal == -1:  # Sell signal
            # Execute sell logic
            pass
    
    return portfolio_value, positions

# Run backtest
final_value, trades = backtest_strategy('technical_ensemble', market_data)
```

---

## Data Requirements

### Required DataFrame Columns

Your market data DataFrame should include:

```python
# Basic OHLCV data
df = pd.DataFrame({
    'close': [...],    # Closing prices
    'high': [...],     # High prices  
    'low': [...],      # Low prices
    'volume': [...]    # Trading volume
})

# Technical indicators (add these columns)
df['sma_20'] = df['close'].rolling(20).mean()
df['sma_50'] = df['close'].rolling(50).mean()
df['rsi'] = calculate_rsi(df['close'])
df['macd'], df['macd_signal'] = calculate_macd(df['close'])
df['bb_upper'], df['bb_lower'] = calculate_bollinger_bands(df['close'])
df['atr'] = calculate_atr(df)
```

### For Sentiment Strategies

```python
# Add news data column
df['news_headline'] = [...]  # News headlines or summaries
```

---

## Advanced Features

### Dynamic Strategy Loading

```python
# List available strategies and combinations
print("Available strategies:", composer.list_available_strategies())
print("Available combinations:", composer.list_available_combinations())

# Get detailed combination info
combo_info = composer.get_combination_info('technical_ensemble')
print("Combination details:", combo_info)
```

### Error Handling

```python
try:
    signals = composer.execute_combination('my_combo', df)
except ValueError as e:
    print(f"Configuration error: {e}")
except KeyError as e:
    print(f"Missing data column: {e}")
```

### Performance Optimization

```python
# Reuse composer instance for multiple executions
composer = create_composer()

# Execute multiple combinations efficiently
for combo_name in ['technical_ensemble', 'sentiment_only']:
    signals = composer.execute_combination(combo_name, df)
    # Process signals...
```

---

## Integration Points

### With Backtesting Modules
```python
from composer import get_signals
from backtester import run_backtest

signals = get_signals('technical_ensemble', data)
results = run_backtest(signals, data, initial_capital=100000)
```

### With Execution Systems
```python
from composer import create_composer
from execution import place_order

composer = create_composer()
signals = composer.execute_combination('live_strategy', real_time_data)

for date, signal in signals.tail(1).items():  # Latest signal
    if signal != 0:
        place_order(signal, quantity=100)
```

### With Portfolio Management
```python
from composer import get_signals
from portfolio import PortfolioManager

pm = PortfolioManager()
signals = get_signals('diversified_combo', data)
pm.update_positions(signals)
```

---

## Best Practices

1. **Strategy Testing**: Test individual strategies before combining them
2. **Parameter Tuning**: Use backtesting to optimize strategy parameters
3. **Filter Usage**: Always consider using volatility or other filters
4. **Configuration Management**: Keep different configs for different market conditions
5. **Data Quality**: Ensure your data includes all required technical indicators
6. **Error Handling**: Implement proper error handling for production use

---

## Troubleshooting

### Common Issues

1. **Missing columns**: Ensure your DataFrame has all required technical indicators
2. **Configuration errors**: Validate YAML syntax and strategy names
3. **Strategy not found**: Check that strategy is enabled in configuration
4. **Import errors**: Ensure all strategy modules are properly imported

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

composer = create_composer()
# Now you'll see detailed logging
```

---

## Future Enhancements

- Integration with broker APIs (Alpaca, InteractiveBrokers)
- Real-time execution engine
- Web dashboard for strategy monitoring
- Machine learning model integration
- Advanced portfolio optimization

This composer module provides a flexible foundation for strategy combination and can be easily extended with new strategies, combination methods, and integration points.