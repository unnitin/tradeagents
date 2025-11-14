"""
Filters Module

This module provides comprehensive filtering functionality for stock trading strategies.
It includes various filter types for stock selection, time-based filtering, liquidity
requirements, and composite filtering capabilities.

Key Features:
- Stock filtering by price, volume, market cap, volatility
- Time-based filtering for specific dates, times, and market conditions
- Liquidity filtering based on trading volume and bid-ask spreads
- Composite filtering with AND/OR logic combinations
- Integration with strategy composition and backtesting systems

Usage:
    from filters import StockFilter, TimeFilter, LiquidityFilter, CompositeFilter
    
    # Create individual filters
    stock_filter = StockFilter(min_volume=2000000, min_price=10.0)
    time_filter = TimeFilter(exclude_market_holidays=True)
    
    # Combine filters
    composite_filter = CompositeFilter([stock_filter, time_filter], logic="AND")
    
    # Apply to data
    filtered_data = composite_filter.apply_filter(data)
"""

from .core import (
    BaseFilter,
    StockFilter,
    TimeFilter,
    LiquidityFilter,
    CompositeFilter
)

# Version information
__version__ = "1.0.0"

# Main exports
__all__ = [
    "BaseFilter",
    "StockFilter", 
    "TimeFilter",
    "LiquidityFilter",
    "CompositeFilter"
]


def create_stock_filter(config: dict) -> StockFilter:
    """
    Create a StockFilter from configuration dictionary.
    
    Args:
        config: Configuration dictionary with filter parameters
        
    Returns:
        Configured StockFilter instance
    """
    return StockFilter(**config)


def create_time_filter(config: dict) -> TimeFilter:
    """
    Create a TimeFilter from configuration dictionary.
    
    Args:
        config: Configuration dictionary with filter parameters
        
    Returns:
        Configured TimeFilter instance
    """
    return TimeFilter(**config)


def create_liquidity_filter(config: dict) -> LiquidityFilter:
    """
    Create a LiquidityFilter from configuration dictionary.
    
    Args:
        config: Configuration dictionary with filter parameters
        
    Returns:
        Configured LiquidityFilter instance
    """
    return LiquidityFilter(**config)


def create_composite_filter(filters: list, logic: str = "AND") -> CompositeFilter:
    """
    Create a CompositeFilter from a list of filters.
    
    Args:
        filters: List of filter instances
        logic: Combination logic ("AND" or "OR")
        
    Returns:
        Configured CompositeFilter instance
    """
    return CompositeFilter(filters, logic)


# Convenience functions for common filter configurations
def create_conservative_filter() -> CompositeFilter:
    """
    Create a conservative filter configuration suitable for stable strategies.
    
    Returns:
        CompositeFilter with conservative settings
    """
    stock_filter = StockFilter(
        min_volume=5000000.0,
        min_price=20.0,
        max_price=500.0,
        max_volatility=0.03
    )
    
    time_filter = TimeFilter(
        exclude_market_holidays=True,
        exclude_earnings_periods=True,
        min_trading_days=60
    )
    
    liquidity_filter = LiquidityFilter(
        min_avg_volume=5000000.0,
        volume_window=30,
        max_bid_ask_spread=0.001
    )
    
    return CompositeFilter([stock_filter, time_filter, liquidity_filter], logic="AND")


def create_aggressive_filter() -> CompositeFilter:
    """
    Create an aggressive filter configuration suitable for high-risk strategies.
    
    Returns:
        CompositeFilter with aggressive settings
    """
    stock_filter = StockFilter(
        min_volume=1000000.0,
        min_price=5.0,
        max_volatility=0.10  # Allow higher volatility
    )
    
    time_filter = TimeFilter(
        exclude_market_holidays=True,
        min_trading_days=30
    )
    
    liquidity_filter = LiquidityFilter(
        min_avg_volume=1000000.0,
        volume_window=20
    )
    
    return CompositeFilter([stock_filter, time_filter, liquidity_filter], logic="AND")


def create_day_trading_filter() -> CompositeFilter:
    """
    Create a filter configuration optimized for day trading strategies.
    
    Returns:
        CompositeFilter with day trading settings
    """
    stock_filter = StockFilter(
        min_volume=5000000.0,
        min_price=10.0,
        max_price=200.0
    )
    
    time_filter = TimeFilter(
        start_time="09:45",  # Avoid opening volatility
        end_time="15:30",    # Avoid closing volatility
        exclude_market_holidays=True
    )
    
    liquidity_filter = LiquidityFilter(
        min_avg_volume=10000000.0,
        volume_window=5,
        max_bid_ask_spread=0.0005,
        min_dollar_volume=50000000.0
    )
    
    return CompositeFilter([stock_filter, time_filter, liquidity_filter], logic="AND")


# Export convenience functions
__all__.extend([
    "create_stock_filter",
    "create_time_filter", 
    "create_liquidity_filter",
    "create_composite_filter",
    "create_conservative_filter",
    "create_aggressive_filter",
    "create_day_trading_filter"
]) 