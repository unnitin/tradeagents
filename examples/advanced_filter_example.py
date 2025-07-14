#!/usr/bin/env python3
"""
Advanced Filter Demo - Demonstrates Enhanced Strategy Base Class

This example shows how ALL strategy classes now inherit advanced filter functionality
from the base Strategy class, including:
- Basic filters (volume, price, liquidity)
- Symbol-specific filters (different rules per stock)
- Dynamic filters (market condition-based)
- Configuration-based filtering
- Filter validation and analytics

All strategies (SMACrossover, RSIReversion, MACDCross, etc.) now have these capabilities.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import strategies - all now have advanced filter capabilities
from strategies import SMACrossover, RSIReversion, MACDCross
from filters import StockFilter, TimeFilter, LiquidityFilter, CompositeFilter


def create_sample_data() -> pd.DataFrame:
    """Create sample market data for demonstration with technical indicators."""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # Create sample data for multiple symbols
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY']
    data = []
    
    for symbol in symbols:
        # Generate realistic price data
        initial_price = np.random.uniform(100, 300)
        price_returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [initial_price]
        
        for ret in price_returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Generate volume data
        base_volume = np.random.uniform(1000000, 10000000)
        volumes = np.random.normal(base_volume, base_volume * 0.3, len(dates))
        volumes = np.abs(volumes)  # Ensure positive
        
        symbol_data = pd.DataFrame({
            'date': dates,
            'symbol': symbol,
            'open': prices,
            'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
            'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
            'close': prices,
            'volume': volumes
        })
        
        # Add technical indicators required by strategies
        symbol_data['sma_5'] = symbol_data['close'].rolling(5).mean()
        symbol_data['sma_10'] = symbol_data['close'].rolling(10).mean()
        symbol_data['sma_15'] = symbol_data['close'].rolling(15).mean()
        symbol_data['sma_20'] = symbol_data['close'].rolling(20).mean()
        symbol_data['sma_50'] = symbol_data['close'].rolling(50).mean()
        
        # Add RSI
        delta = symbol_data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        symbol_data['rsi_14'] = 100 - (100 / (1 + rs))
        
        # Add MACD
        exp1 = symbol_data['close'].ewm(span=12).mean()
        exp2 = symbol_data['close'].ewm(span=26).mean()
        symbol_data['macd'] = exp1 - exp2
        symbol_data['macd_signal'] = symbol_data['macd'].ewm(span=9).mean()
        
        data.append(symbol_data)
    
    return pd.concat(data, ignore_index=True)


def demonstrate_basic_filtering():
    """Demonstrate basic filtering capabilities available to all strategies."""
    print("=" * 60)
    print("BASIC FILTERING - Available to ALL Strategy Classes")
    print("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    print(f"Original data: {len(df)} rows")
    
    # Initialize any strategy - they all have filter capabilities now
    strategy = SMACrossover(fast=10, slow=20)
    
    # Create basic filters
    volume_filter = StockFilter(min_volume=2000000)
    price_filter = StockFilter(min_price=150, max_price=250)
    
    # Set filters with AND logic
    strategy.set_filters([volume_filter, price_filter], logic="AND")
    
    # Apply filters and generate signals
    signals = strategy.generate_signals_with_filters(df)
    
    print(f"After filtering: {len(signals[signals != 0])} signals generated")
    print(f"Filter info: {strategy.get_filter_info()}")
    
    return strategy, df


def demonstrate_symbol_specific_filtering():
    """Demonstrate symbol-specific filtering - different rules per stock."""
    print("\n" + "=" * 60)
    print("SYMBOL-SPECIFIC FILTERING - Different Rules Per Stock")
    print("=" * 60)
    
    # Use any strategy - RSIReversion in this case
    strategy = RSIReversion(rsi_col="rsi_14", low_thresh=30, high_thresh=70)
    
    # Create different filters for different symbols
    symbol_filters = {
        'AAPL': [StockFilter(min_volume=5000000)],  # High volume for AAPL
        'GOOGL': [StockFilter(min_price=200)],      # High price for GOOGL
        'TSLA': [StockFilter(max_price=200)],       # Cap price for TSLA
        'SPY': [StockFilter(min_volume=1000000)]    # Lower volume for SPY
    }
    
    # Set symbol-specific filters
    strategy.set_symbol_filters(symbol_filters)
    
    # Create sample data
    df = create_sample_data()
    
    # Generate signals with symbol-specific filtering
    signals = strategy.generate_signals_with_advanced_filters(df)
    
    print(f"Symbol-specific signals generated: {len(signals[signals != 0])}")
    print("Symbol filter configuration:")
    for symbol, filters in symbol_filters.items():
        print(f"  {symbol}: {len(filters)} filters")
    
    return strategy


def demonstrate_dynamic_filtering():
    """Demonstrate dynamic filtering based on market conditions."""
    print("\n" + "=" * 60)
    print("DYNAMIC FILTERING - Market Condition Adaptive")
    print("=" * 60)
    
    # Use MACDCross strategy
    strategy = MACDCross(macd_col="macd", signal_col="macd_signal")
    
    # Create dynamic filters that could change based on market conditions
    # (In real implementation, these would adapt to VIX, market regime, etc.)
    high_volatility_filter = StockFilter(min_volume=3000000)  # Higher volume during volatility
    earnings_season_filter = TimeFilter(exclude_earnings_periods=True)
    
    # Set dynamic filters
    strategy.set_dynamic_filters([high_volatility_filter, earnings_season_filter])
    
    # Create sample data
    df = create_sample_data()
    
    # Generate signals with dynamic filtering
    signals = strategy.generate_signals_with_advanced_filters(df)
    
    print(f"Dynamic filtering signals: {len(signals[signals != 0])}")
    print(f"Dynamic filters count: {len(strategy.dynamic_filters)}")
    
    return strategy


def demonstrate_config_based_filtering():
    """Demonstrate configuration-based filtering from YAML."""
    print("\n" + "=" * 60)
    print("CONFIGURATION-BASED FILTERING - YAML Driven")
    print("=" * 60)
    
    # Use any strategy - all support config-based filtering
    strategy = SMACrossover(fast=5, slow=15)
    
    # Create filter configuration (normally loaded from YAML)
    filter_config = {
        'stock_filter': {
            'min_volume': 1500000,
            'min_price': 50,
            'max_price': 500,
            'exclude_symbols': ['PENNY_STOCK']
        },
        'time_filter': {
            'exclude_earnings_periods': True,
            'exclude_market_holidays': True,
            'min_trading_days': 20
        },
        'liquidity_filter': {
            'min_avg_volume': 1000000,
            'volume_window': 20
        },
        'logic': 'AND'
    }
    
    # Configure filters from config
    strategy.configure_filters_from_config(filter_config)
    
    # Create sample data
    df = create_sample_data()
    
    # Generate signals with config-based filtering
    signals = strategy.generate_signals_with_filters(df)
    
    print(f"Config-based signals: {len(signals[signals != 0])}")
    print("Loaded filter configuration:")
    for key, value in filter_config.items():
        if isinstance(value, dict):
            print(f"  {key}: {len(value)} parameters")
        else:
            print(f"  {key}: {value}")
    
    return strategy


def demonstrate_filter_validation_and_analytics():
    """Demonstrate filter validation and comprehensive analytics."""
    print("\n" + "=" * 60)
    print("FILTER VALIDATION AND ANALYTICS")
    print("=" * 60)
    
    # Create a custom strategy with filter requirements
    class CustomStrategy(SMACrossover):
        def get_filter_requirements(self) -> Dict[str, Any]:
            return {
                "required": ["StockFilter"],
                "optional": ["TimeFilter", "LiquidityFilter"]
            }
    
    strategy = CustomStrategy(fast=10, slow=30)
    
    # Add required filter
    strategy.add_filter(StockFilter(min_volume=1000000))
    
    # Validate filters
    is_valid = strategy.validate_filters()
    print(f"Filter validation passed: {is_valid}")
    
    # Add symbol-specific and dynamic filters for comprehensive demo
    strategy.set_symbol_filters({
        'AAPL': [StockFilter(min_volume=2000000)],
        'GOOGL': [StockFilter(min_price=100)]
    })
    
    strategy.set_dynamic_filters([TimeFilter(exclude_market_holidays=True)])
    
    # Get comprehensive analytics
    analytics = strategy.get_advanced_filter_info()
    
    print("\nComprehensive Filter Analytics:")
    print(f"Base filters: {analytics['base_filters']['filter_count']}")
    print(f"Symbol-specific filters: {len(analytics['symbol_filters'])} symbols")
    print(f"Dynamic filters: {len(analytics['dynamic_filters'])}")
    
    return strategy


def demonstrate_multi_strategy_filtering():
    """Show how multiple strategies can use different filtering approaches."""
    print("\n" + "=" * 60)
    print("MULTI-STRATEGY FILTERING COMPARISON")
    print("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Strategy 1: Conservative filtering
    conservative_strategy = SMACrossover(fast=20, slow=50)
    conservative_strategy.set_filters([
        StockFilter(min_volume=5000000, min_price=100),
        LiquidityFilter(min_avg_volume=3000000)
    ])
    
    # Strategy 2: Aggressive filtering
    aggressive_strategy = RSIReversion(rsi_col="rsi_14", low_thresh=20, high_thresh=80)
    aggressive_strategy.set_filters([
        StockFilter(min_volume=1000000, min_price=10)
    ])
    
    # Strategy 3: Symbol-specific approach
    symbol_strategy = MACDCross()
    symbol_strategy.set_symbol_filters({
        'AAPL': [StockFilter(min_volume=10000000)],
        'TSLA': [StockFilter(min_volume=5000000)],
        'SPY': [StockFilter(min_volume=1000000)]
    })
    
    strategies = [
        ("Conservative", conservative_strategy),
        ("Aggressive", aggressive_strategy),
        ("Symbol-Specific", symbol_strategy)
    ]
    
    for name, strategy in strategies:
        if name == "Symbol-Specific":
            signals = strategy.generate_signals_with_advanced_filters(df)
        else:
            signals = strategy.generate_signals_with_filters(df)
        
        print(f"{name} Strategy: {len(signals[signals != 0])} signals")
    
    return strategies


def main():
    """Main demonstration function."""
    print("🚀 ADVANCED FILTER DEMO")
    print("Demonstrating Enhanced Strategy Base Class")
    print("ALL strategy classes now inherit these capabilities!")
    
    # Run all demonstrations
    demonstrate_basic_filtering()
    demonstrate_symbol_specific_filtering()
    demonstrate_dynamic_filtering()
    demonstrate_config_based_filtering()
    demonstrate_filter_validation_and_analytics()
    demonstrate_multi_strategy_filtering()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)
    print("Key Takeaways:")
    print("1. ALL strategy classes inherit advanced filtering")
    print("2. Symbol-specific filtering for different rules per stock")
    print("3. Dynamic filtering that adapts to market conditions")
    print("4. Configuration-driven filtering from YAML")
    print("5. Filter validation and comprehensive analytics")
    print("6. Multiple filtering approaches can coexist")
    print("\nNo more need for separate FilterableStrategy class!")


if __name__ == "__main__":
    main() 