import unittest
import pandas as pd
from strategies.atr_filter import ATRVolatilityFilter
from strategies.bollinger_bounce import BollingerBounce
from strategies.macd_cross import MACDCross
from strategies.rsi_reversion import RSIReversion
from strategies.sma_crossover import SMACrossover

class TestStrategies(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            "close": [10, 12, 8, 15, 7, 13, 9, 14, 8, 12],
            "bb_lower_20": [8]*10,
            "bb_upper_20": [14]*10,
            "macd": [0, 5, 10, 15, 5, -5, -10, -15, 0, 5],
            "rsi_14": [25, 35, 75, 65, 20, 80, 50, 30, 70, 40],
            "sma_20": [10]*10,
            "sma_50": [12]*10,
            "atr_14": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })

    def test_atr_volatility_filter(self):
        strat = ATRVolatilityFilter(atr_col="atr_14", window=3)
        signals = strat.generate_signals(self.df)
        self.assertEqual(len(signals), len(self.df))
        self.assertTrue(set(signals.unique()).issubset({0, 1}))

    def test_bollinger_bounce(self):
        strat = BollingerBounce(bb_window=20)
        signals = strat.generate_signals(self.df)
        self.assertEqual(len(signals), len(self.df))
        self.assertTrue(set(signals.unique()).issubset({-1, 0, 1}))

    def test_macd_cross(self):
        strat = MACDCross(macd_signal=5)
        signals = strat.generate_signals(self.df)
        self.assertEqual(len(signals), len(self.df))
        self.assertTrue(set(signals.unique()).issubset({-1, 0, 1}))

    def test_rsi_reversion(self):
        strat = RSIReversion(rsi_col="rsi_14", low_thresh=30, high_thresh=70)
        signals = strat.generate_signals(self.df)
        self.assertEqual(len(signals), len(self.df))
        self.assertTrue(set(signals.unique()).issubset({-1, 0, 1}))

    def test_sma_crossover(self):
        strat = SMACrossover(fast=20, slow=50)
        signals = strat.generate_signals(self.df)
        self.assertEqual(len(signals), len(self.df))
        self.assertTrue(set(signals.unique()).issubset({-1, 0, 1}))

if __name__ == "__main__":
    unittest.main()
