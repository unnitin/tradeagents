# Strategy Composer Module

The composer module provides intelligent strategy combination and orchestration capabilities for algorithmic trading. It enables you to combine multiple strategies using various logic approaches and test them comprehensively with the backtest module.

## ✅ **Implemented Features**

### 🎼 **Strategy Combination Methods**
- **Majority Vote**: Combines signals where majority consensus determines the action
- **Weighted Average**: Uses weighted averages of strategy signals with configurable weights
- **Unanimous**: Requires all strategies to agree before taking action (conservative approach)

### 🔧 **Configuration Management**
- **YAML-based Configuration**: Load strategy combinations from `config/strategies.yaml`
- **Dynamic Registration**: Automatically register and access strategies from the strategies module
- **Flexible Weighting**: Configure strategy weights and combination logic

### 🚀 **Backtest Integration**
- **Comprehensive Testing**: Test strategy combinations with the backtest module
- **Performance Analysis**: Get detailed metrics for ensemble strategies
- **Comparison Tools**: Compare individual vs combined strategy performance

---

## 🧪 **Quick Start Examples**

### **Basic Strategy Combination**
```python
from composer import StrategyComposer
from strategies import SMACrossover, RSIReversion, MACDCross

# Initialize composer
composer = StrategyComposer()

# Add strategies
composer.add_strategy(SMACrossover(fast=20, slow=50), weight=0.4)
composer.add_strategy(RSIReversion(low_thresh=30, high_thresh=70), weight=0.3)
composer.add_strategy(MACDCross(), weight=0.3)

# Generate combined signals
import pandas as pd
# ... assuming you have market data in 'data' DataFrame
signals = composer.generate_signals(data, method='weighted_average')
```

### **Configuration-Based Composition**
```python
# Load from YAML configuration
composer = create_composer("config/strategies.yaml")

# The configuration automatically sets up strategies and weights
signals = composer.generate_signals(data, method='majority_vote')
```

### **Backtest Integration**
```python
# Test strategy combination with backtesting
from backtest import create_backtest_engine

engine = create_backtest_engine()

# Test composer-based strategy
results = engine.run_composer_backtest(
    combination_name="technical_ensemble",
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# Analyze ensemble performance
print(f"Ensemble Return: {results.metrics.total_return:.2%}")
print(f"Ensemble Sharpe: {results.metrics.sharpe_ratio:.2f}")
print(f"Win Rate: {results.metrics.win_rate:.2%}")
```

---

## 📊 **Combination Methods**

### 1. **Majority Vote**
- **Logic**: Takes the action that the majority of strategies agree on
- **Use Case**: Democratic decision-making, reduces false signals
- **Example**: If 3 strategies say "buy" and 2 say "hold", result is "buy"

```python
signals = composer.generate_signals(data, method='majority_vote')
```

### 2. **Weighted Average**
- **Logic**: Combines signals using weighted averages based on strategy importance
- **Use Case**: When you want to give more weight to certain strategies
- **Example**: RSI (weight=0.5) + MACD (weight=0.3) + SMA (weight=0.2)

```python
signals = composer.generate_signals(data, method='weighted_average')
```

### 3. **Unanimous**
- **Logic**: Only takes action when ALL strategies agree
- **Use Case**: Conservative approach, reduces trade frequency but increases confidence
- **Example**: Only buy when RSI, MACD, and SMA all signal "buy"

```python
signals = composer.generate_signals(data, method='unanimous')
```

---

## ⚙️ **Configuration System**

### **YAML Configuration Example**
```yaml
# config/strategies.yaml
strategies:
  technical_ensemble:
    description: "Combination of technical indicators"
    strategies:
      - name: "SMACrossover"
        params:
          fast: 20
          slow: 50
        weight: 0.4
      - name: "RSIReversion"
        params:
          low_thresh: 30
          high_thresh: 70
        weight: 0.3
      - name: "MACDCross"
        params:
          fast: 12
          slow: 26
          signal: 9
        weight: 0.3
    combination_method: "weighted_average"
    
  conservative_ensemble:
    description: "Conservative unanimous approach"
    strategies:
      - name: "RSIReversion"
        params:
          low_thresh: 25
          high_thresh: 75
        weight: 1.0
      - name: "BollingerBounce"
        params:
          bb_window: 20
        weight: 1.0
    combination_method: "unanimous"
```

### **Loading Configuration**
```python
from composer import create_composer

# Load specific configuration
composer = create_composer("config/strategies.yaml")

# Access specific ensemble
technical_composer = composer.get_ensemble("technical_ensemble")
conservative_composer = composer.get_ensemble("conservative_ensemble")
```

---

## 🎯 **Advanced Usage**

### **Dynamic Strategy Registration**
```python
# Register strategies dynamically
composer = StrategyComposer()

# Add strategies with custom configurations
composer.add_strategy(
    SMACrossover(fast=10, slow=30), 
    weight=0.5, 
    name="fast_sma"
)

composer.add_strategy(
    RSIReversion(low_thresh=20, high_thresh=80), 
    weight=0.3, 
    name="aggressive_rsi"
)

# Remove or modify strategies
composer.remove_strategy("fast_sma")
composer.update_weight("aggressive_rsi", 0.5)
```

### **Performance Comparison**
```python
# Compare different combination methods
methods = ['majority_vote', 'weighted_average', 'unanimous']
results = {}

for method in methods:
    result = engine.run_composer_backtest(
        combination_name="technical_ensemble",
        symbols=["AAPL", "MSFT"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        combination_method=method
    )
    results[method] = result

# Compare performance
for method, result in results.items():
    print(f"{method}: {result.metrics.total_return:.2%} return, "
          f"{result.metrics.sharpe_ratio:.2f} Sharpe")
```

### **Multi-Strategy Analysis**
```python
# Run multiple ensemble backtests
ensemble_names = ["technical_ensemble", "conservative_ensemble", "aggressive_ensemble"]
comparison_results = engine.run_multiple_composer_backtests(
    ensemble_names=ensemble_names,
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# Analyze best performing ensemble
best_ensemble = max(comparison_results.items(), 
                   key=lambda x: x[1].metrics.total_return)
print(f"Best Ensemble: {best_ensemble[0]} with {best_ensemble[1].metrics.total_return:.2%} return")
```

---

## 🔧 **Implementation Flow**

### **Data Pipeline**
```
Market Data → Individual Strategies → Signal Generation → Composer → Combined Signals → Backtest → Performance Analysis
```

### **Strategy Integration**
1. **Strategy Registration**: Add strategies to composer with weights
2. **Configuration Loading**: Load from YAML or set programmatically
3. **Signal Generation**: Generate individual strategy signals
4. **Signal Combination**: Apply combination method (majority, weighted, unanimous)
5. **Backtesting**: Test combined strategy performance
6. **Analysis**: Evaluate metrics and compare approaches

---

## 🧪 **Testing and Examples**

### **Run Composer Tests**
```bash
# Test composer functionality
python -m pytest tests/unit_test/test_composer.py -v

# Test composer-backtest integration
python tests/test_backtest_runner.py

# Run composer examples
python examples/strategy_composer_example.py
python examples/composer_backtest_example.py
```

### **Complete Example**
```python
# Complete workflow example
from composer import create_composer
from backtest import create_backtest_engine
from filters import StockFilter, TimeFilter

# 1. Create composer from config
composer = create_composer("config/strategies.yaml")

# 2. Create backtest engine
engine = create_backtest_engine()

# 3. Add filters
stock_filter = StockFilter(min_volume=1000000, min_price=20)
time_filter = TimeFilter(exclude_earnings_periods=True)

# 4. Run comprehensive backtest
results = engine.run_composer_backtest(
    combination_name="technical_ensemble",
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    stock_filter=stock_filter,
    time_filter=time_filter
)

# 5. Analyze results
print(f"Strategy: {results.strategy_name}")
print(f"Total Return: {results.metrics.total_return:.2%}")
print(f"Sharpe Ratio: {results.metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.metrics.max_drawdown:.2%}")
print(f"Win Rate: {results.metrics.win_rate:.2%}")
print(f"Total Trades: {results.metrics.total_trades}")
```

---

## 📚 **API Reference**

### **StrategyComposer Class**
- `add_strategy(strategy, weight, name=None)`: Add strategy to composer
- `remove_strategy(name)`: Remove strategy from composer
- `update_weight(name, weight)`: Update strategy weight
- `generate_signals(data, method='weighted_average')`: Generate combined signals
- `get_strategy_info()`: Get information about registered strategies

### **Utility Functions**
- `create_composer(config_path)`: Create composer from YAML configuration
- `load_strategy_config(config_path)`: Load strategy configurations
- `register_strategies(strategy_list)`: Register multiple strategies at once

---

## 🎯 **Best Practices**

1. **Weight Distribution**: Ensure weights sum to 1.0 for weighted_average method
2. **Strategy Diversity**: Combine strategies with different approaches (trend, mean-reversion, sentiment)
3. **Parameter Optimization**: Use backtesting to find optimal strategy parameters
4. **Risk Management**: Use unanimous method for conservative approach
5. **Performance Monitoring**: Regularly compare individual vs ensemble performance

---

**The composer module enables intelligent strategy orchestration with comprehensive backtesting capabilities for robust algorithmic trading systems.**