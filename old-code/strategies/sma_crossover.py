import pandas as pd
from .base import Strategy

class SMACrossover(Strategy):
    """
    Simple Moving Average crossover strategy.
    Generates signals only when fast SMA crosses above/below slow SMA.
    """
    def __init__(self, fast: int = 20, slow: int = 50):
        super().__init__()
        self.fast = fast
        self.slow = slow

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on SMA crossovers.
        
        Returns:
            1 when fast SMA crosses ABOVE slow SMA (bullish crossover)
            -1 when fast SMA crosses BELOW slow SMA (bearish crossover)
            0 otherwise (no crossover)
        """
        signal = pd.Series(0, index=df.index)
        
        fast_sma = df[f"sma_{self.fast}"]
        slow_sma = df[f"sma_{self.slow}"]
        
        # Detect crossovers by comparing current vs previous relationships
        # Bullish crossover: fast was below slow, now above slow
        prev_fast_below = (fast_sma.shift(1) <= slow_sma.shift(1))
        curr_fast_above = (fast_sma > slow_sma)
        bullish_crossover = prev_fast_below & curr_fast_above
        
        # Bearish crossover: fast was above slow, now below slow  
        prev_fast_above = (fast_sma.shift(1) >= slow_sma.shift(1))
        curr_fast_below = (fast_sma < slow_sma)
        bearish_crossover = prev_fast_above & curr_fast_below
        
        signal[bullish_crossover] = 1
        signal[bearish_crossover] = -1
        
        return signal
