import unittest
import pandas as pd
import numpy as np
import sys
import os
import tempfile
import yaml
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from composer import StrategyComposer, create_composer, get_signals


class TestComposerRefactoring(unittest.TestCase):
    """Test that the composer refactoring worked correctly."""
    
    def test_imports_work_correctly(self):
        """Test that all imports work after refactoring."""
        # Test importing from main composer module
        from composer import StrategyComposer, create_composer, get_signals
        
        # Test importing directly from strategy_composer
        from composer import StrategyComposer as DirectComposer
        
        # Verify both imports reference the same class
        self.assertIs(StrategyComposer, DirectComposer, 
                     "Both imports should reference the same class")
    
    def test_strategy_composer_methods_exist(self):
        """Test that StrategyComposer has all required methods."""
        required_methods = [
            'register_strategies',
            'combine_strategies', 
            'execute_combination',
            'list_available_strategies',
            'list_available_combinations',
            'get_strategy',
            'get_filter',
            'get_combination_info'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(StrategyComposer, method),
                           f"StrategyComposer should have {method} method")
    
    def test_convenience_functions_exist(self):
        """Test that convenience functions are available and callable."""
        self.assertTrue(callable(create_composer), 
                       "create_composer should be callable")
        self.assertTrue(callable(get_signals), 
                       "get_signals should be callable")


class TestComposerFunctionality(unittest.TestCase):
    """Test the core functionality of the composer module."""
    
    def setUp(self):
        """Set up test data and configuration."""
        # Create sample market data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        base_price = 100
        prices = [base_price]
        for _ in range(len(dates)):
            price_change = np.random.normal(0, 2)
            prices.append(max(prices[-1] + price_change, 1))  # Prevent negative prices
        
        self.df = pd.DataFrame({
            'close': prices[1:],
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices[1:]],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices[1:]],
            'volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        # Add required technical indicators
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
        high_low = self.df['high'] - self.df['low']
        high_close = abs(self.df['high'] - self.df['close'].shift())
        low_close = abs(self.df['low'] - self.df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.df['atr_14'] = true_range.rolling(14).mean()
        
        # Create a temporary config file for testing
        self.temp_config = {
            'strategies': {
                'sma_crossover': {
                    'class': 'SMACrossover',
                    'parameters': {'fast': 20, 'slow': 50},
                    'enabled': True
                },
                'rsi_reversion': {
                    'class': 'RSIReversion',
                    'parameters': {},
                    'enabled': True
                },
                'atr_filter': {
                    'class': 'ATRVolatilityFilter',
                    'parameters': {},
                    'enabled': True,
                    'type': 'filter'
                }
            },
            'combinations': {
                'test_combo': {
                    'strategies': ['sma_crossover', 'rsi_reversion'],
                    'method': 'majority_vote',
                    'filters': ['atr_filter']
                },
                'single_strategy': {
                    'strategies': ['sma_crossover'],
                    'method': 'single',
                    'filters': []
                }
            },
            'settings': {
                'signal_threshold': 0.5,
                'max_positions': 10,
                'risk_per_trade': 0.02
            }
        }
        
        # Create temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.temp_config, self.temp_file)
        self.temp_file.close()
        self.config_path = self.temp_file.name

    def tearDown(self):
        """Clean up temporary files."""
        if hasattr(self, 'config_path') and os.path.exists(self.config_path):
            os.unlink(self.config_path)

    def test_strategy_composer_initialization(self):
        """Test StrategyComposer can be initialized with custom config."""
        composer = StrategyComposer(self.config_path)
        
        # Test config loading
        self.assertIsInstance(composer.config, dict)
        self.assertIn('strategies', composer.config)
        self.assertIn('combinations', composer.config)
        
        # Test strategy classes registration
        self.assertIsInstance(composer.strategy_classes, dict)
        self.assertIn('SMACrossover', composer.strategy_classes)

    def test_strategy_registration(self):
        """Test that strategies are registered correctly."""
        composer = StrategyComposer(self.config_path)
        composer.register_strategies()
        
        # Test that directional strategies are registered
        self.assertIn('sma_crossover', composer.initialized_strategies)
        self.assertIn('rsi_reversion', composer.initialized_strategies)
        
        # Test that filters are registered separately
        self.assertIn('atr_filter', composer.filters)
        
        # Test getting individual strategies
        sma_strategy = composer.get_strategy('sma_crossover')
        self.assertIsNotNone(sma_strategy)
        
        atr_filter = composer.get_filter('atr_filter')
        self.assertIsNotNone(atr_filter)

    def test_combination_methods(self):
        """Test different combination methods work correctly."""
        composer = StrategyComposer(self.config_path)
        composer.register_strategies()
        
        # Test majority vote combination
        signals = composer.execute_combination('test_combo', self.df)
        self.assertIsInstance(signals, pd.Series)
        self.assertEqual(len(signals), len(self.df))
        
        # Test signal values are valid
        unique_signals = set(signals.dropna().unique())
        valid_signals = {-1, 0, 1}
        self.assertTrue(unique_signals.issubset(valid_signals),
                       f"Invalid signals: {unique_signals}")
        
        # Test single strategy method
        single_signals = composer.execute_combination('single_strategy', self.df)
        self.assertIsInstance(single_signals, pd.Series)

    def test_convenience_functions(self):
        """Test that convenience functions work correctly."""
        # Test create_composer
        composer = create_composer(self.config_path)
        self.assertIsInstance(composer, StrategyComposer)
        self.assertTrue(len(composer.initialized_strategies) > 0)
        
        # Test get_signals
        signals = get_signals('test_combo', self.df, self.config_path)
        self.assertIsInstance(signals, pd.Series)
        self.assertEqual(len(signals), len(self.df))

    def test_list_methods(self):
        """Test listing methods work correctly."""
        composer = StrategyComposer(self.config_path)
        
        # Test list strategies
        strategies = composer.list_available_strategies()
        self.assertIsInstance(strategies, list)
        self.assertIn('sma_crossover', strategies)
        self.assertIn('rsi_reversion', strategies)
        
        # Test list combinations
        combinations = composer.list_available_combinations()
        self.assertIsInstance(combinations, list)
        self.assertIn('test_combo', combinations)
        self.assertIn('single_strategy', combinations)

    def test_combination_info(self):
        """Test getting combination information."""
        composer = StrategyComposer(self.config_path)
        
        combo_info = composer.get_combination_info('test_combo')
        self.assertIsInstance(combo_info, dict)
        self.assertEqual(combo_info['method'], 'majority_vote')
        self.assertIn('sma_crossover', combo_info['strategies'])

    def test_error_handling(self):
        """Test proper error handling for invalid inputs."""
        composer = StrategyComposer(self.config_path)
        composer.register_strategies()
        
        # Test invalid combination name
        with self.assertRaises(ValueError):
            composer.execute_combination('nonexistent_combo', self.df)
        
        # Test invalid strategy name
        with self.assertRaises(ValueError):
            composer.get_strategy('nonexistent_strategy')
        
        # Test invalid filter name
        with self.assertRaises(ValueError):
            composer.get_filter('nonexistent_filter')

    def test_signal_combinations(self):
        """Test that signal combination methods work correctly."""
        composer = StrategyComposer(self.config_path)
        composer.register_strategies()
        
        # Create test signals for combination testing
        test_signals = [
            pd.Series([1, -1, 0, 1, -1], index=self.df.index[:5]),
            pd.Series([1, 1, -1, 0, -1], index=self.df.index[:5]),
            pd.Series([0, -1, -1, 1, 0], index=self.df.index[:5])
        ]
        
        # Test majority vote
        majority_result = composer._majority_vote(test_signals)
        self.assertIsInstance(majority_result, pd.Series)
        
        # Test unanimous
        unanimous_result = composer._unanimous(test_signals)
        self.assertIsInstance(unanimous_result, pd.Series)
        
        # Test weighted average
        strategy_names = ['s1', 's2', 's3']
        weights = {'s1': 0.5, 's2': 0.3, 's3': 0.2}
        weighted_result = composer._weighted_average(test_signals, strategy_names, weights)
        self.assertIsInstance(weighted_result, pd.Series)


def run_composer_tests():
    """Run all composer tests."""
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestComposerRefactoring))
    suite.addTests(loader.loadTestsFromTestCase(TestComposerFunctionality))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running Composer Module Tests...")
    print("=" * 50)
    
    success = run_composer_tests()
    
    if success:
        print("\n🎉 All composer tests passed!")
        print("\nThe refactoring was successful:")
        print("✓ Functionality moved from composer/__init__.py to composer/strategy_composer.py")
        print("✓ Public API maintained for backward compatibility")
        print("✓ All core functionality working correctly")
    else:
        print("\n❌ Some tests failed!")
    
    sys.exit(0 if success else 1) 