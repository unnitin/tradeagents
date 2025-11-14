from .sma_crossover import SMACrossover
from .rsi_reversion import RSIReversion
from .macd_cross import MACDCross
from .bollinger_bounce import BollingerBounce
from .atr_filter import ATRVolatilityFilter

def get_all_strategies():
    """Get all available trading strategies."""
    return [
        SMACrossover(),
        RSIReversion(),
        MACDCross(),
        BollingerBounce(),
        # ATRVolatilityFilter acts as filter; not directional
    ]

def combine_signals(df, strategies):
    """Combine signals from multiple strategies."""
    import pandas as pd
    
    if not strategies:
        return pd.Series(0, index=df.index)
    
    signals = [s.generate_signals(df) for s in strategies]
    combined = signals[0].copy()
    for signal in signals[1:]:
        combined = combined.add(signal, fill_value=0)
    
    return combined.clip(-1, 1)  # Normalize: strong agreement = still 1 or -1
