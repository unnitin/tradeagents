# Configuration System

This directory contains configuration files and utilities for the trading system. The configuration system provides a flexible way to manage backtest parameters, strategy settings, and filter configurations through YAML files.

| File | Purpose |
| --- | --- |
| `backtest_config.py` | Loads/validates scenarios defined in `backtest.yaml`, exposes helpers such as `load_backtest_config`. |
| `filter_config.py` | Parses `filters.yaml`, builds filter objects for strategies or composer combinations. |
| `strategies.yaml` | Declares enabled strategies, parameters, and ensembles for the composer. |
| `backtest.yaml` | Houses preset risk profiles (default, conservative, aggressive, day_trading, etc.). |
| `filters.yaml` | Named filter bundles mapped to stock/time/liquidity settings. |

Every module—agents, strategies, composer, backtest—reads from this directory, ensuring the behaviour described in `spec.md` is driven by declarative configs rather than hardcoded values.

## Overview

The configuration system consists of:

- **`backtest_config.py`** - Backtest configuration management
- **`filter_config.py`** - Filter configuration management  
- **`backtest.yaml`** - Backtest parameter configurations
- **`strategies.yaml`** - Strategy configurations
- **`filters.yaml`** - Filter configurations
- **`__init__.py`** - Package exports

## Filter Configuration System

### Quick Start

```python
from config import load_filter_config, FilterConfigManager

# Load a preset configuration
config = load_filter_config("large_cap_conservative")

# Create a filter with the configuration
from filters import StockFilter
filter = StockFilter(
    min_volume=config.min_volume,
    min_price=config.min_price,
    max_price=config.max_price,
    # ... other parameters
)
```

### Available Filter Presets

#### Stock Market Configurations

| Configuration | Description | Use Case |
|---------------|-------------|----------|
| `default` | Balanced settings for general use | Standard backtesting |
| `large_cap_conservative` | High-volume, stable stocks | Conservative portfolios |
| `small_cap_aggressive` | Lower barriers, higher volatility | Growth strategies |
| `day_trading` | High-volume, tight spreads | Intraday trading |
| `etf_portfolio` | ETF-specific settings | Diversified ETF strategies |
| `crypto_etf` | Cryptocurrency-related stocks | Crypto exposure |
| `no_filter` | Minimal restrictions | Testing and development |

#### Configuration Details

**Large Cap Conservative**
```yaml
min_volume: 5,000,000    # High liquidity requirement
min_price: $20           # Avoid penny stocks
max_price: $500          # Reasonable upper bound
min_market_cap: $10B     # Large companies only
max_volatility: 2%       # Low volatility stocks
excludes: TSLA, GME, AMC # Volatile stocks excluded
```

**Day Trading**
```yaml
min_volume: 10,000,000   # Very high liquidity
min_dollar_volume: $100M # High dollar volume
max_bid_ask_spread: 0.05% # Tight spreads
trading_hours: 9:30-16:00 # Full market hours
```

**ETF Portfolio**
```yaml
symbols: [SPY, QQQ, VTI, IWM, ...] # Curated ETF list
max_volatility: 1.5%     # Low volatility
min_dollar_volume: $100M # High liquidity
tight_spreads: 0.01%     # Very tight spreads
```

### Filter Types

#### 1. Stock Filters
Control which stocks are included based on fundamental criteria:

```python
# Available parameters
min_volume: 1000000.0      # Minimum daily volume
min_price: 5.0             # Minimum stock price
max_price: null            # Maximum stock price
min_market_cap: null       # Minimum market cap
max_volatility: null       # Maximum volatility (ATR)
exclude_symbols: []        # Stocks to exclude
include_symbols: []        # Only include these stocks
```

#### 2. Time Filters
Control when trading occurs:

```python
# Available parameters
exclude_dates: []          # Specific dates to exclude
include_dates: []          # Only trade on these dates
start_time: "09:30"        # Trading start time
end_time: "16:00"          # Trading end time
exclude_earnings_periods: false
exclude_market_holidays: true
min_trading_days: 30       # Minimum data requirement
```

#### 3. Liquidity Filters
Focus on liquidity-specific metrics:

```python
# Available parameters
min_avg_volume: 1000000.0  # Average volume requirement
volume_window: 20          # Days for volume calculation
max_bid_ask_spread: null   # Maximum spread percentage
min_dollar_volume: null    # Minimum price × volume
```

### Using the Configuration Manager

#### Basic Usage

```python
from config.filter_config import FilterConfigManager

# Create manager
manager = FilterConfigManager()

# List available configurations
configs = manager.list_available_configs()
print(f"Available: {configs}")

# Load specific configuration
config = manager.get_stock_filter_config("large_cap_conservative")
```

#### Advanced Usage

```python
# Get different filter types
stock_config = manager.get_stock_filter_config("day_trading")
time_config = manager.get_time_filter_config("day_trading")
liquidity_config = manager.get_liquidity_filter_config("day_trading")

# Validate configurations
try:
    manager.validate_config("large_cap_conservative")
    print("✓ Configuration is valid")
except ValueError as e:
    print(f"✗ Invalid configuration: {e}")

# Get global settings
settings = manager.get_settings()
```

### Creating Custom Configurations

#### Method 1: Extend filters.yaml

Add your configuration to the `configurations` section:

```yaml
configurations:
  my_custom_config:
    stock_filter:
      min_volume: 2000000.0
      min_price: 10.0
      max_volatility: 0.025
      include_symbols: ["AAPL", "MSFT", "GOOGL"]
    
    time_filter:
      start_time: "10:00"
      end_time: "15:30"
      exclude_earnings_periods: true
      min_trading_days: 45
    
    liquidity_filter:
      min_avg_volume: 3000000.0
      volume_window: 30
      max_bid_ask_spread: 0.001
```

#### Method 2: Programmatic Creation

```python
from config.filter_config import FilterConfig

# Create custom configuration
custom_config = FilterConfig(
    min_volume=2000000.0,
    min_price=15.0,
    max_price=300.0,
    exclude_symbols=["TSLA", "GME"],
    include_symbols=["AAPL", "MSFT", "GOOGL", "AMZN"]
)

# Use with filters
from filters import StockFilter
filter = StockFilter(
    min_volume=custom_config.min_volume,
    min_price=custom_config.min_price,
    max_price=custom_config.max_price,
    exclude_symbols=custom_config.exclude_symbols,
    include_symbols=custom_config.include_symbols
)
```

### Filter Combinations

The system supports combining multiple filters with AND/OR logic:

```yaml
combinations:
  conservative_multi:
    filters:
      - large_cap_conservative
      - liquidity_strict
    logic: "AND"  # All filters must pass
    
  flexible_multi:
    filters:
      - small_cap_aggressive
      - day_trading
    logic: "OR"   # At least one filter must pass
```

### Validation Rules

All configurations are validated against predefined rules:

```yaml
validation:
  stock_filter:
    min_volume:
      min: 0.0
      max: 100000000.0
    min_price:
      min: 0.01
      max: 10000.0
    max_volatility:
      min: 0.001
      max: 1.0
```

### Configuration Examples

#### Conservative Long-Term Strategy
```python
# Use large cap conservative settings
config = load_filter_config("large_cap_conservative")
# Results in: High-quality, stable, liquid stocks
```

#### Aggressive Growth Strategy
```python
# Use small cap aggressive settings
config = load_filter_config("small_cap_aggressive")
# Results in: Higher volatility, growth-oriented stocks
```

#### Day Trading Setup
```python
# Use day trading settings
config = load_filter_config("day_trading")
# Results in: High-volume, tight-spread stocks for intraday
```

### Error Handling

The configuration system includes comprehensive error handling:

```python
try:
    config = load_filter_config("nonexistent_config")
except ValueError as e:
    print(f"Configuration error: {e}")
    # Handle gracefully with fallback

try:
    manager.validate_config("my_config")
except ValueError as e:
    print(f"Validation failed: {e}")
    # Fix configuration issues
```

### Best Practices

1. **Start with Presets**: Use existing configurations as starting points
2. **Validate Early**: Always validate configurations before use
3. **Document Custom Configs**: Add comments to custom configurations
4. **Test Thoroughly**: Validate configurations with sample data
5. **Use Appropriate Presets**: Match configurations to your strategy type

### Migration Guide

#### From Hard-coded Filters

**Before:**
```python
# Hard-coded in strategy
filter = StockFilter(
    min_volume=1000000.0,
    min_price=5.0,
    exclude_symbols=["TSLA"]
)
```

**After:**
```python
# Configuration-driven
config = load_filter_config("large_cap_conservative")
filter = StockFilter(
    min_volume=config.min_volume,
    min_price=config.min_price,
    exclude_symbols=config.exclude_symbols
)
```

#### From Manual Configuration

**Before:**
```python
# Manual parameter management
min_vol = 1000000 if strategy_type == "conservative" else 500000
min_price = 20 if strategy_type == "conservative" else 1
```

**After:**
```python
# Configuration-based
config_name = "large_cap_conservative" if strategy_type == "conservative" else "small_cap_aggressive"
config = load_filter_config(config_name)
```

### Integration with Backtesting

The filter configuration system integrates seamlessly with the backtesting framework:

```python
from config import load_filter_config
from filters import StockFilter, CompositeFilter
from backtest.engine import BacktestEngine

# Load configuration
config = load_filter_config("large_cap_conservative")

# Create filters
stock_filter = StockFilter(
    min_volume=config.min_volume,
    min_price=config.min_price,
    max_price=config.max_price,
    exclude_symbols=config.exclude_symbols
)

# Use in backtest
engine = BacktestEngine(filters=[stock_filter])
```

## File Structure

```
config/
├── README.md              # This file
├── __init__.py            # Package exports
├── backtest_config.py     # Backtest configuration
├── filter_config.py       # Filter configuration
├── backtest.yaml          # Backtest parameters
├── strategies.yaml        # Strategy configurations
└── filters.yaml           # Filter configurations
```

## See Also

- **`examples/filter_config_example.py`** - Comprehensive usage examples
- **`examples/backtest_example.py`** - Integration with backtesting
- **`filters/core.py`** - Filter implementations
- **`strategies/`** - Strategy implementations using configurations 
