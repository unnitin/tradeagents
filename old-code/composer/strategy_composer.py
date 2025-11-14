"""
Strategy Composer Core Module

This module provides functionality to:
1. Register different strategies from the strategies/ module
2. Load configurations from YAML files
3. Combine various strategies using different methods
4. Support individual strategy execution (like quiver strategies)
5. Output strategies that plug into backtesting and execution
"""

import yaml
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import importlib
from abc import ABC, abstractmethod

# Import all available strategies using clean public API
from strategies import (
    Strategy, SMACrossover, RSIReversion, MACDCross, 
    BollingerBounce, ATRVolatilityFilter, SentimentLLMStrategy,
    PoliticianFollowingStrategy, PelosiTrackingStrategy, CongressMomentumStrategy
)

# Import filter classes
from filters import StockFilter, TimeFilter, LiquidityFilter, CompositeFilter
from config.filter_config import FilterConfigManager


class StrategyComposer:
    """
    Main composer class that handles strategy registration, configuration loading,
    and strategy combination.
    """
    
    def __init__(self, config_path: str = "config/strategies.yaml"):
        """
        Initialize the composer with a configuration file.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.strategy_classes = self._get_strategy_classes()
        self.initialized_strategies = {}
        self.filters = {}
        self.filter_config_manager = FilterConfigManager()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _get_strategy_classes(self) -> Dict[str, type]:
        """Get all available strategy classes."""
        return {
            'SMACrossover': SMACrossover,
            'RSIReversion': RSIReversion,
            'MACDCross': MACDCross,
            'BollingerBounce': BollingerBounce,
            'ATRVolatilityFilter': ATRVolatilityFilter,
            'SentimentLLMStrategy': SentimentLLMStrategy,
            'PoliticianFollowingStrategy': PoliticianFollowingStrategy,
            'PelosiTrackingStrategy': PelosiTrackingStrategy,
            'CongressMomentumStrategy': CongressMomentumStrategy,
        }
    
    def register_strategies(self) -> None:
        """Register and initialize all enabled strategies from configuration."""
        strategies_config = self.config.get('strategies', {})
        
        for strategy_name, strategy_config in strategies_config.items():
            if not strategy_config.get('enabled', True):
                continue
                
            class_name = strategy_config.get('class')
            parameters = strategy_config.get('parameters', {})
            strategy_type = strategy_config.get('type', 'directional')
            
            if class_name not in self.strategy_classes:
                raise ValueError(f"Unknown strategy class: {class_name}")
            
            # Initialize strategy with parameters
            strategy_class = self.strategy_classes[class_name]
            strategy_instance = strategy_class(**parameters)
            
            if strategy_type == 'filter':
                self.filters[strategy_name] = strategy_instance
            else:
                self.initialized_strategies[strategy_name] = strategy_instance
    
    def get_strategy(self, strategy_name: str) -> Strategy:
        """Get a specific initialized strategy."""
        if strategy_name not in self.initialized_strategies:
            raise ValueError(f"Strategy '{strategy_name}' not found or not enabled")
        return self.initialized_strategies[strategy_name]
    
    def get_filter(self, filter_name: str) -> Strategy:
        """Get a specific initialized filter."""
        if filter_name not in self.filters:
            raise ValueError(f"Filter '{filter_name}' not found or not enabled")
        return self.filters[filter_name]
    
    def create_filter_from_config(self, filter_config: Dict[str, Any]) -> List:
        """
        Create filter instances from configuration.
        
        Args:
            filter_config: Filter configuration dictionary
            
        Returns:
            List of filter instances
        """
        filters = []
        
        if 'stock_filter' in filter_config:
            stock_config = filter_config['stock_filter']
            stock_filter = StockFilter(
                min_volume=stock_config.get('min_volume', 1000000.0),
                min_price=stock_config.get('min_price', 5.0),
                max_price=stock_config.get('max_price'),
                min_market_cap=stock_config.get('min_market_cap'),
                max_volatility=stock_config.get('max_volatility'),
                exclude_symbols=stock_config.get('exclude_symbols', []),
                include_symbols=stock_config.get('include_symbols', [])
            )
            filters.append(stock_filter)
            
        if 'time_filter' in filter_config:
            time_config = filter_config['time_filter']
            time_filter = TimeFilter(
                exclude_dates=time_config.get('exclude_dates', []),
                include_dates=time_config.get('include_dates', []),
                start_time=time_config.get('start_time'),
                end_time=time_config.get('end_time'),
                exclude_earnings_periods=time_config.get('exclude_earnings_periods', False),
                exclude_market_holidays=time_config.get('exclude_market_holidays', True),
                min_trading_days=time_config.get('min_trading_days', 30)
            )
            filters.append(time_filter)
            
        if 'liquidity_filter' in filter_config:
            liquidity_config = filter_config['liquidity_filter']
            liquidity_filter = LiquidityFilter(
                min_avg_volume=liquidity_config.get('min_avg_volume', 1000000.0),
                volume_window=liquidity_config.get('volume_window', 20),
                max_bid_ask_spread=liquidity_config.get('max_bid_ask_spread'),
                min_dollar_volume=liquidity_config.get('min_dollar_volume')
            )
            filters.append(liquidity_filter)
            
        return filters
    
    def apply_filters_to_data(self, df: pd.DataFrame, filters: List, logic: str = "AND") -> pd.DataFrame:
        """
        Apply filters to DataFrame.
        
        Args:
            df: Input DataFrame
            filters: List of filter instances
            logic: How to combine filters ("AND" or "OR")
            
        Returns:
            Filtered DataFrame
        """
        if not filters:
            return df
            
        if len(filters) == 1:
            return filters[0].apply_filter(df)
        
        composite_filter = CompositeFilter(filters, logic)
        return composite_filter.apply_filter(df)
    
    def combine_strategies(self, combination_name: str, df: pd.DataFrame) -> pd.Series:
        """
        Combine multiple strategies according to the specified combination method.
        
        Args:
            combination_name: Name of the combination from config
            df: DataFrame with market data
            
        Returns:
            Combined trading signals
        """
        if combination_name not in self.config.get('combinations', {}):
            raise ValueError(f"Combination '{combination_name}' not found in configuration")
        
        combination_config = self.config['combinations'][combination_name]
        strategy_names = combination_config.get('strategies', [])
        method = combination_config.get('method', 'majority_vote')
        weights = combination_config.get('weights', {})
        filter_names = combination_config.get('filters', [])
        
        # Handle new filter configuration format
        filter_config = combination_config.get('filter_config', {})
        
        # Apply data-level filters first if specified
        working_df = df
        if filter_config:
            data_filters = self.create_filter_from_config(filter_config)
            filter_logic = filter_config.get('logic', 'AND')
            working_df = self.apply_filters_to_data(df, data_filters, filter_logic)
        
        # Generate signals from individual strategies
        signals = []
        for strategy_name in strategy_names:
            strategy = self.get_strategy(strategy_name)
            
            # Check if strategy has individual filter configuration
            strategy_config = self.config.get('strategies', {}).get(strategy_name, {})
            strategy_filter_config = strategy_config.get('filter_config', {})
            
            if strategy_filter_config:
                # Configure filters for this strategy
                strategy_filters = self.create_filter_from_config(strategy_filter_config)
                strategy_filter_logic = strategy_filter_config.get('logic', 'AND')
                strategy.set_filters(strategy_filters, strategy_filter_logic)
                
                # Use filtered signal generation
                signal = strategy.generate_signals_with_filters(working_df)
            else:
                signal = strategy.generate_signals(working_df)
                
            signals.append(signal)
        
        # Combine signals based on method
        if method == 'single':
            if len(signals) != 1:
                raise ValueError("Single method requires exactly one strategy")
            combined_signal = signals[0]
        elif method == 'majority_vote':
            combined_signal = self._majority_vote(signals)
        elif method == 'weighted_average':
            combined_signal = self._weighted_average(signals, strategy_names, weights)
        elif method == 'unanimous':
            combined_signal = self._unanimous(signals)
        else:
            raise ValueError(f"Unknown combination method: {method}")
        
        # Apply legacy filter-based strategies (for backward compatibility)
        for filter_name in filter_names:
            filter_strategy = self.get_filter(filter_name)
            filter_signal = filter_strategy.generate_signals(working_df)
            combined_signal = self._apply_filter(combined_signal, filter_signal)
        
        return combined_signal
    
    def _majority_vote(self, signals: List[pd.Series]) -> pd.Series:
        """Combine signals using majority vote."""
        if not signals:
            raise ValueError("No signals to combine")
        
        # Sum all signals and take the sign
        combined = signals[0].copy()
        for signal in signals[1:]:
            combined = combined.add(signal, fill_value=0)
        return pd.Series(combined.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0)), dtype=int)
    
    def _weighted_average(self, signals: List[pd.Series], strategy_names: List[str], 
                         weights: Dict[str, float]) -> pd.Series:
        """Combine signals using weighted average."""
        if not signals:
            raise ValueError("No signals to combine")
        
        # Normalize weights to sum to 1
        total_weight = sum(weights.get(name, 1.0) for name in strategy_names)
        normalized_weights = {name: weights.get(name, 1.0) / total_weight 
                            for name in strategy_names}
        
        # Calculate weighted average
        combined = pd.Series(0.0, index=signals[0].index)
        for signal, strategy_name in zip(signals, strategy_names):
            weight = normalized_weights[strategy_name]
            combined = combined.add(signal * weight, fill_value=0)
        
        # Apply threshold to convert to discrete signals
        threshold = self.config.get('settings', {}).get('signal_threshold', 0.5)
        return pd.Series(combined.apply(lambda x: 1 if x >= threshold else (-1 if x <= -threshold else 0)), dtype=int)
    
    def _unanimous(self, signals: List[pd.Series]) -> pd.Series:
        """Combine signals requiring unanimous agreement."""
        if not signals:
            raise ValueError("No signals to combine")
        
        # All signals must agree on direction
        combined = signals[0].copy()
        for signal in signals[1:]:
            # Keep signal only if all agree
            combined = combined.where(combined == signal, 0)
        
        return combined
    
    def _apply_filter(self, signal: pd.Series, filter_signal: pd.Series) -> pd.Series:
        """Apply a filter to the combined signal."""
        # Filter typically zeros out signals when conditions aren't met
        # Assuming filter returns 1 for allow, 0 for block
        return signal * filter_signal
    
    def execute_combination(self, combination_name: str, df: pd.DataFrame) -> pd.Series:
        """
        Execute a specific combination and return the signals.
        This is the main method that should be called by backtesting/execution modules.
        
        Args:
            combination_name: Name of the combination to execute
            df: DataFrame with market data
            
        Returns:
            Trading signals ready for backtesting/execution
        """
        if not self.initialized_strategies:
            self.register_strategies()
        
        return self.combine_strategies(combination_name, df)
    
    def list_available_combinations(self) -> List[str]:
        """List all available combinations from config."""
        return list(self.config.get('combinations', {}).keys())
    
    def list_available_strategies(self) -> List[str]:
        """List all available strategies from config."""
        return list(self.config.get('strategies', {}).keys())
    
    def get_combination_info(self, combination_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific combination."""
        if combination_name not in self.config.get('combinations', {}):
            raise ValueError(f"Combination '{combination_name}' not found")
        
        return self.config['combinations'][combination_name]


# Convenience functions for easy usage
def create_composer(config_path: str = "config/strategies.yaml") -> StrategyComposer:
    """Create and initialize a strategy composer."""
    composer = StrategyComposer(config_path)
    composer.register_strategies()
    return composer


def get_signals(combination_name: str, df: pd.DataFrame, 
                config_path: str = "config/strategies.yaml") -> pd.Series:
    """
    Convenience function to get trading signals from a combination.
    
    Args:
        combination_name: Name of the combination to execute
        df: DataFrame with market data
        config_path: Path to configuration file
        
    Returns:
        Trading signals
    """
    composer = create_composer(config_path)
    return composer.execute_combination(combination_name, df) 