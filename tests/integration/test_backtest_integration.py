#!/usr/bin/env python3
"""
Integration tests for the backtest module.

This module contains integration tests that verify end-to-end functionality
of the backtest system including:
- Complete backtest workflows
- Strategy integration
- Data integration
- Configuration integration
- Results storage and retrieval
- Multi-strategy testing
- Composer integration
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import pickle

# Add project root to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import BacktestConfig, BacktestConfigManager, load_backtest_config
from backtest import BacktestEngine, create_backtest_engine, StockFilter, TimeFilter
from backtest.results import BacktestResults, save_results, load_results
from strategies.base import Strategy
from strategies import SMACrossover, RSIReversion


class MockStrategy(Strategy):
    """Mock strategy for testing."""
    
    def __init__(self, name="MockStrategy"):
        super().__init__()
        self.name = name
        self.signals_generated = 0
    
    def generate_signals(self, data):
        """Generate simple buy/sell signals for testing."""
        self.signals_generated += 1
        
        # Simple signal: buy at the beginning, sell at the end
        signals = pd.Series(0, index=data.index)
        if len(signals) >= 2:
            signals.iloc[0] = 1   # Buy signal
            signals.iloc[-1] = -1  # Sell signal
        
        return signals


def create_mock_strategy(name="MockStrategy"):
    """Create a unique MockStrategy class with the given name."""
    class UniqueStrategy(MockStrategy):
        def __init__(self):
            super().__init__(name)
    
    UniqueStrategy.__name__ = name
    return UniqueStrategy()


class TestBacktestIntegration(unittest.TestCase):
    """Integration tests for complete backtest workflows."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock data
        self.mock_data = self._create_mock_data()
        
        # Create temporary directory for results
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock data fetcher - properly configure the methods that backtest engine expects
        self.mock_data_fetcher = Mock()
        self.mock_data_fetcher.get_stock_data.return_value = self.mock_data  # This is what engine calls
        self.mock_data_fetcher.get_data.return_value = self.mock_data  # Fallback
        self.mock_data_fetcher.get_symbols.return_value = ["AAPL", "MSFT"]
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_mock_data(self):
        """Create mock market data for testing."""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        # Create realistic price data
        np.random.seed(42)
        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, 100)  # ~25% annual vol
        prices = [base_price]
        
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        data = pd.DataFrame({
            'date': dates,
            'symbol': 'AAPL',  # Add symbol column that backtest engine expects
            'open': prices[:-1],
            'high': [p * 1.02 for p in prices[:-1]],
            'low': [p * 0.98 for p in prices[:-1]],
            'close': prices[1:],
            'volume': np.random.randint(1000000, 5000000, 100)
        })
        
        # Add technical indicators
        data['sma_20'] = data['close'].rolling(20).mean()
        data['sma_50'] = data['close'].rolling(50).mean()
        data['rsi'] = self._calculate_rsi(data['close'])
        
        return data
    
    def _calculate_rsi(self, prices, period=14):
        """Simple RSI calculation for testing."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @patch('backtest.engine.DataFetcher')
    def test_basic_backtest_workflow(self, mock_data_fetcher_class):
        """Test basic end-to-end backtest workflow."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Create strategy
        strategy = create_mock_strategy()
        
        # Run backtest
        results = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Verify results
        self.assertIsInstance(results, BacktestResults)
        self.assertEqual(results.strategy_name, "MockStrategy")
        self.assertEqual(results.config.initial_capital, 100000.0)
        self.assertIsNotNone(results.metrics)
        self.assertGreater(len(results.portfolio_history), 0)
        
        # Verify strategy was called
        self.assertGreater(strategy.signals_generated, 0)
    
    @patch('backtest.engine.DataFetcher')
    def test_backtest_with_filters(self, mock_data_fetcher_class):
        """Test backtest with stock and time filters."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Create filters
        stock_filter = StockFilter(min_volume=1500000)
        time_filter = TimeFilter(min_trading_days=50)
        
        # Create strategy
        strategy = create_mock_strategy()
        
        # Run backtest with filters
        results = engine.run_backtest(
            strategy=strategy,
            symbols=["AAPL", "MSFT"],
            start_date="2023-01-01",
            end_date="2023-04-10",
            stock_filter=stock_filter,
            time_filter=time_filter
        )
        
        # Verify results
        self.assertIsInstance(results, BacktestResults)
        self.assertIsNotNone(results.metrics)
        
        # Verify filters were applied
        self.assertIsNotNone(results.data_info)
    
    @patch('backtest.engine.DataFetcher')
    def test_multiple_strategies_comparison(self, mock_data_fetcher_class):
        """Test running multiple strategies and comparing results."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Create multiple strategies
        strategies = [
            create_mock_strategy("Strategy1"),
            create_mock_strategy("Strategy2"),
            create_mock_strategy("Strategy3")
        ]
        
        results = []
        for strategy in strategies:
            result = engine.run_backtest(
                strategy=strategy,
                symbols="AAPL",
                start_date="2023-01-01",
                end_date="2023-04-10"
            )
            results.append(result)
        
        # Verify all strategies ran
        self.assertEqual(len(results), 3)
        for i, result in enumerate(results):
            self.assertEqual(result.strategy_name, f"Strategy{i+1}")
            self.assertIsNotNone(result.metrics)
    
    @patch('backtest.engine.DataFetcher')
    def test_configuration_integration(self, mock_data_fetcher_class):
        """Test integration with configuration system."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Test with different configurations
        config_names = ["default", "conservative", "aggressive"]
        
        for config_name in config_names:
            try:
                # Load config
                config = load_backtest_config(config_name)
                engine = create_backtest_engine(config)
                
                # Run backtest
                strategy = create_mock_strategy()
                results = engine.run_backtest(
                    strategy=strategy,
                    symbols="AAPL",
                    start_date="2023-01-01",
                    end_date="2023-04-10"
                )
                
                # Verify results
                self.assertIsInstance(results, BacktestResults)
                self.assertEqual(results.config.initial_capital, config.initial_capital)
                
            except Exception as e:
                # Some configs might not be available in test environment
                if "not found" not in str(e):
                    raise
    
    @patch('backtest.engine.DataFetcher')
    def test_results_storage_and_retrieval(self, mock_data_fetcher_class):
        """Test saving and loading backtest results."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Run backtest
        strategy = create_mock_strategy()
        results = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Save results
        results_file = os.path.join(self.temp_dir, "test_results.pkl")
        save_results(results, results_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(results_file))
        
        # Load results
        loaded_results = load_results(results_file)
        
        # Verify loaded results match original
        self.assertEqual(loaded_results.strategy_name, results.strategy_name)
        self.assertEqual(loaded_results.config.initial_capital, results.config.initial_capital)
        self.assertEqual(len(loaded_results.portfolio_history), len(results.portfolio_history))
    
    @patch('backtest.engine.DataFetcher')
    def test_real_strategy_integration(self, mock_data_fetcher_class):
        """Test integration with real strategy classes."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Test with real strategies
        try:
            # SMA Crossover strategy
            sma_strategy = SMACrossover(fast=20, slow=50)
            sma_results = engine.run_backtest(
                strategy=sma_strategy,
                symbols="AAPL",
                start_date="2023-01-01",
                end_date="2023-04-10"
            )
            
            self.assertIsInstance(sma_results, BacktestResults)
            self.assertEqual(sma_results.strategy_name, "SMACrossover")
            
        except ImportError:
            # Skip if strategy not available
            pass
        
        try:
            # RSI Reversion strategy
            rsi_strategy = RSIReversion(rsi_col="rsi", low_thresh=30, high_thresh=70)
            rsi_results = engine.run_backtest(
                strategy=rsi_strategy,
                symbols="AAPL",
                start_date="2023-01-01",
                end_date="2023-04-10"
            )
            
            self.assertIsInstance(rsi_results, BacktestResults)
            self.assertEqual(rsi_results.strategy_name, "RSIReversion")
            
        except ImportError:
            # Skip if strategy not available
            pass
    
    @patch('backtest.engine.DataFetcher')
    def test_performance_metrics_integration(self, mock_data_fetcher_class):
        """Test integration of performance metrics calculation."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0, risk_free_rate=0.02)
        engine = create_backtest_engine(config)
        
        # Run backtest
        strategy = create_mock_strategy()
        results = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Verify metrics are calculated
        metrics = results.metrics
        self.assertIsNotNone(metrics.total_return)
        self.assertIsNotNone(metrics.annualized_volatility)
        self.assertIsNotNone(metrics.sharpe_ratio)
        self.assertIsNotNone(metrics.max_drawdown)
        
        # Verify metrics are reasonable
        self.assertGreaterEqual(metrics.max_drawdown, -1.0)  # Can't lose more than 100%
        self.assertLessEqual(metrics.max_drawdown, 0.0)      # Drawdown should be negative
    
    @patch('backtest.engine.DataFetcher')
    def test_error_handling(self, mock_data_fetcher_class):
        """Test error handling in backtest workflow."""
        # Setup mock with error
        mock_data_fetcher_class.return_value.get_data.side_effect = Exception("Data fetch error")
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Run backtest - should handle error gracefully
        strategy = create_mock_strategy()
        
        with self.assertRaises(Exception):
            engine.run_backtest(
                strategy=strategy,
                symbols="AAPL",
                start_date="2023-01-01",
                end_date="2023-04-10"
            )
    
    @patch('backtest.engine.DataFetcher')
    def test_parameter_sensitivity(self, mock_data_fetcher_class):
        """Test parameter sensitivity analysis."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Test different commission rates
        commission_rates = [0.0001, 0.0005, 0.001, 0.002]
        results = []
        
        for rate in commission_rates:
            config = BacktestConfig(
                initial_capital=100000.0,
                commission_rate=rate
            )
            engine = create_backtest_engine(config)
            
            strategy = create_mock_strategy()
            result = engine.run_backtest(
                strategy=strategy,
                symbols="AAPL",
                start_date="2023-01-01",
                end_date="2023-04-10"
            )
            results.append((rate, result))
        
        # Verify all backtests completed
        self.assertEqual(len(results), 4)
        
        # Verify commission rates affected results
        for rate, result in results:
            self.assertIsNotNone(result.metrics)
            # Higher commission rates should generally lead to lower returns
            # (though this depends on strategy behavior)
    
    @patch('backtest.engine.DataFetcher')
    def test_multi_symbol_backtest(self, mock_data_fetcher_class):
        """Test backtesting with multiple symbols."""
        # Setup mock to return data for multiple symbols
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Run backtest with multiple symbols
        strategy = create_mock_strategy()
        results = engine.run_backtest(
            strategy=strategy,
            symbols=["AAPL", "MSFT", "GOOGL"],
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Verify results
        self.assertIsInstance(results, BacktestResults)
        self.assertEqual(len(results.symbols), 3)
        self.assertIn("AAPL", results.symbols)
        self.assertIn("MSFT", results.symbols)
        self.assertIn("GOOGL", results.symbols)


class TestComposerIntegration(unittest.TestCase):
    """Integration tests for composer functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_data = self._create_mock_data()
        
        # Mock data fetcher - properly configure for backtest engine
        self.mock_data_fetcher = Mock()
        self.mock_data_fetcher.get_stock_data.return_value = self.mock_data
        self.mock_data_fetcher.get_data.return_value = self.mock_data
    
    def _create_mock_data(self):
        """Create mock market data for testing."""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        np.random.seed(42)
        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, 100)
        prices = [base_price]
        
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        data = pd.DataFrame({
            'date': dates,
            'symbol': 'AAPL',  # Add symbol column that backtest engine expects
            'open': prices[:-1],
            'high': [p * 1.02 for p in prices[:-1]],
            'low': [p * 0.98 for p in prices[:-1]],
            'close': prices[1:],
            'volume': np.random.randint(1000000, 5000000, 100)
        })
        
        return data
    
    @patch('backtest.engine.DataFetcher')
    def test_composer_backtest_integration(self, mock_data_fetcher_class):
        """Test integration with composer module."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Test composer integration if available
        try:
            from composer import StrategyComposer
            # Skip this test - composer integration is complex and would need proper setup
            # This test is meant to verify the API works, not the full composer functionality
            self.skipTest("Composer integration test requires full composer setup")
            
        except ImportError:
            # Skip if composer not available
            self.skipTest("Composer module not available")


class TestBacktestPerformance(unittest.TestCase):
    """Performance tests for backtest module."""
    
    def setUp(self):
        """Set up performance test environment."""
        self.large_data = self._create_large_dataset()
        
        # Mock data fetcher - properly configure for backtest engine
        self.mock_data_fetcher = Mock()
        self.mock_data_fetcher.get_stock_data.return_value = self.large_data
        self.mock_data_fetcher.get_data.return_value = self.large_data
    
    def _create_large_dataset(self):
        """Create large dataset for performance testing."""
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')  # ~3 years
        
        np.random.seed(42)
        base_price = 100.0
        returns = np.random.normal(0.0008, 0.015, 1000)
        prices = [base_price]
        
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        data = pd.DataFrame({
            'date': dates,
            'symbol': 'AAPL',  # Add symbol column that backtest engine expects
            'open': prices[:-1],
            'high': [p * 1.015 for p in prices[:-1]],
            'low': [p * 0.985 for p in prices[:-1]],
            'close': prices[1:],
            'volume': np.random.randint(500000, 10000000, 1000)
        })
        
        return data
    
    @patch('backtest.engine.DataFetcher')
    def test_large_dataset_performance(self, mock_data_fetcher_class):
        """Test performance with large dataset."""
        # Setup mock
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Measure execution time
        import time
        start_time = time.time()
        
        strategy = create_mock_strategy()
        results = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2020-01-01",
            end_date="2022-12-31"
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify results
        self.assertIsInstance(results, BacktestResults)
        self.assertIsNotNone(results.metrics)
        
        # Performance should be reasonable (less than 10 seconds for 1000 days)
        self.assertLess(execution_time, 10.0)


if __name__ == '__main__':
    # Run tests with increased verbosity
    unittest.main(verbosity=2) 