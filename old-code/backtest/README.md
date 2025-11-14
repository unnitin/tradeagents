# Backtest Module

## Overview

The backtest module provides comprehensive backtesting functionality for evaluating trading strategy performance against defined parameters. It serves as a robust testing framework that validates strategy effectiveness within specific constraints and conditions.

| File | Responsibility |
| --- | --- |
| `engine.py` | `BacktestEngine` orchestration, runs single strategies or composer combinations, handles filters and transaction costs. |
| `portfolio.py` | Positions, executions, and portfolio equity curve tracking. |
| `metrics.py` | Computes returns, risk, Sharpe/Sortino, drawdown, VaR, trade stats, and benchmark comparisons. |
| `results.py` | Serialization helpers plus comparison utilities for multiple runs. |
| `__init__.py` | Convenience exports (e.g., `create_backtest_engine`). |

The engine is designed to plug directly into the agents module: `AgentOutput.signals` feeds into the backtest for evaluation, and backtest metrics can be fed back as agent metadata for the learning loop described in `spec.md`.

## Objectives

The primary objectives of this module align with the original requirements:

1. **Strategy Performance Verification**: Test strategies against defined parameters and time periods
2. **Parameter-Bound Results**: Ensure results are tied to specific test parameters (time duration, stock pools, filters)
3. **Configurable Testing Environment**: Support various filtering criteria including liquidity, volume, and custom attributes
4. **Comprehensive Performance Metrics**: Calculate expected return, variance, Sharpe ratio, drawdown, and other key metrics
5. **Results Storage and Analysis**: Maintain detailed records of backtest results with comparison capabilities

## Architecture

The backtest module follows a modular architecture with clear separation of concerns:

```
backtest/
├── __init__.py          # Module exports and convenience functions
├── engine.py            # Core BacktestEngine and simulation logic
├── portfolio.py         # Portfolio management and trade execution
├── metrics.py           # Performance metrics calculation
├── filters.py           # Stock and time filtering functionality
├── results.py           # Results storage and analysis
└── README.md           # This documentation
```

## Configuration System

The backtest module uses a centralized YAML-based configuration system located in the `config` module. This provides:

- **Predefined Scenarios**: Multiple ready-to-use configurations (conservative, aggressive, day_trading, etc.)
- **Custom Configuration**: Easy parameter customization with validation
- **Centralized Management**: All configuration parameters in one place
- **Validation**: Automatic parameter validation and error checking

### Available Configurations

- **default**: Balanced configuration suitable for most use cases
- **conservative**: Low-risk configuration with tight constraints
- **aggressive**: High-risk configuration allowing larger positions
- **day_trading**: Optimized for intraday trading strategies
- **etf_portfolio**: Low-cost configuration for ETF strategies

## Core Components

### 1. BacktestEngine (`engine.py`)

The main orchestration component that manages the entire backtesting process:

```python
from backtest import create_backtest_engine
from config import BacktestConfig, load_backtest_config
from strategies import SMACrossover

# Option 1: Use predefined configuration
config = load_backtest_config("conservative")
engine = create_backtest_engine(config)

# Option 2: Create custom configuration
config = BacktestConfig(
    initial_capital=100000.0,
    commission_rate=0.001,
    max_position_size=0.1
)
engine = create_backtest_engine(config)

# Run backtest
strategy = SMACrossover(fast=20, slow=50)
results = engine.run_backtest(
    strategy=strategy,
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

### 2. Portfolio Management (`portfolio.py`)

Handles position tracking, trade execution, and portfolio valuation:

- **Position Tracking**: Maintains current positions with average price and P&L
- **Trade Execution**: Executes buy/sell orders with commission and slippage costs
- **Portfolio Valuation**: Real-time portfolio value calculation and history tracking

### 3. Performance Metrics (`metrics.py`)

Calculates comprehensive performance metrics:

- **Return Metrics**: Total return, annualized return, volatility
- **Risk-Adjusted Metrics**: Sharpe ratio, Sortino ratio, Calmar ratio
- **Risk Metrics**: Maximum drawdown, VaR, beta
- **Trade Metrics**: Win rate, profit factor, trade analysis
- **Benchmark Comparison**: Alpha, tracking error, information ratio

### 4. Filtering System (`filters.py`)

Provides configurable filtering for stocks and time periods:

```python
from filters import StockFilter, TimeFilter, CompositeFilter

# Stock filtering
stock_filter = StockFilter(
    min_volume=1000000,      # Minimum daily volume
    min_price=10.0,          # Minimum stock price
    max_volatility=0.5,      # Maximum volatility threshold
    exclude_symbols=["TSLA"] # Exclude specific symbols
)

# Time filtering
time_filter = TimeFilter(
    exclude_market_holidays=True,
    min_trading_days=100,
    start_time="09:30",      # Market open
    end_time="16:00"         # Market close
)

# Composite filtering (AND/OR logic)
composite_filter = CompositeFilter([stock_filter, time_filter], logic="AND")
```

### 5. Results Management (`results.py`)

Comprehensive results storage and analysis:

```python
from backtest import save_results, load_results, compare_multiple_results

# Save results in multiple formats
save_results(results, "backtest_results.pkl", format="pickle")
save_results(results, "backtest_results.xlsx", format="excel")

# Load and analyze results
loaded_results = load_results("backtest_results.pkl")
performance_summary = loaded_results.get_performance_summary()
trade_analysis = loaded_results.get_trade_analysis()

# Compare multiple strategies
comparison_df = compare_multiple_results([results1, results2, results3])
```

## Configuration Management

### Loading Configurations

```python
from config import BacktestConfigManager, load_backtest_config

# Method 1: Direct loading
config = load_backtest_config("aggressive")

# Method 2: Using config manager
manager = BacktestConfigManager()
config = manager.get_config("conservative")

# List available configurations
available_configs = manager.list_available_configs()
print(f"Available: {available_configs}")
```

### Custom Configuration Creation

```python
from config import BacktestConfigManager

manager = BacktestConfigManager()

# Create custom config based on existing one
custom_config = manager.create_custom_config(
    base_config="aggressive",
    initial_capital=500000.0,
    commission_rate=0.0001,
    max_position_size=0.3
)

# Validate configuration
manager.validate_config(custom_config)
```

### Configuration Parameters

The YAML configuration file (`config/backtest.yaml`) includes:

- **Capital Management**: Initial capital, position sizing
- **Transaction Costs**: Commission rates, slippage modeling
- **Risk Management**: Drawdown limits, daily loss limits
- **Benchmarking**: Risk-free rate, benchmark symbols
- **Rebalancing**: Frequency and thresholds
- **Validation Rules**: Parameter constraints and limits

## Parameter Types

The module supports various parameter types as specified in the requirements:

### 1. Time Duration Parameters
- **Start/End Dates**: Define the testing period
- **Trading Sessions**: Filter by time of day for intraday strategies
- **Market Holidays**: Exclude non-trading days
- **Minimum Trading Days**: Ensure sufficient data points

### 2. Stock Selection Parameters
- **Volume Filters**: Minimum/maximum trading volume thresholds
- **Price Filters**: Stock price range constraints
- **Liquidity Measures**: Average volume, dollar volume, bid-ask spreads
- **Volatility Filters**: ATR-based or custom volatility measures
- **Include/Exclude Lists**: Explicit symbol filtering
- **Market Cap Filters**: Size-based stock selection

### 3. Configuration Parameters
- **Capital Management**: Initial capital, position sizing methods
- **Transaction Costs**: Commission rates, slippage modeling
- **Risk Management**: Stop loss, take profit, maximum drawdown limits
- **Rebalancing**: Frequency and methodology

## Output Metrics

The backtest module provides comprehensive performance metrics as required:

### 1. Return Metrics
- **Expected Return**: Mean return over the testing period
- **Total Return**: Cumulative return from start to end
- **Annualized Return**: Geometric mean return annualized
- **Rolling Returns**: Time-series analysis of performance

### 2. Risk Metrics
- **Variance/Volatility**: Standard deviation of returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Value at Risk**: Potential loss at confidence levels
- **Beta**: Systematic risk relative to benchmark

### 3. Risk-Adjusted Metrics
- **Sharpe Ratio**: Return per unit of total risk
- **Sortino Ratio**: Return per unit of downside risk
- **Calmar Ratio**: Return per unit of maximum drawdown
- **Information Ratio**: Active return per unit of tracking error

### 4. Trade-Specific Metrics
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Average Win/Loss**: Mean profit and loss per trade
- **Trade Frequency**: Number of trades relative to time period

## Usage Examples

### Basic Backtest
```python
from backtest import create_backtest_engine
from config import load_backtest_config
from strategies import RSIReversion

# Simple backtest with predefined configuration
config = load_backtest_config("default")
engine = create_backtest_engine(config)
strategy = RSIReversion(rsi_col="rsi_14", low_thresh=30, high_thresh=70)

results = engine.run_backtest(
    strategy=strategy,
    symbols="AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

print(f"Total Return: {results.metrics.total_return:.2%}")
print(f"Sharpe Ratio: {results.metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.metrics.max_drawdown:.2%}")
```

### Advanced Backtest with Filtering
```python
from backtest import create_backtest_engine
from filters import StockFilter, TimeFilter
from config import load_backtest_config
from strategies import SMACrossover

# Load aggressive configuration
config = load_backtest_config("aggressive")
engine = create_backtest_engine(config)

# Create comprehensive filters
stock_filter = StockFilter(
    min_volume=2000000,        # High volume stocks only
    min_price=20.0,            # Avoid penny stocks
    max_volatility=0.3,        # Limit volatility
    exclude_symbols=["SPCE"]   # Exclude volatile stocks
)

time_filter = TimeFilter(
    exclude_market_holidays=True,
    min_trading_days=200,      # Ensure sufficient data
    start_time="10:00",        # Skip opening volatility
    end_time="15:30"          # Skip closing rush
)

strategy = SMACrossover(fast=10, slow=30)
results = engine.run_backtest(
    strategy=strategy,
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    start_date="2022-01-01",
    end_date="2023-12-31",
    stock_filter=stock_filter,
    time_filter=time_filter
)

# Parameter-bound result interpretation
print(f"Strategy: {strategy.__class__.__name__}")
print(f"Parameters: fast={strategy.fast}, slow={strategy.slow}")
print(f"Time Period: {results.start_date} to {results.end_date}")
print(f"Stocks: {len(results.symbols)} symbols")
print(f"Filters Applied: Volume≥2M, Price≥$20, Volatility≤30%")
print(f"Performance: {results.metrics.total_return:.2%} return")
print(f"Risk: {results.metrics.max_drawdown:.2%} max drawdown")
```

### Multi-Strategy Comparison
```python
from backtest import create_backtest_engine, compare_multiple_results
from config import load_backtest_config
from strategies import SMACrossover, RSIReversion, MACDCross

# Use conservative configuration for comparison
config = load_backtest_config("conservative")
engine = create_backtest_engine(config)

# Test multiple strategies
strategies = [
    SMACrossover(fast=20, slow=50),
    RSIReversion(rsi_col="rsi_14", low_thresh=30, high_thresh=70),
    MACDCross()
]

results = []
for strategy in strategies:
    result = engine.run_backtest(
        strategy=strategy,
        symbols=["AAPL", "MSFT", "GOOGL"],
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    results.append(result)

# Compare results
comparison_df = compare_multiple_results(results)
print("Strategy Performance Comparison:")
print(comparison_df.to_string())
```

### Configuration Sensitivity Analysis
```python
from backtest import create_backtest_engine
from config import BacktestConfigManager
from strategies import SMACrossover

manager = BacktestConfigManager()
strategy = SMACrossover(fast=20, slow=50)

# Test different commission rates
commission_rates = [0.0001, 0.0005, 0.001, 0.002]
results = []

for rate in commission_rates:
    config = manager.create_custom_config(
        base_config="default",
        commission_rate=rate
    )
    engine = create_backtest_engine(config)
    
    result = engine.run_backtest(
        strategy=strategy,
        symbols="AAPL",
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    results.append((rate, result))

# Analyze commission impact
print("Commission Rate Impact Analysis:")
for rate, result in results:
    print(f"Rate {rate:.4f}: {result.metrics.total_return:.2%} return")
```

## Composer Integration

The backtest module seamlessly integrates with the composer module for testing strategy combinations:

```python
from backtest import create_backtest_engine
from config import load_backtest_config

# Load configuration
config = load_backtest_config("default")
engine = create_backtest_engine(config)

# Test strategy combination
results = engine.run_composer_backtest(
    strategy_names=["sma_crossover", "rsi_reversion", "macd_cross"],
    combination_method="majority_vote",
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)

print(f"Combined Strategy Return: {results.metrics.total_return:.2%}")
print(f"Individual vs Combined Performance Available")
```

## Performance Optimization

The backtest module includes several performance optimization features:

1. **Vectorized Operations**: NumPy and Pandas operations for speed
2. **Efficient Memory Usage**: Optimized data structures
3. **Parallel Processing**: Multi-symbol backtests in parallel
4. **Caching**: Cached indicator calculations
5. **Lazy Loading**: Data loaded only when needed

## Error Handling and Validation

Comprehensive error handling and validation:

1. **Parameter Validation**: Automatic validation of all configuration parameters
2. **Data Quality Checks**: Validation of input data quality
3. **Strategy Validation**: Ensures strategy compatibility
4. **Graceful Degradation**: Continues operation with warnings where possible
5. **Detailed Error Messages**: Clear error reporting for debugging

## Integration Points

The backtest module integrates with other system components:

- **Strategies Module**: Uses registered strategies for testing
- **Data Module**: Fetches and preprocesses market data
- **Composer Module**: Tests strategy combinations
- **Utils Module**: Leverages shared utilities and constants

## Parameter-Bound Results

A key feature of the backtest module is that all results are explicitly tied to the parameters used in testing:

```python
# Results contain full parameter context
print(f"Configuration: {results.config}")
print(f"Strategy Parameters: {results.strategy_params}")
print(f"Time Period: {results.start_date} to {results.end_date}")
print(f"Symbols: {results.symbols}")
print(f"Filters Applied: {results.filters}")
print(f"Data Quality: {results.data_info}")
```

This ensures that performance metrics are always interpreted within the context of the specific testing parameters, maintaining the integrity of the backtesting process.

## Best Practices

1. **Use Appropriate Configurations**: Choose configurations that match your use case
2. **Validate Parameters**: Always validate configuration parameters
3. **Apply Filters**: Use appropriate filters to ensure data quality
4. **Monitor Performance**: Track both returns and risk metrics
5. **Document Tests**: Save detailed results for future reference
6. **Compare Strategies**: Use multiple strategies for robust analysis
7. **Understand Limitations**: Be aware of survivorship bias and other limitations

## Future Enhancements

Planned enhancements include:

1. **Walk-Forward Analysis**: Rolling window backtesting
2. **Monte Carlo Simulation**: Stress testing capabilities
3. **Advanced Risk Models**: Integration with risk management systems
4. **Real-time Backtesting**: Live strategy validation
5. **Enhanced Reporting**: More comprehensive performance reports
