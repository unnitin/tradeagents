import unittest
import pandas as pd

from data.fetch_data import get_data
from data.features import add_sma, add_ema, add_rsi
from data.preprocess import resample_ohlcv
from data.constants import OHLCVResampleRules

class TestFetchData(unittest.TestCase):
    def test_get_data_returns_dataframe(self):
        # Use a very short time window for speed
        df = get_data("AAPL", interval="1d", start="2024-06-01", end="2024-06-03")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("close", df.columns)

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            "close": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "open": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "high": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "low": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "volume": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
        })

    def test_add_sma(self):
        df = add_sma(self.df.copy(), window=3)
        self.assertIn("sma_3", df.columns)
        self.assertTrue(df["sma_3"].isnull().sum() > 0)  # First few will be NaN

    def test_add_ema(self):
        df = add_ema(self.df.copy(), window=3)
        self.assertIn("ema_3", df.columns)

    def test_add_rsi(self):
        df = add_rsi(self.df.copy(), window=3)
        self.assertIn("rsi_3", df.columns)

class TestPreprocess(unittest.TestCase):
    def setUp(self):
        rng = pd.date_range("2024-06-01", periods=10, freq="T")
        self.df = pd.DataFrame({
            "open": range(10),
            "high": range(1, 11),
            "low": range(10),
            "close": range(10),
            "volume": range(10, 20)
        }, index=rng)

    def test_resample_ohlcv(self):
        resampled = resample_ohlcv(self.df, interval="5T")
        self.assertIsInstance(resampled, pd.DataFrame)
        self.assertIn("open", resampled.columns)
        self.assertEqual(len(resampled), 2)

if __name__ == "__main__":
    unittest.main()
