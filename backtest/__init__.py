"""
Backtest module for evaluating trading strategy performance.

This module provides comprehensive backtesting functionality including:
- Strategy performance evaluation against defined parameters
- Time duration and stock filtering capabilities
- Performance metrics calculation (returns, variance, Sharpe ratio, etc.)
- Results storage and analysis
- Strategy combination testing via composer integration

Usage:
    from backtest import BacktestEngine, create_backtest_engine
    from backtest.metrics import PerformanceMetrics
    from backtest.filters import StockFilter
    
    # Simple backtest
    engine = create_backtest_engine()
    results = engine.run_backtest(strategy, data, start_date, end_date)
    
    # Advanced backtest with filters
    stock_filter = StockFilter(min_volume=1000000, min_price=10)
    results = engine.run_backtest(strategy, data, 
                                 start_date, end_date, 
                                 stock_filter=stock_filter)
    
    # Composer integration for strategy combinations
    results = engine.run_composer_backtest('technical_ensemble', symbols, start_date, end_date)
"""

from .engine import BacktestEngine, create_backtest_engine
from .metrics import PerformanceMetrics, calculate_performance_metrics
from .filters import StockFilter, TimeFilter
from .results import BacktestResults, save_results, load_results
from .portfolio import Portfolio

__all__ = [
    'BacktestEngine',
    'create_backtest_engine',
    'PerformanceMetrics',
    'calculate_performance_metrics',
    'StockFilter',
    'TimeFilter',
    'BacktestResults',
    'save_results',
    'load_results',
    'Portfolio'
] 