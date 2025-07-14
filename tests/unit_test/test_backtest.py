#!/usr/bin/env python3
"""
Unit tests for the backtest module.

This module contains unit tests for individual backtest components:
- BacktestConfig and BacktestConfigManager
- Portfolio management
- Performance metrics calculations
- Filtering system
- Results handling
- Engine core functionality
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import yaml

# Add project root to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import BacktestConfig, BacktestConfigManager
from backtest.portfolio import Portfolio, Position
from backtest.metrics import PerformanceMetrics, calculate_performance_metrics
from filters import StockFilter, TimeFilter, LiquidityFilter, CompositeFilter
from backtest.results import BacktestResults
from backtest.engine import BacktestEngine


class TestBacktestConfig(unittest.TestCase):
    """Test BacktestConfig dataclass functionality."""
    
    def test_default_config_creation(self):
        """Test creating a config with default values."""
        config = BacktestConfig()
        self.assertEqual(config.initial_capital, 100000.0)
        self.assertEqual(config.commission_rate, 0.0005)
        self.assertEqual(config.max_position_size, 0.25)
        self.assertEqual(config.benchmark_symbol, "SPY")
    
    def test_custom_config_creation(self):
        """Test creating a config with custom values."""
        config = BacktestConfig(
            initial_capital=50000.0,
            commission_rate=0.001,
            max_position_size=0.1,
            benchmark_symbol="QQQ"
        )
        self.assertEqual(config.initial_capital, 50000.0)
        self.assertEqual(config.commission_rate, 0.001)
        self.assertEqual(config.max_position_size, 0.1)
        self.assertEqual(config.benchmark_symbol, "QQQ")
    
    def test_config_validation_positive_capital(self):
        """Test that negative capital raises error."""
        with self.assertRaises(ValueError):
            BacktestConfig(initial_capital=-1000.0)
    
    def test_config_validation_commission_rate(self):
        """Test commission rate validation."""
        with self.assertRaises(ValueError):
            BacktestConfig(commission_rate=-0.001)
        
        with self.assertRaises(ValueError):
            BacktestConfig(commission_rate=0.15)  # 15% is too high
    
    def test_config_validation_position_size(self):
        """Test position size validation."""
        with self.assertRaises(ValueError):
            BacktestConfig(max_position_size=0.0)
        
        with self.assertRaises(ValueError):
            BacktestConfig(max_position_size=1.5)  # > 100%
    
    def test_config_validation_position_sizing_method(self):
        """Test position sizing method validation."""
        with self.assertRaises(ValueError):
            BacktestConfig(position_sizing_method="invalid_method")
        
        # Valid methods should work
        valid_methods = ["equal_weight", "kelly", "fixed_dollar"]
        for method in valid_methods:
            config = BacktestConfig(position_sizing_method=method)
            self.assertEqual(config.position_sizing_method, method)
    
    def test_config_validation_drawdown_limit(self):
        """Test drawdown limit validation."""
        with self.assertRaises(ValueError):
            BacktestConfig(max_drawdown_limit=0.02)  # Too low
        
        with self.assertRaises(ValueError):
            BacktestConfig(max_drawdown_limit=0.98)  # Too high
        
        # Valid values should work
        config = BacktestConfig(max_drawdown_limit=0.2)
        self.assertEqual(config.max_drawdown_limit, 0.2)


class TestBacktestConfigManager(unittest.TestCase):
    """Test BacktestConfigManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary config file
        self.test_config = {
            'default': {
                'initial_capital': 100000.0,
                'commission_rate': 0.0005,
                'max_position_size': 0.25,
                'benchmark_symbol': 'SPY'
            },
            'configurations': {
                'test_config': {
                    'initial_capital': 50000.0,
                    'commission_rate': 0.001,
                    'max_position_size': 0.1
                }
            },
            'validation': {
                'initial_capital': {'min': 1000.0, 'max': 10000000.0},
                'commission_rate': {'min': 0.0, 'max': 0.1}
            }
        }
        
        # Create temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.test_config, self.temp_file)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_file.name)
    
    def test_config_manager_initialization(self):
        """Test config manager initialization."""
        manager = BacktestConfigManager(self.temp_file.name)
        self.assertIsNotNone(manager._config_data)
        self.assertEqual(manager._config_data['default']['initial_capital'], 100000.0)
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        manager = BacktestConfigManager(self.temp_file.name)
        config = manager.get_config("default")
        self.assertEqual(config.initial_capital, 100000.0)
        self.assertEqual(config.commission_rate, 0.0005)
    
    def test_get_named_config(self):
        """Test getting named configuration."""
        manager = BacktestConfigManager(self.temp_file.name)
        config = manager.get_config("test_config")
        self.assertEqual(config.initial_capital, 50000.0)
        self.assertEqual(config.commission_rate, 0.001)
        self.assertEqual(config.benchmark_symbol, "SPY")  # Should inherit from default
    
    def test_get_nonexistent_config(self):
        """Test getting non-existent configuration."""
        manager = BacktestConfigManager(self.temp_file.name)
        with self.assertRaises(ValueError):
            manager.get_config("nonexistent")
    
    def test_list_available_configs(self):
        """Test listing available configurations."""
        manager = BacktestConfigManager(self.temp_file.name)
        configs = manager.list_available_configs()
        self.assertIn("default", configs)
        self.assertIn("test_config", configs)
    
    def test_create_custom_config(self):
        """Test creating custom configuration."""
        manager = BacktestConfigManager(self.temp_file.name)
        custom_config = manager.create_custom_config(
            base_config="default",
            initial_capital=200000.0,
            commission_rate=0.0003
        )
        self.assertEqual(custom_config.initial_capital, 200000.0)
        self.assertEqual(custom_config.commission_rate, 0.0003)
    
    def test_config_validation(self):
        """Test configuration validation."""
        manager = BacktestConfigManager(self.temp_file.name)
        
        # Valid config should pass
        valid_config = BacktestConfig(initial_capital=50000.0, commission_rate=0.001)
        self.assertTrue(manager.validate_config(valid_config))
        
        # Invalid config should fail
        invalid_config = BacktestConfig(initial_capital=500.0)  # Below minimum
        with self.assertRaises(ValueError):
            manager.validate_config(invalid_config)


class TestPosition(unittest.TestCase):
    """Test Position class functionality."""
    
    def test_position_creation(self):
        """Test position creation."""
        position = Position("AAPL", 100, 150.0)
        self.assertEqual(position.symbol, "AAPL")
        self.assertEqual(position.quantity, 100)
        self.assertEqual(position.avg_price, 150.0)
        self.assertEqual(position.current_price, 0.0)  # Default
    
    def test_position_pnl_calculation(self):
        """Test P&L calculation."""
        position = Position("AAPL", 100, 150.0)
        position.update_price(160.0)  # Update to new price
        
        pnl = position.get_total_pnl()
        expected_pnl = (160.0 - 150.0) * 100  # 10 * 100 = 1000
        self.assertEqual(pnl, expected_pnl)
    
    def test_position_market_value(self):
        """Test market value calculation."""
        position = Position("AAPL", 100, 150.0)
        position.update_price(165.0)  # 10% gain
        
        market_value = position.get_market_value()
        expected_value = 165.0 * 100  # 16500
        self.assertEqual(market_value, expected_value)
    
    def test_position_update_price(self):
        """Test updating position price."""
        position = Position("AAPL", 100, 150.0)
        position.update_price(160.0)
        self.assertEqual(position.current_price, 160.0)
        self.assertEqual(position.unrealized_pnl, 1000.0)  # (160-150) * 100


class TestPortfolio(unittest.TestCase):
    """Test Portfolio class functionality."""
    
    def setUp(self):
        """Set up test portfolio."""
        self.portfolio = Portfolio(initial_capital=100000.0, commission_rate=0.001)
    
    def test_portfolio_initialization(self):
        """Test portfolio initialization."""
        self.assertEqual(self.portfolio.cash, 100000.0)
        self.assertEqual(self.portfolio.commission_rate, 0.001)
        self.assertEqual(len(self.portfolio.positions), 0)
    
    def test_buy_stock(self):
        """Test buying stock."""
        timestamp = datetime.now()
        success = self.portfolio.buy("AAPL", 100, 150.0, timestamp)
        
        # Check trade was successful
        self.assertTrue(success)
        
        # Check position created
        self.assertIn("AAPL", self.portfolio.positions)
        position = self.portfolio.positions["AAPL"]
        self.assertEqual(position.quantity, 100)
        self.assertEqual(position.avg_price, 150.0)
        
        # Check cash reduced (including commission)
        expected_cash = 100000.0 - (100 * 150.0) - (100 * 150.0 * 0.001) - (100 * 150.0 * 0.0005)
        self.assertAlmostEqual(self.portfolio.cash, expected_cash, places=2)
    
    def test_sell_stock(self):
        """Test selling stock."""
        timestamp = datetime.now()
        
        # First buy
        self.portfolio.buy("AAPL", 100, 150.0, timestamp)
        initial_cash = self.portfolio.cash
        
        # Then sell
        success = self.portfolio.sell("AAPL", 50, 160.0, timestamp)
        
        # Check trade was successful
        self.assertTrue(success)
        
        # Check position updated
        position = self.portfolio.positions["AAPL"]
        self.assertEqual(position.quantity, 50)
        
        # Check cash increased
        expected_cash_increase = (50 * 160.0) - (50 * 160.0 * 0.001) - (50 * 160.0 * 0.0005)
        expected_cash = initial_cash + expected_cash_increase
        self.assertAlmostEqual(self.portfolio.cash, expected_cash, places=2)
    
    def test_sell_all_stock(self):
        """Test selling all shares of a stock."""
        timestamp = datetime.now()
        
        self.portfolio.buy("AAPL", 100, 150.0, timestamp)
        self.portfolio.sell("AAPL", 100, 160.0, timestamp)
        
        # Position should be removed
        self.assertNotIn("AAPL", self.portfolio.positions)
    
    def test_sell_more_than_owned(self):
        """Test selling more shares than owned."""
        timestamp = datetime.now()
        
        self.portfolio.buy("AAPL", 100, 150.0, timestamp)
        
        # Try to sell more than owned
        success = self.portfolio.sell("AAPL", 150, 160.0, timestamp)
        self.assertFalse(success)
    
    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation."""
        timestamp = datetime.now()
        
        self.portfolio.buy("AAPL", 100, 150.0, timestamp)
        self.portfolio.buy("MSFT", 50, 200.0, timestamp)
        
        # Mock current prices - need 'symbol' column as the portfolio expects
        mock_data = pd.DataFrame({
            'symbol': ['AAPL', 'MSFT'],
            'close': [160.0, 220.0]
        })
        
        total_value = self.portfolio.update_portfolio_value(mock_data)
        expected_value = self.portfolio.cash + (100 * 160.0) + (50 * 220.0)
        self.assertAlmostEqual(total_value, expected_value, places=2)


class TestStockFilter(unittest.TestCase):
    """Test StockFilter functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = pd.DataFrame({
            'volume': [1000000, 500000, 2000000, 100000],
            'close': [50.0, 5.0, 100.0, 200.0],
            'volatility': [0.2, 0.6, 0.1, 0.3]
        }, index=['AAPL', 'PENNY', 'MSFT', 'GOOGL'])
    
    def test_volume_filter(self):
        """Test volume filtering."""
        filter_obj = StockFilter(min_volume=750000)
        filtered = filter_obj.apply_filter(self.test_data)
        
        # Should keep AAPL and MSFT, filter out PENNY and GOOGL
        expected_symbols = ['AAPL', 'MSFT']
        self.assertEqual(list(filtered.index), expected_symbols)
    
    def test_price_filter(self):
        """Test price filtering."""
        filter_obj = StockFilter(min_price=20.0, max_price=150.0)
        filtered = filter_obj.apply_filter(self.test_data)
        
        # Should keep AAPL and MSFT, filter out PENNY (too low) and GOOGL (too high)
        expected_symbols = ['AAPL', 'MSFT']
        self.assertEqual(list(filtered.index), expected_symbols)
    
    def test_volatility_filter(self):
        """Test volatility filtering."""
        # Need to set min_volume to 0 to include GOOGL which has low volume
        filter_obj = StockFilter(max_volatility=0.4, min_volume=0)
        filtered = filter_obj.apply_filter(self.test_data)
        
        # Should filter out PENNY (volatility 0.6)
        expected_symbols = ['AAPL', 'MSFT', 'GOOGL']
        self.assertEqual(list(filtered.index), expected_symbols)
    
    def test_exclude_symbols(self):
        """Test symbol exclusion."""
        filter_obj = StockFilter(exclude_symbols=['PENNY', 'GOOGL'], min_volume=0)
        filtered = filter_obj.apply_filter(self.test_data)
        
        expected_symbols = ['AAPL', 'MSFT']
        self.assertEqual(list(filtered.index), expected_symbols)
    
    def test_combined_filters(self):
        """Test combined filtering criteria."""
        filter_obj = StockFilter(
            min_volume=750000,
            min_price=20.0,
            max_volatility=0.4,
            exclude_symbols=['GOOGL']
        )
        filtered = filter_obj.apply_filter(self.test_data)
        
        # Should only keep AAPL and MSFT
        expected_symbols = ['AAPL', 'MSFT']
        self.assertEqual(list(filtered.index), expected_symbols)


class TestTimeFilter(unittest.TestCase):
    """Test TimeFilter functionality."""
    
    def setUp(self):
        """Set up test data."""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        self.test_data = pd.DataFrame({
            'close': range(10)
        }, index=dates)
    
    def test_basic_filter_creation(self):
        """Test basic time filter creation."""
        filter_obj = TimeFilter(min_trading_days=5)
        self.assertEqual(filter_obj.min_trading_days, 5)
    
    def test_filter_application(self):
        """Test time filter application."""
        filter_obj = TimeFilter(min_trading_days=5)
        
        # Should pass since we have 10 days > 5
        try:
            filtered = filter_obj.apply_filter(self.test_data)
            # If no exception, the test passes
            self.assertEqual(len(filtered), 10)
        except ValueError:
            self.fail("Time filter should not raise ValueError for sufficient data")
    
    def test_insufficient_data(self):
        """Test filter with insufficient data."""
        filter_obj = TimeFilter(min_trading_days=20)
        
        # Should return empty DataFrame since we only have 10 days < 20
        filtered = filter_obj.apply_filter(self.test_data)
        self.assertTrue(filtered.empty, "Should return empty DataFrame for insufficient data")
    
    def test_exclude_dates(self):
        """Test excluding specific dates."""
        filter_obj = TimeFilter(exclude_dates=['2023-01-02', '2023-01-05'])
        filtered = filter_obj.apply_filter(self.test_data)
        
        # Should have fewer rows (original - excluded)
        self.assertLess(len(filtered), len(self.test_data))


class TestCompositeFilter(unittest.TestCase):
    """Test CompositeFilter functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = pd.DataFrame({
            'volume': [1000000, 500000, 2000000],
            'close': [50.0, 5.0, 100.0],
            'volatility': [0.2, 0.6, 0.1]
        }, index=['AAPL', 'PENNY', 'MSFT'])
    
    def test_and_logic(self):
        """Test AND logic combination."""
        volume_filter = StockFilter(min_volume=750000)
        price_filter = StockFilter(min_price=20.0)
        
        composite = CompositeFilter([volume_filter, price_filter], logic="AND")
        filtered = composite.apply_filter(self.test_data)
        
        # Should only keep stocks that pass both filters
        expected_symbols = ['AAPL', 'MSFT']
        self.assertEqual(list(filtered.index), expected_symbols)
    
    def test_or_logic(self):
        """Test OR logic combination."""
        volume_filter = StockFilter(min_volume=1500000)  # Only MSFT
        price_filter = StockFilter(min_price=45.0)       # Only AAPL, MSFT
        
        composite = CompositeFilter([volume_filter, price_filter], logic="OR")
        filtered = composite.apply_filter(self.test_data)
        
        # Should keep stocks that pass either filter (order may vary)
        expected_symbols = ['AAPL', 'MSFT']
        self.assertEqual(sorted(list(filtered.index)), sorted(expected_symbols))


class TestPerformanceMetrics(unittest.TestCase):
    """Test performance metrics calculations."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample portfolio history
        dates = pd.date_range('2023-01-01', periods=252, freq='D')
        np.random.seed(42)  # For reproducible results
        
        # Generate sample returns (roughly 8% annual with 15% volatility)
        daily_returns = np.random.normal(0.08/252, 0.15/np.sqrt(252), 252)
        portfolio_values = [100000.0]
        
        for ret in daily_returns:
            portfolio_values.append(portfolio_values[-1] * (1 + ret))
        
        self.portfolio_history = pd.DataFrame({
            'total_value': portfolio_values[:-1],
            'timestamp': dates
        })
        
        # Mock benchmark data
        benchmark_returns = np.random.normal(0.1/252, 0.12/np.sqrt(252), 252)
        self.benchmark_values = [100000.0]
        for ret in benchmark_returns:
            self.benchmark_values.append(self.benchmark_values[-1] * (1 + ret))
    
    def test_total_return_calculation(self):
        """Test total return calculation."""
        metrics = calculate_performance_metrics(
            self.portfolio_history,
            risk_free_rate=0.02
        )
        
        expected_total_return = (self.portfolio_history['total_value'].iloc[-1] / self.portfolio_history['total_value'].iloc[0]) - 1
        self.assertAlmostEqual(metrics.total_return, expected_total_return, places=4)
    
    def test_volatility_calculation(self):
        """Test volatility calculation."""
        metrics = calculate_performance_metrics(
            self.portfolio_history,
            risk_free_rate=0.02
        )
        
        # Check that volatility is positive and reasonable
        self.assertGreater(metrics.annualized_volatility, 0)
        self.assertLess(metrics.annualized_volatility, 1.0)  # Should be less than 100%
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation."""
        metrics = calculate_performance_metrics(
            self.portfolio_history,
            risk_free_rate=0.02
        )
        
        # Sharpe ratio should be reasonable (can be negative)
        self.assertIsInstance(metrics.sharpe_ratio, float)
        self.assertGreater(metrics.sharpe_ratio, -5.0)
        self.assertLess(metrics.sharpe_ratio, 5.0)
    
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        metrics = calculate_performance_metrics(
            self.portfolio_history,
            risk_free_rate=0.02
        )
        
        # Max drawdown should be negative (or zero)
        self.assertLessEqual(metrics.max_drawdown, 0)
        self.assertGreater(metrics.max_drawdown, -1.0)  # Shouldn't lose more than 100%


class TestBacktestResults(unittest.TestCase):
    """Test BacktestResults functionality."""
    
    def setUp(self):
        """Set up test results."""
        # Create PerformanceMetrics with all required fields
        self.metrics = PerformanceMetrics(
            total_return=0.15,
            annualized_return=0.12,
            annualized_volatility=0.18,
            sharpe_ratio=0.8,
            sortino_ratio=0.65,
            calmar_ratio=1.2,
            max_drawdown=-0.1,
            max_drawdown_duration=30,
            value_at_risk_95=-0.02,
            conditional_var_95=-0.035,
            beta=0.95,
            total_trades=50,
            win_rate=0.6,
            profit_factor=1.4,
            avg_win=0.03,
            avg_loss=-0.02,
            benchmark_return=0.1,
            alpha=0.02,
            tracking_error=0.05,
            information_ratio=0.4,
            start_date='2023-01-01',
            end_date='2023-12-31',
            trading_days=252
        )
        
        # Create BacktestResults with all required parameters
        self.results = BacktestResults(
            strategy_name="TestStrategy",
            symbols=["AAPL", "MSFT"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            config=BacktestConfig(),
            portfolio_history=pd.DataFrame({'total_value': [100000, 115000]}),
            metrics=self.metrics,
            trades=[],
            data_info={'symbols_count': 2, 'data_points': 252}
        )
    
    def test_results_creation(self):
        """Test results object creation."""
        self.assertEqual(self.results.strategy_name, "TestStrategy")
        self.assertEqual(len(self.results.symbols), 2)
        self.assertEqual(self.results.start_date, "2023-01-01")
        self.assertEqual(self.results.end_date, "2023-12-31")
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        summary = self.results.get_performance_summary()
        
        self.assertIn("Total Return", summary['Metric'].values)
        self.assertIn("Sharpe Ratio", summary['Metric'].values)
        self.assertIn("Maximum Drawdown", summary['Metric'].values)
    
    def test_trade_analysis(self):
        """Test trade analysis."""
        # Mock some trade data
        self.results.trades = [
            {'symbol': 'AAPL', 'side': 'BUY', 'quantity': 100, 'price': 150.0, 'commission': 0.5, 'slippage': 0.1},
            {'symbol': 'AAPL', 'side': 'SELL', 'quantity': 100, 'price': 160.0, 'commission': 0.5, 'slippage': 0.1},
            {'symbol': 'MSFT', 'side': 'BUY', 'quantity': 50, 'price': 200.0, 'commission': 0.3, 'slippage': 0.05}
        ]
        
        analysis = self.results.get_trade_analysis()
        self.assertIn("total_trades", analysis)
        self.assertIn("symbols_traded", analysis)
        self.assertEqual(analysis['total_trades'], 3)


if __name__ == '__main__':
    unittest.main() 