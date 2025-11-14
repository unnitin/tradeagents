import unittest
import pandas as pd
import sys
import os
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path to import data modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import (
    get_data, add_sma, add_ema, add_rsi, add_bollinger_bands, 
    add_macd, add_atr, resample_ohlcv
)
from data.constants import OHLCVResampleRules

class TestFetchData(unittest.TestCase):
    def test_get_data_returns_dataframe(self):
        # Use dynamic dates based on today to ensure recent data availability
        # Go back 10 days to ensure we capture multiple trading days (avoiding weekends)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        # Format dates as strings
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        df = get_data("AAPL", interval="1d", start=start_str, end=end_str)
        self.assertIsInstance(df, pd.DataFrame)
        # Check for close column (may be named 'close_aapl' or 'close')
        close_columns = [col for col in df.columns if 'close' in col.lower()]
        self.assertGreater(len(close_columns), 0, f"No close column found in {df.columns}")
        # Should have data for recent trading days (at least 1 day in 10-day window)
        self.assertGreater(len(df), 0)

class TestFeatures(unittest.TestCase):
    def setUp(self):
        # Create simple test data where we can manually calculate expected values
        self.df = pd.DataFrame({
            "close": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            "open": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            "high": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
            "low": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            "volume": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
        })

    def test_add_sma_calculation(self):
        """Test that SMA is calculated correctly."""
        df = add_sma(self.df.copy(), window=3)
        
        # First two values should be NaN (not enough data)
        self.assertTrue(pd.isna(df["sma_3"].iloc[0]))
        self.assertTrue(pd.isna(df["sma_3"].iloc[1]))
        
        # Third value should be (10 + 11 + 12) / 3 = 11
        self.assertAlmostEqual(df["sma_3"].iloc[2], 11.0, places=6)
        
        # Fourth value should be (11 + 12 + 13) / 3 = 12
        self.assertAlmostEqual(df["sma_3"].iloc[3], 12.0, places=6)
        
        # Last value should be (18 + 19 + 20) / 3 = 19
        self.assertAlmostEqual(df["sma_3"].iloc[-1], 19.0, places=6)

    def test_add_ema_calculation(self):
        """Test that EMA is calculated correctly."""
        df = add_ema(self.df.copy(), window=3)
        
        # EMA should have no NaN values (pandas ewm handles initialization)
        self.assertFalse(df["ema_3"].isna().any())
        
        # First value should equal the first close price
        self.assertAlmostEqual(df["ema_3"].iloc[0], 10.0, places=6)
        
        # EMA should be trending upward with our increasing data
        self.assertTrue(df["ema_3"].iloc[-1] > df["ema_3"].iloc[0])
        
        # EMA should be closer to recent values than SMA
        df_sma = add_sma(df, window=3)
        # At the end, EMA should be higher than SMA for uptrending data
        self.assertGreater(df["ema_3"].iloc[-1], df_sma["sma_3"].iloc[-1])

    def test_add_rsi_calculation(self):
        """Test that RSI is calculated correctly."""
        # Create data with known price movements for RSI testing
        rsi_data = pd.DataFrame({
            "close": [44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.85, 46.08, 
                     45.89, 46.03, 45.61, 46.28, 46.28, 46, 46.03, 46.41, 46.22, 45.64],
            "open": [43, 44, 44, 44, 43, 44, 44, 45, 46, 45, 46, 45, 46, 46, 46, 46, 46, 46, 45],
            "high": [45, 45, 45, 45, 44, 45, 45, 46, 47, 46, 47, 46, 47, 47, 46, 47, 47, 47, 46],
            "low": [43, 44, 43, 44, 43, 44, 44, 45, 45, 45, 45, 45, 46, 46, 45, 45, 46, 46, 45],
            "volume": [100] * 19
        })
        
        df = add_rsi(rsi_data, window=14)
        
        # First 13-14 values should be NaN (not enough data for RSI calculation)
        self.assertEqual(df["rsi_14"].isna().sum(), 13)
        
        # RSI should be between 0 and 100
        valid_rsi = df["rsi_14"].dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())
        
        # For our slightly uptrending data, RSI should be above 50
        self.assertGreater(valid_rsi.iloc[-1], 50)

    def test_add_bollinger_bands_calculation(self):
        """Test that Bollinger Bands are calculated correctly."""
        df = add_bollinger_bands(self.df.copy(), window=5, num_std=2.0)
        
        # Check that columns are created
        self.assertIn("bb_upper_5", df.columns)
        self.assertIn("bb_lower_5", df.columns)
        
        # For our linearly increasing data, upper band should be above close price
        valid_data = df.dropna()
        self.assertTrue((valid_data["bb_upper_5"] > valid_data["close"]).all())
        
        # Lower band should be below close price
        self.assertTrue((valid_data["bb_lower_5"] < valid_data["close"]).all())
        
        # Manually verify one calculation
        # For window=5, at index 4: close prices are [10,11,12,13,14]
        # SMA = 12, STD = 1.58..., so upper = 12 + 2*1.58 ≈ 15.16
        self.assertAlmostEqual(df["bb_upper_5"].iloc[4], 15.165, places=2)
        self.assertAlmostEqual(df["bb_lower_5"].iloc[4], 8.835, places=2)

    def test_add_macd_calculation(self):
        """Test that MACD is calculated correctly."""
        df = add_macd(self.df.copy(), fast=5, slow=10, signal=3)
        
        # Check that all MACD columns are created
        self.assertIn("macd", df.columns)
        self.assertIn("macd_signal", df.columns)
        self.assertIn("macd_hist", df.columns)
        
        # MACD histogram should equal MACD line minus signal line
        valid_data = df.dropna()
        np.testing.assert_array_almost_equal(
            valid_data["macd_hist"], 
            valid_data["macd"] - valid_data["macd_signal"],
            decimal=10
        )
        
        # For uptrending data, MACD should eventually become positive
        self.assertGreater(df["macd"].iloc[-1], 0)

    def test_add_atr_calculation(self):
        """Test that ATR is calculated correctly."""
        df = add_atr(self.df.copy(), window=3)
        
        # Check that ATR column is created
        self.assertIn("atr_3", df.columns)
        
        # ATR should always be positive
        valid_atr = df["atr_3"].dropna()
        self.assertTrue((valid_atr > 0).all())
        
        # First value should be NaN (no previous close for TR calculation)
        # Second value should also be NaN (not enough data for rolling mean)
        self.assertTrue(pd.isna(df["atr_3"].iloc[0]))
        self.assertTrue(pd.isna(df["atr_3"].iloc[1]))
        
        # For our simple data with constant ranges, ATR should be relatively stable
        # Each day has high-low = 2, so ATR should be close to 2.0
        self.assertAlmostEqual(df["atr_3"].iloc[-1], 2.0, places=1)

    def test_feature_functions_preserve_original_data(self):
        """Test that feature functions don't modify original DataFrame structure."""
        original_df = self.df.copy()
        original_columns = set(original_df.columns)
        
        # Apply all feature functions
        df = add_sma(original_df.copy(), window=3)
        df = add_ema(df, window=3)
        df = add_rsi(df, window=3)
        df = add_bollinger_bands(df, window=3)
        df = add_macd(df)
        df = add_atr(df, window=3)
        
        # Original columns should still exist
        for col in original_columns:
            self.assertIn(col, df.columns)
        
        # Original data should be unchanged
        for col in original_columns:
            pd.testing.assert_series_equal(df[col], original_df[col])

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test with single row
        single_row = pd.DataFrame({"close": [10], "high": [11], "low": [9], "open": [9.5], "volume": [100]})
        
        # These should not raise errors but will have NaN values
        df = add_sma(single_row.copy(), window=3)
        self.assertTrue(pd.isna(df["sma_3"].iloc[0]))
        
        # Test with window larger than data
        small_df = pd.DataFrame({"close": [10, 11], "high": [11, 12], "low": [9, 10], "open": [9.5, 10.5], "volume": [100, 110]})
        df = add_sma(small_df.copy(), window=5)
        self.assertTrue(df["sma_5"].isna().all())

class TestPreprocess(unittest.TestCase):
    def setUp(self):
        rng = pd.date_range("2024-06-01", periods=10, freq="min")
        self.df = pd.DataFrame({
            "open": range(10),
            "high": range(1, 11),
            "low": range(10),
            "close": range(10),
            "volume": range(10, 20)
        }, index=rng)

    def test_resample_ohlcv(self):
        resampled = resample_ohlcv(self.df, interval="5min")
        self.assertIsInstance(resampled, pd.DataFrame)
        self.assertIn("open", resampled.columns)
        self.assertEqual(len(resampled), 2)

if __name__ == "__main__":
    unittest.main()
