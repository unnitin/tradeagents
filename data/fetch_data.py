# data/fetch_data.py

import yfinance as yf
import pandas as pd

def get_data(ticker: str, interval: str = "1m", start: str = None, end: str = None) -> pd.DataFrame:
    """
    Fetch historical stock data from Yahoo Finance.

    Args:
        ticker (str): Stock ticker (e.g., "AAPL").
        interval (str): Data interval (e.g., "1m", "5m", "1d").
        start (str): Start date (YYYY-MM-DD or None).
        end (str): End date (YYYY-MM-DD or None).

    Returns:
        pd.DataFrame: Cleaned DataFrame with OHLCV columns.
    """
    df = yf.download(
        tickers=ticker,
        interval=interval,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
    )

    if df.empty:
        raise ValueError(f"No data returned for {ticker} with interval {interval}.")

    df.dropna(inplace=True)
    df = df.reset_index()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col.strip()).strip() for col in df.columns.values]
    df.columns = df.columns.str.lower()  # standardize column names
    
    return df



if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"
    interval = "1m"
    start_date = "2025-06-20"
    end_date = "2025-06-26"

    df = get_data(ticker, interval, start_date, end_date)
    print(df.head())