"""
Configuration module for the trading system.

This module provides configuration management for various components
including backtest settings, strategy parameters, and system settings.
"""

from .backtest_config import BacktestConfigManager, BacktestConfig, load_backtest_config, create_backtest_config
from .filter_config import FilterConfig, FilterConfigManager, load_filter_config, create_filter_config_manager

__all__ = [
    'BacktestConfigManager',
    'BacktestConfig',
    'load_backtest_config',
    'create_backtest_config',
    'FilterConfig',
    'FilterConfigManager',
    'load_filter_config',
    'create_filter_config_manager'
] 