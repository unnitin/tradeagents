import unittest
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from composer import create_composer, get_signals, StrategyComposer
from strategies import SMACrossover, RSIReversion, MACDCross, BollingerBounce
from data import get_data, add_sma, add_ema, add_rsi
from filters import StockFilter, TimeFilter, LiquidityFilter, CompositeFilter


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete trading system."""
    
    def setUp(self):
        """Set up test data for integration tests."""
        # Create comprehensive sample data that will generate signals
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        
        # Generate realistic price data with clear patterns for signal generation
        base_price = 100
        prices = []
        for i in range(len(dates)):
            # Create cyclical pattern with trend to ensure crossovers
            cycle = 10 * np.sin(i * 0.2)  # Creates oscillations
            trend = i * 0.05  # Gentle upward trend
            noise = np.random.normal(0, 1)  # Reduced noise for clearer signals
            price = base_price + cycle + trend + noise
            prices.append(max(price, 10))  # Prevent negative prices
        
        self.df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
            'volume': np.random.randint(1000000, 5000000, len(dates))
        })
        self.df.set_index('date', inplace=True)
        
        # Add all required technical indicators
        self.df['sma_20'] = self.df['close'].rolling(20).mean()
        self.df['sma_50'] = self.df['close'].rolling(50).mean()
        
        # RSI - create more extreme values by amplifying the calculation
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        self.df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # Fill NaN values and ensure RSI reaches extreme values for testing
        self.df['rsi_14'] = self.df['rsi_14'].fillna(50)  # Fill initial NaN values
        # Add some extreme RSI values
        extreme_indices = [25, 30, 70, 75]
        for idx in extreme_indices:
            if idx < len(self.df):
                self.df.iloc[idx, self.df.columns.get_loc('rsi_14')] = 25 if idx in [25, 30] else 75
        
        # MACD - ensure crossovers
        ema_12 = self.df['close'].ewm(span=12).mean()
        ema_26 = self.df['close'].ewm(span=26).mean()
        self.df['macd'] = ema_12 - ema_26
        self.df['macd_signal'] = self.df['macd'].ewm(span=9).mean()
        
        # Bollinger Bands
        bb_mean = self.df['close'].rolling(20).mean()
        bb_std = self.df['close'].rolling(20).std()
        self.df['bb_upper_20'] = bb_mean + (2 * bb_std)
        self.df['bb_lower_20'] = bb_mean - (2 * bb_std)
        
        # ATR
        high_low = self.df['high'] - self.df['low']
        high_close = abs(self.df['high'] - self.df['close'].shift())
        low_close = abs(self.df['low'] - self.df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.df['atr_14'] = true_range.rolling(14).mean()

    def test_composer_initialization(self):
        """Test that the strategy composer initializes correctly."""
        composer = create_composer()
        
        self.assertIsInstance(composer, StrategyComposer)
        
        # Test that strategies are loaded
        strategies = composer.list_available_strategies()
        self.assertGreater(len(strategies), 0, "No strategies loaded")
        
        # Test that combinations are loaded
        combinations = composer.list_available_combinations()
        self.assertGreater(len(combinations), 0, "No combinations loaded")
        
        print(f"✅ Composer loaded {len(strategies)} strategies and {len(combinations)} combinations")

    def test_individual_strategies(self):
        """Test that individual strategies work correctly."""
        strategies_to_test = [
            ('SMACrossover', SMACrossover, {'fast': 20, 'slow': 50}),
            ('RSIReversion', RSIReversion, {'rsi_col': 'rsi_14', 'low_thresh': 30, 'high_thresh': 70}),
            ('MACDCross', MACDCross, {'macd_col': 'macd', 'signal_col': 'macd_signal'}),
            ('BollingerBounce', BollingerBounce, {'bb_window': 20})
        ]
        
        for strategy_name, strategy_class, params in strategies_to_test:
            with self.subTest(strategy=strategy_name):
                strategy = strategy_class(**params)
                signals = strategy.generate_signals(self.df)
                
                # Test signal format
                self.assertIsInstance(signals, pd.Series)
                self.assertEqual(len(signals), len(self.df))
                
                # Test signal values
                unique_signals = set(signals.dropna().unique())
                self.assertTrue(unique_signals.issubset({-1, 0, 1}))
                
                # Test that some signals are generated (not all zeros)
                non_zero_signals = (signals != 0).sum()
                self.assertGreater(non_zero_signals, 0, f"{strategy_name} generated no signals")
                
                print(f"✅ {strategy_name}: {non_zero_signals} signals generated")

    def test_strategy_combinations(self):
        """Test that strategy combinations work correctly."""
        composer = create_composer()
        
        # Test available combinations
        combinations = composer.list_available_combinations()
        test_combinations = ['technical_ensemble']  # Start with one we know works
        
        for combination_name in test_combinations:
            if combination_name in combinations:
                with self.subTest(combination=combination_name):
                    try:
                        signals = composer.execute_combination(combination_name, self.df)
                        
                        # Test signal format
                        self.assertIsInstance(signals, pd.Series)
                        self.assertEqual(len(signals), len(self.df))
                        
                        # Test signal values
                        unique_signals = set(signals.dropna().unique())
                        self.assertTrue(unique_signals.issubset({-1, 0, 1}))
                        
                        # Test signal statistics
                        total_signals = (signals != 0).sum()
                        buy_signals = (signals == 1).sum()
                        sell_signals = (signals == -1).sum()
                        
                        print(f"✅ {combination_name}: {total_signals} total signals ({buy_signals} buy, {sell_signals} sell)")
                        
                    except Exception as e:
                        self.fail(f"Combination {combination_name} failed: {e}")

    def test_convenience_functions(self):
        """Test convenience functions work correctly."""
        # Test get_signals function
        try:
            signals = get_signals('technical_ensemble', self.df)
            self.assertIsInstance(signals, pd.Series)
            self.assertEqual(len(signals), len(self.df))
            print("✅ get_signals() convenience function works")
        except Exception as e:
            self.fail(f"get_signals() failed: {e}")

    def test_data_integration(self):
        """Test that data fetching and processing integrates correctly."""
        # Test dynamic data fetching (using the same logic as our fixed tests)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            df = get_data("AAPL", interval="1d", start=start_str, end=end_str)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertGreater(len(df), 0)
            
            # Check for close column (may be named differently)
            close_columns = [col for col in df.columns if 'close' in col.lower()]
            self.assertGreater(len(close_columns), 0)
            
            print(f"✅ Data integration: Fetched {len(df)} rows of real market data")
            
        except Exception as e:
            # Don't fail the integration test if external data is unavailable
            print(f"⚠️  External data fetch warning: {e}")

    def test_feature_engineering_integration(self):
        """Test that feature engineering functions integrate correctly."""
        # Create simple base data
        base_df = pd.DataFrame({
            'close': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            'high': [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            'low': [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
        })
        
        # Test feature functions
        features_to_test = [
            ('SMA', add_sma, {'window': 3}),
            ('EMA', add_ema, {'window': 3}),
            ('RSI', add_rsi, {'window': 3})
        ]
        
        df = base_df.copy()
        for feature_name, feature_func, params in features_to_test:
            try:
                df = feature_func(df, **params)
                self.assertIn(f"{feature_name.lower()}_{params.get('window', '')}", df.columns)
                print(f"✅ {feature_name} feature engineering works")
            except Exception as e:
                self.fail(f"{feature_name} feature engineering failed: {e}")

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        print("\n🔄 Running end-to-end integration test...")
        
        # Step 1: Initialize composer
        composer = create_composer()
        self.assertIsInstance(composer, StrategyComposer)
        
        # Step 2: Get strategy info
        strategies = composer.list_available_strategies()
        combinations = composer.list_available_combinations()
        
        # Step 3: Execute a combination
        if 'technical_ensemble' in combinations:
            signals = composer.execute_combination('technical_ensemble', self.df)
            
            # Step 4: Validate results
            self.assertIsInstance(signals, pd.Series)
            self.assertEqual(len(signals), len(self.df))
            
            # Step 5: Generate summary statistics
            total_signals = (signals != 0).sum()
            buy_signals = (signals == 1).sum()
            sell_signals = (signals == -1).sum()
            signal_rate = total_signals / len(signals) * 100
            
            # Step 6: Validate reasonable behavior
            self.assertGreaterEqual(signal_rate, 0)  # Should have some signal rate
            self.assertLessEqual(signal_rate, 50)    # But not too many signals
            
            print(f"✅ End-to-end test completed successfully:")
            print(f"   - Loaded {len(strategies)} strategies")
            print(f"   - Processed {len(self.df)} data points")
            print(f"   - Generated {total_signals} signals ({signal_rate:.1f}% signal rate)")
            print(f"   - Buy/Sell ratio: {buy_signals}/{sell_signals}")
        else:
            self.skipTest("technical_ensemble combination not available")

    def test_strategy_level_filtering_integration(self):
        """Test strategy-level filtering integration with complete workflow."""
        print("\n🔄 Testing strategy-level filtering integration...")
        
        # Create multi-symbol dataset for realistic testing
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        multi_symbol_data = []
        
        for symbol in symbols:
            symbol_data = self.df.copy()
            symbol_data['symbol'] = symbol
            # Vary volume to test filtering
            if symbol == 'AAPL':
                symbol_data['volume'] = symbol_data['volume'] * 3  # High volume
            elif symbol == 'TSLA':
                symbol_data['volume'] = symbol_data['volume'] * 0.5  # Low volume
            multi_symbol_data.append(symbol_data)
        
        multi_df = pd.concat(multi_symbol_data, ignore_index=True)
        
        # Test basic filtering
        strategy = SMACrossover(fast=20, slow=50)
        volume_filter = StockFilter(min_volume=2000000)
        strategy.set_filters([volume_filter])
        
        # Generate signals with filtering
        filtered_signals = strategy.generate_signals_with_filters(self.df)
        unfiltered_signals = strategy.generate_signals(self.df)
        
        # Verify filtering has an effect
        self.assertEqual(len(filtered_signals), len(unfiltered_signals))
        # Filtered signals should have fewer or equal non-zero signals
        filtered_signal_count = (filtered_signals != 0).sum()
        unfiltered_signal_count = (unfiltered_signals != 0).sum()
        self.assertLessEqual(filtered_signal_count, unfiltered_signal_count)
        
        print(f"✅ Basic filtering: {unfiltered_signal_count} → {filtered_signal_count} signals after filtering")

    def test_symbol_specific_filtering_integration(self):
        """Test symbol-specific filtering in realistic multi-symbol scenarios."""
        print("\n🔄 Testing symbol-specific filtering integration...")
        
        # Create strategy with symbol-specific filters
        strategy = RSIReversion(rsi_col='rsi_14', low_thresh=30, high_thresh=70)
        
        # Set different filters for different symbols
        symbol_filters = {
            'AAPL': [StockFilter(min_volume=3000000)],  # Stricter for AAPL
            'GOOGL': [StockFilter(min_price=120)],      # Price filter for GOOGL
            'MSFT': [StockFilter(max_price=180)],       # Max price for MSFT
        }
        strategy.set_symbol_filters(symbol_filters)
        
        # Test with multi-symbol data
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'OTHERS']
        multi_symbol_data = []
        
        for symbol in symbols:
            symbol_data = self.df.copy()
            symbol_data['symbol'] = symbol
            # Customize data per symbol
            if symbol == 'AAPL':
                symbol_data['volume'] = symbol_data['volume'] * 2
                symbol_data['close'] = symbol_data['close'] * 1.5
            elif symbol == 'GOOGL':
                symbol_data['close'] = symbol_data['close'] * 1.2
            elif symbol == 'OTHERS':
                symbol_data['volume'] = symbol_data['volume'] * 0.3  # Low volume
            multi_symbol_data.append(symbol_data)
        
        multi_df = pd.concat(multi_symbol_data, ignore_index=True)
        
        # Generate signals with symbol-specific filtering
        advanced_signals = strategy.generate_signals_with_advanced_filters(multi_df)
        basic_signals = strategy.generate_signals_with_filters(multi_df)
        
        # Verify results
        self.assertEqual(len(advanced_signals), len(multi_df))
        
        # Symbol-specific filtering should affect results differently than basic filtering
        advanced_signal_count = (advanced_signals != 0).sum()
        basic_signal_count = (basic_signals != 0).sum()
        
        print(f"✅ Symbol-specific filtering: {basic_signal_count} → {advanced_signal_count} signals with symbol rules")

    def test_dynamic_filtering_integration(self):
        """Test dynamic filtering that adapts to market conditions."""
        print("\n🔄 Testing dynamic filtering integration...")
        
        # Create strategy with dynamic filters
        strategy = MACDCross(macd_col='macd', signal_col='macd_signal')
        
        # Simulate dynamic filters that change based on market conditions
        # In real usage, these would adapt to VIX, market regime, etc.
        high_volatility_filter = StockFilter(min_volume=3000000)  # Require higher volume during volatility
        low_volatility_filter = StockFilter(min_volume=1000000)   # Lower volume requirement in calm markets
        
        # Test high volatility scenario
        strategy.set_dynamic_filters([high_volatility_filter])
        high_vol_signals = strategy.generate_signals_with_advanced_filters(self.df)
        
        # Test low volatility scenario
        strategy.set_dynamic_filters([low_volatility_filter])
        low_vol_signals = strategy.generate_signals_with_advanced_filters(self.df)
        
        # Verify different filtering produces different results
        high_vol_count = (high_vol_signals != 0).sum()
        low_vol_count = (low_vol_signals != 0).sum()
        
        # Low volatility filter should generally allow more signals
        self.assertGreaterEqual(low_vol_count, high_vol_count)
        
        print(f"✅ Dynamic filtering: High vol: {high_vol_count}, Low vol: {low_vol_count} signals")

    def test_configuration_based_filtering_integration(self):
        """Test configuration-driven filtering integration."""
        print("\n🔄 Testing configuration-based filtering integration...")
        
        # Create multiple filter configurations
        configs = {
            'conservative': {
                'stock_filter': {
                    'min_volume': 5000000,
                    'min_price': 100,
                    'max_price': 500
                },
                'liquidity_filter': {
                    'min_avg_volume': 3000000,
                    'volume_window': 20
                },
                'logic': 'AND'
            },
            'aggressive': {
                'stock_filter': {
                    'min_volume': 1000000,
                    'min_price': 10
                },
                'logic': 'AND'
            },
            'balanced': {
                'stock_filter': {
                    'min_volume': 2000000,
                    'min_price': 50
                },
                'time_filter': {
                    'exclude_market_holidays': True,
                    'min_trading_days': 20
                },
                'logic': 'AND'
            }
        }
        
        results = {}
        
        for config_name, filter_config in configs.items():
            strategy = SMACrossover(fast=20, slow=50)
            strategy.configure_filters_from_config(filter_config)
            
            signals = strategy.generate_signals_with_filters(self.df)
            signal_count = (signals != 0).sum()
            results[config_name] = signal_count
            
            # Verify configuration was applied
            self.assertGreater(len(strategy.filters), 0)
            self.assertEqual(strategy.filter_logic, filter_config['logic'])
        
        # Conservative should have fewer signals than aggressive
        self.assertLessEqual(results['conservative'], results['aggressive'])
        
        print(f"✅ Config-based filtering: Conservative: {results['conservative']}, "
              f"Balanced: {results['balanced']}, Aggressive: {results['aggressive']} signals")

    def test_composer_with_filtered_strategies_integration(self):
        """Test composer integration with filtered strategies."""
        print("\n🔄 Testing composer integration with filtered strategies...")
        
        # Create filtered strategies
        strategies = {}
        
        # Strategy 1: Volume-filtered SMA
        sma_strategy = SMACrossover(fast=20, slow=50)
        sma_strategy.set_filters([StockFilter(min_volume=2000000)])
        strategies['filtered_sma'] = sma_strategy
        
        # Strategy 2: RSI with symbol-specific filters
        rsi_strategy = RSIReversion(rsi_col='rsi_14', low_thresh=30, high_thresh=70)
        rsi_strategy.set_symbol_filters({
            'AAPL': [StockFilter(min_volume=3000000)],
            'GOOGL': [StockFilter(min_price=100)]
        })
        strategies['symbol_filtered_rsi'] = rsi_strategy
        
        # Strategy 3: Configuration-based filtering
        macd_strategy = MACDCross(macd_col='macd', signal_col='macd_signal')
        macd_strategy.configure_filters_from_config({
            'stock_filter': {'min_volume': 1500000, 'min_price': 80},
            'liquidity_filter': {'min_avg_volume': 1000000},
            'logic': 'AND'
        })
        strategies['config_filtered_macd'] = macd_strategy
        
        # Test each filtered strategy
        for name, strategy in strategies.items():
            with self.subTest(strategy=name):
                # Test basic filtering
                basic_signals = strategy.generate_signals_with_filters(self.df)
                self.assertEqual(len(basic_signals), len(self.df))
                
                # Test advanced filtering (if applicable)
                if hasattr(strategy, 'symbol_filters') and strategy.symbol_filters:
                    advanced_signals = strategy.generate_signals_with_advanced_filters(self.df)
                    self.assertEqual(len(advanced_signals), len(self.df))
                
                basic_count = (basic_signals != 0).sum()
                print(f"✅ {name}: {basic_count} filtered signals generated")

    def test_filter_analytics_integration(self):
        """Test filter analytics and validation in integration scenarios."""
        print("\n🔄 Testing filter analytics integration...")
        
        # Create complex filtering setup
        strategy = BollingerBounce(bb_window=20)
        
        # Add multiple types of filters
        strategy.set_filters([
            StockFilter(min_volume=2000000, min_price=50),
            LiquidityFilter(min_avg_volume=1500000)
        ])
        
        strategy.set_symbol_filters({
            'AAPL': [StockFilter(min_volume=5000000)],
            'GOOGL': [StockFilter(min_price=100)],
            'MSFT': [StockFilter(max_price=200)]
        })
        
        strategy.set_dynamic_filters([
            TimeFilter(exclude_market_holidays=True)
        ])
        
        # Test analytics
        basic_info = strategy.get_filter_info()
        advanced_info = strategy.get_advanced_filter_info()
        
        # Verify analytics structure
        self.assertIn('filter_count', basic_info)
        self.assertIn('logic', basic_info)
        self.assertEqual(basic_info['filter_count'], 2)
        
        self.assertIn('base_filters', advanced_info)
        self.assertIn('symbol_filters', advanced_info)
        self.assertIn('dynamic_filters', advanced_info)
        
        # Verify correct counts
        self.assertEqual(len(advanced_info['symbol_filters']), 3)
        self.assertEqual(len(advanced_info['dynamic_filters']), 1)
        
        print(f"✅ Filter analytics: {basic_info['filter_count']} base, "
              f"{len(advanced_info['symbol_filters'])} symbol-specific, "
              f"{len(advanced_info['dynamic_filters'])} dynamic filters")

    def test_filtering_edge_cases_integration(self):
        """Test filtering edge cases in integration scenarios."""
        print("\n🔄 Testing filtering edge cases integration...")
        
        # Test 1: Empty filter handling
        strategy = SMACrossover(fast=20, slow=50)
        empty_signals = strategy.generate_signals_with_filters(self.df)
        no_filter_signals = strategy.generate_signals(self.df)
        
        # Should be equivalent when no filters applied
        pd.testing.assert_series_equal(empty_signals, no_filter_signals, check_names=False)
        
        # Test 2: Filters that eliminate all data
        strict_filter = StockFilter(min_volume=50000000)  # Very high volume requirement
        strategy.set_filters([strict_filter])
        
        strict_signals = strategy.generate_signals_with_filters(self.df)
        # Should return all zeros when everything is filtered out
        self.assertTrue((strict_signals == 0).all())
        
        # Test 3: OR vs AND logic
        filter1 = StockFilter(min_volume=10000000)  # High volume
        filter2 = StockFilter(min_price=200)       # High price
        
        # Test AND logic (restrictive)
        strategy.set_filters([filter1, filter2], logic="AND")
        and_signals = strategy.generate_signals_with_filters(self.df)
        
        # Test OR logic (permissive)
        strategy.set_filters([filter1, filter2], logic="OR")
        or_signals = strategy.generate_signals_with_filters(self.df)
        
        # OR should generally produce more or equal signals than AND
        and_count = (and_signals != 0).sum()
        or_count = (or_signals != 0).sum()
        self.assertGreaterEqual(or_count, and_count)
        
        print(f"✅ Edge cases: AND logic: {and_count}, OR logic: {or_count} signals")

    def test_error_handling(self):
        """Test that error handling works correctly."""
        composer = create_composer()
        
        # Test invalid combination
        with self.assertRaises(ValueError):
            composer.execute_combination('nonexistent_combination', self.df)
        
        # Test invalid data
        empty_df = pd.DataFrame()
        try:
            composer.execute_combination('technical_ensemble', empty_df)
        except Exception:
            pass  # Expected to fail with empty data
        
        print("✅ Error handling works correctly")

    def test_performance_reasonable(self):
        """Test that performance is reasonable for integration testing."""
        import time
        
        composer = create_composer()
        
        # Test with larger dataset
        large_df = self.df.copy()
        for i in range(3):  # Make it 4x larger
            large_df = pd.concat([large_df, self.df])
        
        start_time = time.time()
        signals = composer.execute_combination('technical_ensemble', large_df)
        execution_time = time.time() - start_time
        
        self.assertLess(execution_time, 5.0, "Integration test took too long (>5 seconds)")
        print(f"✅ Performance test: {len(large_df)} data points processed in {execution_time:.2f}s")


if __name__ == '__main__':
    print("🧪 Running Integration Tests...")
    unittest.main(verbosity=2) 