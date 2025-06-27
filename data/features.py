import pandas as pd

def add_sma(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Adds Simple Moving Average (SMA) to the DataFrame.

    Args:
        df (pd.DataFrame): OHLCV DataFrame with a 'close' column.
        window (int): Lookback window for SMA calculation.

    Returns:
        pd.DataFrame: DataFrame with new 'sma_{window}' column.
    """
    df[f"sma_{window}"] = df["close"].rolling(window=window).mean()
    return df

def add_ema(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Adds Exponential Moving Average (EMA) to the DataFrame.

    Args:
        df (pd.DataFrame): OHLCV DataFrame with a 'close' column.
        window (int): EMA period.

    Returns:
        pd.DataFrame: DataFrame with new 'ema_{window}' column.
    """
    df[f"ema_{window}"] = df["close"].ewm(span=window, adjust=False).mean()
    return df

def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    Adds Relative Strength Index (RSI) to the DataFrame.

    Args:
        df (pd.DataFrame): OHLCV DataFrame with a 'close' column.
        window (int): Lookback period for RSI.

    Returns:
        pd.DataFrame: DataFrame with new 'rsi_{window}' column.
    """
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df[f"rsi_{window}"] = 100 - (100 / (1 + rs))
    return df

def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """
    Adds Bollinger Bands to the DataFrame.

    Args:
        df (pd.DataFrame): OHLCV DataFrame with a 'close' column.
        window (int): Rolling window for the moving average.
        num_std (float): Number of standard deviations for band width.

    Returns:
        pd.DataFrame: DataFrame with 'bb_upper_{window}' and 'bb_lower_{window}' columns.
    """
    sma = df["close"].rolling(window=window).mean()
    std = df["close"].rolling(window=window).std()
    df[f"bb_upper_{window}"] = sma + num_std * std
    df[f"bb_lower_{window}"] = sma - num_std * std
    return df

def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    Adds MACD (Moving Average Convergence Divergence) indicators to the DataFrame.

    Args:
        df (pd.DataFrame): OHLCV DataFrame with a 'close' column.
        fast (int): Short-term EMA period.
        slow (int): Long-term EMA period.
        signal (int): Signal line EMA period.

    Returns:
        pd.DataFrame: DataFrame with 'macd', 'macd_signal', and 'macd_hist' columns.
    """
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = macd_line - signal_line
    return df

def add_atr(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    Adds Average True Range (ATR) to the DataFrame.

    Args:
        df (pd.DataFrame): OHLCV DataFrame with 'high', 'low', and 'close' columns.
        window (int): Lookback period for ATR calculation.

    Returns:
        pd.DataFrame: DataFrame with new 'atr_{window}' column.
    """
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df[f"atr_{window}"] = tr.rolling(window).mean()
    return df
