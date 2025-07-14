import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path to import strategies
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies import (
    ATRVolatilityFilter, BollingerBounce, MACDCross, 
    RSIReversion, SMACrossover, get_all_strategies
)
from filters import StockFilter, TimeFilter, LiquidityFilter, CompositeFilter


class TestStrategiesBasic(unittest.TestCase):
    """Basic tests for all strategies - format and interface validation."""
    
    def setUp(self):
        """Create sample data with all required columns."""
        np.random.seed(42)  # For reproducible tests
        
        # Create basic price data
        base_price = 100
        n_periods = 100
        returns = np.random.normal(0.001, 0.02, n_periods)
        prices = [base_price]
        
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        dates = pd.date_range('2023-01-01', periods=n_periods, freq='D')
        
        self.df = pd.DataFrame({
            'date': dates,
            'close': prices[1:],
            'high': np.array(prices[1:]) * (1 + np.random.uniform(0, 0.01, n_periods)),
            'low': np.array(prices[1:]) * (1 - np.random.uniform(0, 0.01, n_periods)),
            'volume': np.random.randint(1000000, 10000000, n_periods)
        })
        
        # Add technical indicators
        self.df['sma_20'] = self.df['close'].rolling(20).mean()
        self.df['sma_50'] = self.df['close'].rolling(50).mean()
        
        # RSI calculation
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        self.df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD calculation
        ema_12 = self.df['close'].ewm(span=12).mean()
        ema_26 = self.df['close'].ewm(span=26).mean()
        self.df['macd'] = ema_12 - ema_26
        self.df['macd_signal'] = self.df['macd'].ewm(span=9).mean()
        
        # Bollinger Bands
        bb_mean = self.df['close'].rolling(20).mean()
        bb_std = self.df['close'].rolling(20).std()
        self.df['bb_upper_20'] = bb_mean + (2 * bb_std)
        self.df['bb_lower_20'] = bb_mean - (2 * bb_std)
        
        # ATR calculation
        self.df['tr'] = np.maximum.reduce([
            self.df['high'] - self.df['low'],
            np.abs(self.df['high'] - self.df['close'].shift(1)),
            np.abs(self.df['low'] - self.df['close'].shift(1))
        ])
        self.df['atr_14'] = self.df['tr'].rolling(14).mean()
        
        self.df.set_index('date', inplace=True)

    def _test_signal_format(self, strategy, strategy_name, expected_values=None):
        """Helper method to test signal format consistency."""
        if expected_values is None:
            expected_values = {-1, 0, 1}
        
        signals = strategy.generate_signals(self.df)
        
        # Test return type
        self.assertIsInstance(signals, pd.Series, 
                            f"{strategy_name} should return pd.Series")
        
        # Test signal values
        unique_signals = set(signals.dropna().unique())
        self.assertTrue(unique_signals.issubset(expected_values), 
                       f"{strategy_name} invalid signals {unique_signals}, expected subset of {expected_values}")
        
        # Test length
        self.assertEqual(len(signals), len(self.df), 
                        f"{strategy_name} signal length mismatch")
        
        return signals

    def test_atr_volatility_filter_format(self):
        """Test ATR filter returns proper format (0, 1 only)."""
        strat = ATRVolatilityFilter(atr_col="atr_14", window=50)
        signals = self._test_signal_format(strat, "ATRVolatilityFilter", {0, 1})
        
        # Additional ATR-specific tests
        rolling_mean = self.df['atr_14'].rolling(50).mean()
        high_vol = self.df['atr_14'] > rolling_mean
        
        # Test logic alignment (excluding NaN periods)
        valid_data = ~(self.df['atr_14'].isna() | rolling_mean.isna())
        expected_signals = high_vol[valid_data].astype(int)
        actual_signals = signals[valid_data]
        
        pd.testing.assert_series_equal(expected_signals, actual_signals, 
                                     check_names=False)

    def test_bollinger_bounce_format(self):
        """Test Bollinger Bands strategy format and logic."""
        strat = BollingerBounce(bb_window=20)
        signals = self._test_signal_format(strat, "BollingerBounce")
        
        # Test logic alignment
        below_lower = self.df['close'] < self.df['bb_lower_20']
        above_upper = self.df['close'] > self.df['bb_upper_20']
        
        # Check specific conditions
        valid_data = ~(self.df['bb_lower_20'].isna() | self.df['bb_upper_20'].isna())
        
        buy_signals = signals == 1
        sell_signals = signals == -1
        
        # Verify buy signals match price below lower band
        self.assertTrue((below_lower[valid_data] == buy_signals[valid_data]).all(),
                       "Buy signals should match price below lower band")
        
        # Verify sell signals match price above upper band  
        self.assertTrue((above_upper[valid_data] == sell_signals[valid_data]).all(),
                       "Sell signals should match price above upper band")

    def test_macd_cross_format(self):
        """Test MACD crossover strategy format and logic."""
        strat = MACDCross(macd_col="macd", signal_col="macd_signal")
        signals = self._test_signal_format(strat, "MACDCross")
        
        # Test crossover logic by creating simple crossover data
        test_df = pd.DataFrame({
            'macd': [1, 2, 3, 2, 1, 2, 3, 4],
            'macd_signal': [2, 2, 2, 2, 2, 2, 2, 2]
        })
        
        test_signals = strat.generate_signals(test_df)
        
        # Should have bullish crossover at index 2 (1->3 crosses above 2)
        # Should have bearish crossover at index 4 (3->1 crosses below 2)
        expected_crossovers = pd.Series([0, 0, 1, 0, -1, 0, 1, 0])
        
        pd.testing.assert_series_equal(test_signals, expected_crossovers, 
                                     check_names=False)

    def test_rsi_reversion_format(self):
        """Test RSI reversion strategy format and thresholds."""
        strat = RSIReversion(rsi_col="rsi_14", low_thresh=30, high_thresh=70)
        signals = self._test_signal_format(strat, "RSIReversion")
        
        # Test threshold logic
        buy_conditions = self.df['rsi_14'] < 30
        sell_conditions = self.df['rsi_14'] > 70
        
        actual_buys = signals == 1
        actual_sells = signals == -1
        
        # Check logic alignment (excluding NaN periods)
        valid_data = ~self.df['rsi_14'].isna()
        
        self.assertTrue((buy_conditions[valid_data] == actual_buys[valid_data]).all(),
                       "Buy signals should match RSI < 30")
        self.assertTrue((sell_conditions[valid_data] == actual_sells[valid_data]).all(),
                       "Sell signals should match RSI > 70")

    def test_sma_crossover_format(self):
        """Test SMA crossover strategy format and crossover detection."""
        strat = SMACrossover(fast=20, slow=50)
        signals = self._test_signal_format(strat, "SMACrossover")
        
        # Test with simple crossover data
        test_df = pd.DataFrame({
            'sma_20': [10, 11, 12, 11, 10, 11, 12, 13],
            'sma_50': [11, 11, 11, 11, 11, 11, 11, 11]
        })
        
        test_signals = strat.generate_signals(test_df)
        
        # Should have bullish crossover at index 2 (10->12 crosses above 11)
        # Should have bearish crossover at index 4 (11->10 crosses below 11)
        expected = pd.Series([0, 0, 1, 0, -1, 0, 1, 0])
        
        pd.testing.assert_series_equal(test_signals, expected, check_names=False)

    def test_strategy_registry_integration(self):
        """Test that all strategies in registry work with sample data."""
        strategies = get_all_strategies()
        self.assertGreater(len(strategies), 0, "Strategy registry should return strategies")
        
        for strategy in strategies:
            strategy_name = type(strategy).__name__
            with self.subTest(strategy=strategy_name):
                try:
                    signals = strategy.generate_signals(self.df)
                    self.assertIsInstance(signals, pd.Series, 
                                        f"{strategy_name} should return pd.Series")
                    self.assertEqual(len(signals), len(self.df),
                                   f"{strategy_name} should return same length as input")
                except Exception as e:
                    self.fail(f"{strategy_name} failed to generate signals: {e}")


class TestStrategiesDetailed(unittest.TestCase):
    """Detailed tests for strategy-specific logic and edge cases."""
    
    def setUp(self):
        """Create more specific test data for detailed testing."""
        # Create data with known patterns
        self.crossover_data = pd.DataFrame({
            'sma_20': [10, 10, 11, 12, 13, 12, 11, 10, 9, 10, 11, 12],
            'sma_50': [11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11],
            'close': [100] * 12,
            'macd': [-1, -0.5, 0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0, 0.5],
            'macd_signal': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'rsi_14': [25, 35, 45, 55, 65, 75, 65, 25, 35, 75, 45, 55],
            'bb_lower_20': [95] * 12,
            'bb_upper_20': [105] * 12,
            'atr_14': [1, 2, 1, 3, 2, 4, 3, 5, 4, 2, 1, 3]
        })
        
        # Add extreme price data for Bollinger testing
        self.crossover_data.loc[[1, 7], 'close'] = 90  # Below lower band
        self.crossover_data.loc[[3, 9], 'close'] = 110  # Above upper band

    def test_sma_crossover_detects_actual_crossovers(self):
        """Test that SMA crossover only signals on actual crossovers, not levels."""
        strat = SMACrossover(fast=20, slow=50)
        signals = strat.generate_signals(self.crossover_data)
        
        # Expected crossovers:
        # Index 3: fast crosses above slow (11->12 crosses above 11)
        # Index 7: fast crosses below slow (11->10 crosses below 11)  
        # Index 11: fast crosses above slow (11->12 crosses above 11)
        expected_signals = [0, 0, 0, 1, 0, 0, 0, -1, 0, 0, 0, 1]
        
        actual_signals = signals.tolist()
        self.assertEqual(actual_signals, expected_signals,
                        "SMA crossover should only signal on actual crossovers")
        
        # Verify total number of signals is reasonable (not constant signaling)
        total_signals = abs(signals).sum()
        self.assertLessEqual(total_signals, 6, 
                           "Should have limited crossover signals, not constant signaling")

    def test_macd_crossover_precision(self):
        """Test MACD crossover detection with precise data."""
        strat = MACDCross()
        signals = strat.generate_signals(self.crossover_data)
        
        # Expected MACD crossovers based on test data:
        # Index 2: MACD crosses above signal (0 > 0, but this is equality edge case)
        # Index 6: MACD crosses below signal (0 < 0, equality edge case)
        # Index 10: MACD crosses above signal (0 > 0, equality edge case)
        
        # Count actual crossovers
        crossover_count = (signals != 0).sum()
        self.assertGreaterEqual(crossover_count, 1, 
                               "Should detect at least one MACD crossover")
        self.assertLessEqual(crossover_count, 6,
                           "Should not have excessive crossover signals")

    def test_edge_cases_with_nan_data(self):
        """Test strategies handle NaN data gracefully."""
        # Create data with NaN values
        nan_data = self.crossover_data.copy()
        nan_data.loc[0:2, 'sma_20'] = np.nan
        nan_data.loc[0:2, 'rsi_14'] = np.nan
        
        strategies = [
            SMACrossover(fast=20, slow=50),
            RSIReversion(),
            MACDCross(),
            BollingerBounce(),
            ATRVolatilityFilter(atr_col="atr_14", window=3)
        ]
        
        for strategy in strategies:
            strategy_name = type(strategy).__name__
            with self.subTest(strategy=strategy_name):
                signals = strategy.generate_signals(nan_data)
                
                # Should return a series of the same length
                self.assertEqual(len(signals), len(nan_data))
                
                # Should not raise exceptions
                self.assertIsInstance(signals, pd.Series)

    def test_bollinger_bands_extreme_values(self):
        """Test Bollinger Bands with price extremes."""
        strat = BollingerBounce(bb_window=20)
        signals = strat.generate_signals(self.crossover_data)
        
        # Check specific extreme value responses
        # Indices 1, 7 have close=90 (below lower band of 95) -> should be 1
        # Indices 3, 9 have close=110 (above upper band of 105) -> should be -1
        
        self.assertEqual(signals.iloc[1], 1, "Price below lower band should generate buy signal")
        self.assertEqual(signals.iloc[7], 1, "Price below lower band should generate buy signal")
        self.assertEqual(signals.iloc[3], -1, "Price above upper band should generate sell signal")
        self.assertEqual(signals.iloc[9], -1, "Price above upper band should generate sell signal")


class TestAdvancedFiltering(unittest.TestCase):
    """Test advanced filtering capabilities added to the base Strategy class."""
    
    def setUp(self):
        """Create sample data for filtering tests."""
        np.random.seed(42)  # For reproducible tests
        
        # Create multi-symbol data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY']
        
        data = []
        for symbol in symbols:
            symbol_data = pd.DataFrame({
                'date': dates,
                'symbol': symbol,
                'close': np.random.uniform(100, 200, 100),
                'volume': np.random.uniform(1000000, 10000000, 100),
                'high': np.random.uniform(200, 250, 100),
                'low': np.random.uniform(50, 100, 100)
            })
            data.append(symbol_data)
        
        self.multi_symbol_df = pd.concat(data, ignore_index=True)
        
        # Create single symbol data with technical indicators
        self.single_symbol_df = pd.DataFrame({
            'date': dates,
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.uniform(1000000, 10000000, 100),
            'high': np.random.uniform(200, 250, 100),
            'low': np.random.uniform(50, 100, 100)
        })
        
        # Add required technical indicators
        self.single_symbol_df['sma_10'] = self.single_symbol_df['close'].rolling(10).mean()
        self.single_symbol_df['sma_20'] = self.single_symbol_df['close'].rolling(20).mean()
        self.single_symbol_df['rsi_14'] = np.random.uniform(10, 90, 100)
        
        # Strategy for testing
        self.strategy = SMACrossover(fast=10, slow=20)
        
    def test_basic_filtering_methods(self):
        """Test basic filtering methods: set_filters, add_filter."""
        # Test set_filters
        volume_filter = StockFilter(min_volume=2000000)
        price_filter = StockFilter(min_price=120)
        
        self.strategy.set_filters([volume_filter, price_filter], logic="AND")
        
        self.assertEqual(len(self.strategy.filters), 2)
        self.assertEqual(self.strategy.filter_logic, "AND")
        
        # Test add_filter
        liquidity_filter = LiquidityFilter(min_avg_volume=1500000)
        self.strategy.add_filter(liquidity_filter)
        
        self.assertEqual(len(self.strategy.filters), 3)
        
        # Test filter info
        filter_info = self.strategy.get_filter_info()
        self.assertEqual(filter_info['filter_count'], 3)
        self.assertEqual(filter_info['logic'], 'AND')
        
    def test_symbol_specific_filtering(self):
        """Test symbol-specific filtering methods."""
        # Test set_symbol_filters
        symbol_filters = {
            'AAPL': [StockFilter(min_volume=5000000)],
            'GOOGL': [StockFilter(min_price=150)],
            'MSFT': [StockFilter(max_price=180)]
        }
        
        self.strategy.set_symbol_filters(symbol_filters)
        
        self.assertEqual(len(self.strategy.symbol_filters), 3)
        self.assertIn('AAPL', self.strategy.symbol_filters)
        self.assertIn('GOOGL', self.strategy.symbol_filters)
        self.assertIn('MSFT', self.strategy.symbol_filters)
        
        # Test add_symbol_filter
        self.strategy.add_symbol_filter('TSLA', StockFilter(min_volume=3000000))
        
        self.assertEqual(len(self.strategy.symbol_filters), 4)
        self.assertIn('TSLA', self.strategy.symbol_filters)
        
    def test_dynamic_filtering(self):
        """Test dynamic filtering methods."""
        # Test set_dynamic_filters
        dynamic_filters = [
            StockFilter(min_volume=2000000),
            TimeFilter(exclude_market_holidays=True)
        ]
        
        self.strategy.set_dynamic_filters(dynamic_filters)
        
        self.assertEqual(len(self.strategy.dynamic_filters), 2)
        
    def test_configuration_based_filtering(self):
        """Test configuration-based filtering from config dict."""
        filter_config = {
            'stock_filter': {
                'min_volume': 1500000,
                'min_price': 50,
                'max_price': 300
            },
            'time_filter': {
                'exclude_market_holidays': True,
                'min_trading_days': 20
            },
            'liquidity_filter': {
                'min_avg_volume': 1000000,
                'volume_window': 20
            },
            'logic': 'AND'
        }
        
        self.strategy.configure_filters_from_config(filter_config)
        
        # Should have created 3 filters
        self.assertEqual(len(self.strategy.filters), 3)
        self.assertEqual(self.strategy.filter_logic, 'AND')
        
        # Should have stored config
        self.assertEqual(self.strategy.filter_config, filter_config)
        
    def test_generate_signals_with_filters(self):
        """Test basic signal generation with filters."""
        # Add a simple filter
        volume_filter = StockFilter(min_volume=2000000)
        self.strategy.set_filters([volume_filter])
        
        # Generate signals with filters
        signals = self.strategy.generate_signals_with_filters(self.single_symbol_df)
        
        # Should return a pandas Series
        self.assertIsInstance(signals, pd.Series)
        
        # Should have same length as input
        self.assertEqual(len(signals), len(self.single_symbol_df))
        
        # Should contain valid signal values
        unique_signals = set(signals.unique())
        self.assertTrue(unique_signals.issubset({-1, 0, 1}))
        
    def test_generate_signals_with_advanced_filters(self):
        """Test advanced signal generation with multi-level filtering."""
        # Set up all types of filters
        base_filter = StockFilter(min_volume=1000000)
        self.strategy.set_filters([base_filter])
        
        symbol_filters = {
            'AAPL': [StockFilter(min_volume=2000000)]
        }
        self.strategy.set_symbol_filters(symbol_filters)
        
        dynamic_filters = [StockFilter(min_price=100)]
        self.strategy.set_dynamic_filters(dynamic_filters)
        
        # Generate signals with advanced filters
        signals = self.strategy.generate_signals_with_advanced_filters(self.single_symbol_df)
        
        # Should return a pandas Series
        self.assertIsInstance(signals, pd.Series)
        
        # Should have same length as input
        self.assertEqual(len(signals), len(self.single_symbol_df))
        
        # Should contain valid signal values
        unique_signals = set(signals.unique())
        self.assertTrue(unique_signals.issubset({-1, 0, 1}))
        
    def test_filter_validation(self):
        """Test filter validation functionality."""
        # Create a custom strategy with filter requirements
        class TestStrategy(SMACrossover):
            def get_filter_requirements(self):
                return {
                    "required": ["StockFilter"],
                    "optional": ["TimeFilter", "LiquidityFilter"]
                }
        
        test_strategy = TestStrategy(fast=10, slow=20)
        
        # Should fail validation initially (no required filters)
        self.assertFalse(test_strategy.validate_filters())
        
        # Add required filter
        test_strategy.add_filter(StockFilter(min_volume=1000000))
        
        # Should pass validation now
        self.assertTrue(test_strategy.validate_filters())
        
    def test_filter_analytics(self):
        """Test comprehensive filter analytics."""
        # Set up complex filter configuration
        self.strategy.set_filters([StockFilter(min_volume=1000000)])
        
        self.strategy.set_symbol_filters({
            'AAPL': [StockFilter(min_volume=2000000)],
            'GOOGL': [StockFilter(min_price=150)]
        })
        
        self.strategy.set_dynamic_filters([TimeFilter(exclude_market_holidays=True)])
        
        # Test basic filter info
        basic_info = self.strategy.get_filter_info()
        self.assertEqual(basic_info['filter_count'], 1)
        self.assertEqual(basic_info['logic'], 'AND')
        
        # Test advanced filter info
        advanced_info = self.strategy.get_advanced_filter_info()
        
        self.assertIn('base_filters', advanced_info)
        self.assertIn('symbol_filters', advanced_info)
        self.assertIn('dynamic_filters', advanced_info)
        
        # Should have correct counts
        self.assertEqual(len(advanced_info['symbol_filters']), 2)
        self.assertEqual(len(advanced_info['dynamic_filters']), 1)
        
    def test_filter_requirements_default(self):
        """Test default filter requirements implementation."""
        requirements = self.strategy.get_filter_requirements()
        
        # Default implementation should return empty requirements
        self.assertEqual(requirements['required'], [])
        self.assertEqual(requirements['optional'], [])
        
    def test_empty_filter_handling(self):
        """Test that strategies handle empty filters gracefully."""
        # Test with no filters
        signals = self.strategy.generate_signals_with_filters(self.single_symbol_df)
        self.assertEqual(len(signals), len(self.single_symbol_df))
        
        # Test advanced signals with no filters
        advanced_signals = self.strategy.generate_signals_with_advanced_filters(self.single_symbol_df)
        self.assertEqual(len(advanced_signals), len(self.single_symbol_df))
        
        # Both should be equivalent when no filters are applied
        pd.testing.assert_series_equal(signals, advanced_signals, check_names=False)
        
    def test_filter_logic_combination(self):
        """Test AND/OR logic combinations."""
        # Test AND logic
        self.strategy.set_filters([
            StockFilter(min_volume=1000000),
            StockFilter(min_price=100)
        ], logic="AND")
        
        self.assertEqual(self.strategy.filter_logic, "AND")
        
        # Test OR logic
        self.strategy.set_filters([
            StockFilter(min_volume=1000000),
            StockFilter(min_price=100)
        ], logic="OR")
        
        self.assertEqual(self.strategy.filter_logic, "OR")
        
    def test_filter_persistence(self):
        """Test that filter configurations persist correctly."""
        # Set up filters
        original_filters = [StockFilter(min_volume=1000000)]
        self.strategy.set_filters(original_filters)
        
        # Filters should persist
        self.assertEqual(len(self.strategy.filters), 1)
        
        # Add more filters
        self.strategy.add_filter(StockFilter(min_price=100))
        
        # Should have both filters
        self.assertEqual(len(self.strategy.filters), 2)
        
    def test_all_strategies_have_filter_methods(self):
        """Test that all strategy classes have the new filter methods."""
        strategies = [
            SMACrossover(fast=10, slow=20),
            RSIReversion(rsi_col="rsi_14", low_thresh=30, high_thresh=70),
            MACDCross(macd_col="macd", signal_col="macd_signal"),
            BollingerBounce(bb_window=20),
            ATRVolatilityFilter(atr_col="atr_14", window=50)
        ]
        
        required_methods = [
            'set_filters', 'add_filter', 'set_symbol_filters', 'add_symbol_filter',
            'set_dynamic_filters', 'configure_filters_from_config',
            'generate_signals_with_filters', 'generate_signals_with_advanced_filters',
            'get_filter_info', 'get_advanced_filter_info', 'validate_filters',
            'get_filter_requirements'
        ]
        
        for strategy in strategies:
            strategy_name = type(strategy).__name__
            for method_name in required_methods:
                with self.subTest(strategy=strategy_name, method=method_name):
                    self.assertTrue(hasattr(strategy, method_name),
                                  f"{strategy_name} should have {method_name} method")
                    
    def test_filter_edge_cases(self):
        """Test edge cases in filtering."""
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        self.strategy.set_filters([StockFilter(min_volume=1000000)])
        
        signals = self.strategy.generate_signals_with_filters(empty_df)
        self.assertEqual(len(signals), 0)
        
        # Test with DataFrame that gets completely filtered out
        filtered_out_df = pd.DataFrame({
            'close': [50, 60, 70],
            'volume': [100, 200, 300],  # Very low volume
            'sma_10': [55, 65, 75],
            'sma_20': [60, 70, 80]
        })
        
        high_volume_filter = StockFilter(min_volume=1000000)
        self.strategy.set_filters([high_volume_filter])
        
        signals = self.strategy.generate_signals_with_filters(filtered_out_df)
        
        # Should return all zeros when everything is filtered out
        self.assertTrue((signals == 0).all())


def run_all_tests():
    """Run all strategy tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestStrategiesBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategiesDetailed))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedFiltering))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run comprehensive tests
    print("🧪 COMPREHENSIVE STRATEGY TESTING")
    print("=" * 60)
    
    success = run_all_tests()
    
    if success:
        print("\n🎉 ALL STRATEGY TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED - Check output above")
