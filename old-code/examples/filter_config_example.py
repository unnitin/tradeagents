#!/usr/bin/env python3
"""
Filter Configuration Demo

This example demonstrates how to use the new filter configuration system
to load and apply different filtering configurations from YAML files.
"""

import sys
import os

# Add the parent directory to sys.path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.filter_config import FilterConfigManager, load_filter_config
from filters import StockFilter, TimeFilter, LiquidityFilter


def main():
    """Demonstrate filter configuration loading and usage."""
    print("=== Filter Configuration Demo ===\n")
    
    # Create a filter configuration manager
    try:
        config_manager = FilterConfigManager()
        print("✓ Filter configuration manager created successfully")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("Make sure the filters.yaml file exists in the config directory")
        return
    
    # List available configurations
    print("\nAvailable filter configurations:")
    configs = config_manager.list_available_configs()
    for config in configs:
        print(f"  - {config}")
    
    # List available combinations
    print("\nAvailable filter combinations:")
    combinations = config_manager.list_available_combinations()
    for combo in combinations:
        print(f"  - {combo}")
    
    # Load different configurations
    print("\n=== Loading Different Configurations ===")
    
    # Load default configuration
    print("\n1. Default Configuration:")
    default_config = load_filter_config("default")
    print(f"   Min volume: {default_config.min_volume:,.0f}")
    print(f"   Min price: ${default_config.min_price}")
    print(f"   Max volatility: {default_config.max_volatility}")
    print(f"   Excluded symbols: {default_config.exclude_symbols}")
    
    # Load large cap conservative configuration
    print("\n2. Large Cap Conservative Configuration:")
    try:
        large_cap_config = load_filter_config("large_cap_conservative")
        print(f"   Min volume: {large_cap_config.min_volume:,.0f}")
        print(f"   Min price: ${large_cap_config.min_price}")
        print(f"   Max price: ${large_cap_config.max_price}")
        print(f"   Min market cap: ${large_cap_config.min_market_cap:,.0f}")
        print(f"   Max volatility: {large_cap_config.max_volatility}")
        print(f"   Excluded symbols: {large_cap_config.exclude_symbols}")
    except ValueError as e:
        print(f"   Error loading config: {e}")
    
    # Load ETF portfolio configuration
    print("\n3. ETF Portfolio Configuration:")
    try:
        etf_config = load_filter_config("etf_portfolio")
        print(f"   Min volume: {etf_config.min_volume:,.0f}")
        print(f"   Min price: ${etf_config.min_price}")
        print(f"   Max price: ${etf_config.max_price}")
        print(f"   Max volatility: {etf_config.max_volatility}")
        print(f"   Included symbols: {etf_config.include_symbols}")
    except ValueError as e:
        print(f"   Error loading config: {e}")
    
    # Create filters using configurations
    print("\n=== Creating Filters from Configurations ===")
    
    # Create a stock filter with default configuration
    print("\n1. Stock Filter (Default):")
    stock_filter = StockFilter(
        min_volume=default_config.min_volume,
        min_price=default_config.min_price,
        max_price=default_config.max_price,
        max_volatility=default_config.max_volatility,
        exclude_symbols=default_config.exclude_symbols,
        include_symbols=default_config.include_symbols
    )
    print(f"   Filter created: {stock_filter.get_filter_info()}")
    
    # Create time filter using configuration
    print("\n2. Time Filter (Large Cap Conservative):")
    try:
        time_config = config_manager.get_time_filter_config("large_cap_conservative")
        time_filter = TimeFilter(
            exclude_dates=time_config.get("exclude_dates", []),
            include_dates=time_config.get("include_dates", []),
            start_time=time_config.get("start_time"),
            end_time=time_config.get("end_time"),
            exclude_earnings_periods=time_config.get("exclude_earnings_periods", False),
            exclude_market_holidays=time_config.get("exclude_market_holidays", True),
            min_trading_days=time_config.get("min_trading_days", 30)
        )
        print(f"   Filter created: {time_filter.get_filter_info()}")
    except ValueError as e:
        print(f"   Error creating time filter: {e}")
    
    # Create liquidity filter using configuration
    print("\n3. Liquidity Filter (Day Trading):")
    try:
        liquidity_config = config_manager.get_liquidity_filter_config("day_trading")
        liquidity_filter = LiquidityFilter(
            min_avg_volume=liquidity_config.get("min_avg_volume", 1000000.0),
            volume_window=liquidity_config.get("volume_window", 20),
            max_bid_ask_spread=liquidity_config.get("max_bid_ask_spread"),
            min_dollar_volume=liquidity_config.get("min_dollar_volume")
        )
        print(f"   Filter created: {liquidity_filter.get_filter_info()}")
    except ValueError as e:
        print(f"   Error creating liquidity filter: {e}")
    
    # Demonstrate configuration validation
    print("\n=== Configuration Validation ===")
    
    # Validate configurations
    configs_to_validate = ["default", "large_cap_conservative", "day_trading"]
    for config_name in configs_to_validate:
        try:
            config_manager.validate_config(config_name)
            print(f"✓ {config_name} configuration is valid")
        except ValueError as e:
            print(f"✗ {config_name} configuration is invalid: {e}")
        except Exception as e:
            print(f"✗ Error validating {config_name}: {e}")
    
    # Show settings
    print("\n=== Global Settings ===")
    try:
        settings = config_manager.get_settings()
        print("Global filter settings:")
        for key, value in settings.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error getting settings: {e}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main() 