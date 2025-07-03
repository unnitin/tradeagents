# data/preprocess.py

import pandas as pd
from .constants import OHLCVResampleRules


def resample_ohlcv(df: pd.DataFrame, interval: str = "5min") -> pd.DataFrame:
    """
    Resamples OHLCV data to a different time interval.

    Args:
        df (pd.DataFrame): Original data with columns ['open', 'high', 'low', 'close', 'volume']
        interval (str): Resample rule (e.g., '5min', '1h', '1d')

    Returns:
        pd.DataFrame: Resampled OHLCV data
    """
    ohlc_dict = {
        'open': OHLCVResampleRules.open,
        'high': OHLCVResampleRules.high,
        'low': OHLCVResampleRules.low,
        'close': OHLCVResampleRules.close,
        'volume': OHLCVResampleRules.volume
    }

    resampled = df.resample(interval).agg(ohlc_dict).dropna()
    return resampled
