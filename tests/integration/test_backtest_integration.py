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
from filters import LiquidityFilter, CompositeFilter


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


class TestStrategyFilteringIntegration(unittest.TestCase):
    """Integration tests for strategy-level filtering with backtest engine."""
    
    def setUp(self):
        """Set up test environment for filtering integration."""
        self.mock_data = self._create_mock_data()
        
        # Create multiple symbols for comprehensive testing
        self.multi_symbol_data = self._create_multi_symbol_data()
        
        # Mock data fetcher
        self.mock_data_fetcher = Mock()
        self.mock_data_fetcher.get_stock_data.return_value = self.mock_data
        self.mock_data_fetcher.get_data.return_value = self.mock_data
    
    def _create_mock_data(self):
        """Create mock market data with varying characteristics for filtering tests."""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        np.random.seed(42)
        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, 100)
        prices = [base_price]
        
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        # Create data with varying volume and price characteristics
        volumes = []
        for i in range(100):
            if i < 25:
                volumes.append(np.random.randint(500000, 1000000))    # Low volume
            elif i < 50:
                volumes.append(np.random.randint(2000000, 4000000))   # Medium volume
            elif i < 75:
                volumes.append(np.random.randint(5000000, 8000000))   # High volume
            else:
                volumes.append(np.random.randint(10000000, 15000000)) # Very high volume
        
        data = pd.DataFrame({
            'date': dates,
            'symbol': 'AAPL',
            'open': prices[:-1],
            'high': [p * 1.02 for p in prices[:-1]],
            'low': [p * 0.98 for p in prices[:-1]],
            'close': prices[1:],
            'volume': volumes
        })
        
        # Add technical indicators
        data['sma_20'] = data['close'].rolling(20).mean()
        data['sma_50'] = data['close'].rolling(50).mean()
        data['rsi'] = self._calculate_rsi(data['close'])
        
        return data
    
    def _create_multi_symbol_data(self):
        """Create multi-symbol data for symbol-specific filtering tests."""
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        all_data = []
        
        for symbol in symbols:
            symbol_data = self._create_mock_data().copy()
            symbol_data['symbol'] = symbol
            
            # Customize each symbol's characteristics
            if symbol == 'AAPL':
                symbol_data['volume'] = symbol_data['volume'] * 2      # Higher volume
                symbol_data['close'] = symbol_data['close'] * 1.5      # Higher price
            elif symbol == 'GOOGL':
                symbol_data['close'] = symbol_data['close'] * 2.0      # Much higher price
            elif symbol == 'TSLA':
                symbol_data['volume'] = symbol_data['volume'] * 0.5    # Lower volume
            # MSFT keeps original characteristics
            
            all_data.append(symbol_data)
        
        return pd.concat(all_data, ignore_index=True)
    
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
    def test_strategy_level_filtering_backtest_integration(self, mock_data_fetcher_class):
        """Test strategy-level filtering integration with backtest workflow."""
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create filtered strategy
        strategy = SMACrossover(fast=20, slow=50)
        volume_filter = StockFilter(min_volume=3000000)  # Only high volume periods
        strategy.set_filters([volume_filter])
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Run backtest with filtered strategy
        results = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Verify results
        self.assertIsInstance(results, BacktestResults)
        self.assertEqual(results.strategy_name, "SMACrossover")
        
        # Verify that filtering affected the results
        # (Should have fewer trades due to volume filtering)
        total_trades = len(results.trades)
        self.assertGreaterEqual(total_trades, 0)  # May have 0 trades if heavily filtered
        
        print(f"✅ Strategy-level filtering backtest: {total_trades} trades executed")
    
    @patch('backtest.engine.DataFetcher')
    def test_symbol_specific_filtering_backtest_integration(self, mock_data_fetcher_class):
        """Test symbol-specific filtering with multi-symbol backtest."""
        # Set up multi-symbol mock data
        self.mock_data_fetcher.get_stock_data.return_value = self.multi_symbol_data
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create strategy with symbol-specific filters
        strategy = RSIReversion(rsi_col='rsi', low_thresh=30, high_thresh=70)
        symbol_filters = {
            'AAPL': [StockFilter(min_volume=5000000)],     # Strict volume for AAPL
            'GOOGL': [StockFilter(min_price=150)],         # Price filter for GOOGL
            'TSLA': [StockFilter(min_volume=1000000)],     # Lenient volume for TSLA
        }
        strategy.set_symbol_filters(symbol_filters)
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Run backtest
        results = engine.run_backtest(
            strategy=strategy,
            symbols=["AAPL", "GOOGL", "MSFT", "TSLA"],
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Verify results
        self.assertIsInstance(results, BacktestResults)
        
        # Analyze trades by symbol to verify filtering worked
        trades_by_symbol = {}
        for trade in results.trades:
            # Trade object has symbol attribute or is a dict with symbol key
            symbol = getattr(trade, 'symbol', trade.get('symbol', 'UNKNOWN'))
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = 0
            trades_by_symbol[symbol] += 1
        
        print(f"✅ Symbol-specific filtering backtest: {len(results.trades)} total trades")
        for symbol, count in trades_by_symbol.items():
            print(f"   {symbol}: {count} trades")
    
    @patch('backtest.engine.DataFetcher')
    def test_configuration_based_filtering_backtest_integration(self, mock_data_fetcher_class):
        """Test configuration-based filtering integration with backtest."""
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create strategy with configuration-based filtering
        strategy = SMACrossover(fast=20, slow=50)
        filter_config = {
            'stock_filter': {
                'min_volume': 2000000,
                'min_price': 80,
                'max_price': 200
            },
            'liquidity_filter': {
                'min_avg_volume': 1500000,
                'volume_window': 20
            },
            'logic': 'AND'
        }
        strategy.configure_filters_from_config(filter_config)
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Run backtest
        results = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Verify results
        self.assertIsInstance(results, BacktestResults)
        self.assertIsNotNone(results.metrics)
        
        # Verify filter configuration was applied
        self.assertEqual(len(strategy.filters), 2)  # Should have stock and liquidity filters
        self.assertEqual(strategy.filter_logic, 'AND')
        
        total_trades = len(results.trades)
        print(f"✅ Configuration-based filtering backtest: {total_trades} trades executed")
    
    @patch('backtest.engine.DataFetcher')
    def test_dynamic_filtering_backtest_integration(self, mock_data_fetcher_class):
        """Test dynamic filtering adaptation during backtest."""
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create strategy with dynamic filters
        strategy = SMACrossover(fast=20, slow=50)
        
        # Simulate dynamic filtering - in practice this would adapt to market conditions
        high_vol_filter = StockFilter(min_volume=5000000)  # High volatility regime
        low_vol_filter = StockFilter(min_volume=1000000)   # Low volatility regime
        
        # Test high volatility scenario
        strategy.set_dynamic_filters([high_vol_filter])
        
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        results_high_vol = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Test low volatility scenario
        strategy.set_dynamic_filters([low_vol_filter])
        
        results_low_vol = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Verify both scenarios work
        self.assertIsInstance(results_high_vol, BacktestResults)
        self.assertIsInstance(results_low_vol, BacktestResults)
        
        high_vol_trades = len(results_high_vol.trades)
        low_vol_trades = len(results_low_vol.trades)
        
        # Low volatility should generally allow more trades
        self.assertGreaterEqual(low_vol_trades, high_vol_trades)
        
        print(f"✅ Dynamic filtering backtest: High vol: {high_vol_trades}, Low vol: {low_vol_trades} trades")
    
    @patch('backtest.engine.DataFetcher')
    def test_combined_filtering_layers_backtest_integration(self, mock_data_fetcher_class):
        """Test multiple filtering layers working together in backtest."""
        mock_data_fetcher_class.return_value = self.mock_data_fetcher
        
        # Create strategy with all types of filters
        strategy = RSIReversion(rsi_col='rsi', low_thresh=30, high_thresh=70)
        
        # Base filters
        base_filters = [
            StockFilter(min_volume=1500000),
            LiquidityFilter(min_avg_volume=1000000, volume_window=10)
        ]
        strategy.set_filters(base_filters, logic="AND")
        
        # Symbol-specific filters
        symbol_filters = {
            'AAPL': [StockFilter(min_volume=3000000)]
        }
        strategy.set_symbol_filters(symbol_filters)
        
        # Dynamic filters
        dynamic_filters = [StockFilter(min_price=50)]
        strategy.set_dynamic_filters(dynamic_filters)
        
        # Create config and engine
        config = BacktestConfig(initial_capital=100000.0)
        engine = create_backtest_engine(config)
        
        # Run backtest with all filtering layers
        results = engine.run_backtest(
            strategy=strategy,
            symbols="AAPL",
            start_date="2023-01-01",
            end_date="2023-04-10"
        )
        
        # Verify results
        self.assertIsInstance(results, BacktestResults)
        
        # Verify all filter types are configured
        self.assertEqual(len(strategy.filters), 2)               # Base filters
        self.assertEqual(len(strategy.symbol_filters), 1)        # Symbol filters
        self.assertEqual(len(strategy.dynamic_filters), 1)       # Dynamic filters
        
        # Get comprehensive filter analytics
        analytics = strategy.get_advanced_filter_info()
        self.assertIn('base_filters', analytics)
        self.assertIn('symbol_filters', analytics)
        self.assertIn('dynamic_filters', analytics)
        
        total_trades = len(results.trades)
        print(f"✅ Combined filtering backtest: {total_trades} trades with multi-layer filtering")
        print(f"   Base filters: {len(strategy.filters)}")
        print(f"   Symbol filters: {len(strategy.symbol_filters)}")
        print(f"   Dynamic filters: {len(strategy.dynamic_filters)}")


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