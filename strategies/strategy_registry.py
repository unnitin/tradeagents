from strategies.sma_crossover import SMACrossover
from strategies.rsi_reversion import RSIReversion
from strategies.macd_cross import MACDCross
from strategies.bollinger_bounce import BollingerBounce
from strategies.atr_filter import ATRVolatilityFilter

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
    combined = sum([s.generate_signals(df) for s in strategies])
    return combined.clip(-1, 1)  # Normalize: strong agreement = still 1 or -1

# Note: For politician trade tracking, use the dedicated modules:
# - data/politician_trades_live.py (API data)
# - data/twitter_politician_tracker.py (Twitter alerts)  
# - examples/easy_politician_tracking.py (complete guide)
