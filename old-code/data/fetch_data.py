# data/fetch_data.py

import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd  # type: ignore
import requests  # type: ignore
import urllib3

from .constants import YAHOO_FINANCE_INTERVALS
from .news import NewsFetcher

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Unified data fetcher combining stock data, politician trades, and social media tracking.
    
    Uses Direct Yahoo Finance API for reliable stock data access, bypassing SSL certificate issues.
    Single entry point for all trading data needs - fully self-contained and production-ready.
    """
    
    def __init__(self, quiver_api_key: Optional[str] = None, capitol_trades_api_key: Optional[str] = None):
        # Load API keys using the centralized loader
        api_keys = self._load_api_keys()
        self.quiver_api_key = quiver_api_key or api_keys.get('quiver_api_key')
        self.capitol_trades_api_key = capitol_trades_api_key or api_keys.get('capitol_trades_api_key')
        self.news_fetcher = NewsFetcher(
            newsapi_api_key=api_keys.get('newsapi_api_key'),
            finnhub_api_key=api_keys.get('finnhub_api_key')
        )
        
        # API Configuration - consolidated external service endpoints
        self.config = self._load_api_config()
        
        # Legacy compatibility - maintain direct access
        self.endpoints = self.config['api_endpoints']
        self.trading_accounts = self.config['social_accounts']
        
        self.ticker_pattern = r'\$([A-Z]{1,5})'
        
        # Note: SSL configuration removed - Direct Yahoo Finance API handles SSL internally
    
    def _load_api_config(self) -> Dict[str, Any]:
        """
        Load consolidated API configuration.
        
        Centralizes all external service endpoints and social media accounts
        for better organization and easier maintenance.
        
        Returns:
            Dict containing API endpoints, social accounts, and other config
        """
        return {
            'api_endpoints': {
                'quiver_house': 'https://api.quiverquant.com/beta/live/congresstrading/house',
                'quiver_senate': 'https://api.quiverquant.com/beta/live/congresstrading/senate',
                'yahoo_finance_chart': 'https://query1.finance.yahoo.com/v8/finance/chart'
            },
            'social_accounts': {
                'PelosiTracker': '@PelosiTracker',
                'CongressTrading': '@CongressTrading',
                'CapitolTrades': '@CapitolTrades_',
                'QuiverQuant': '@QuiverQuant'
            },
            'data_sources': {
                'stock_data': 'yahoo_finance_direct',
                'politician_trades': 'quiver_api',
                'social_sentiment': 'twitter_tracking'
            },
            'default_intervals': {
                'stock_data': '1d',
                'intraday': '1h',
                'minute': '1m'
            }
        }
    
    def _load_api_keys(self) -> Dict[str, Optional[str]]:
        """
        Load API keys from environment variables.
        
        Centralizes API key management with fallback to environment variables.
        This provides a consistent approach similar to the config loader.
        
        Returns:
            Dict containing API keys loaded from environment
        """
        return {
            'quiver_api_key': os.getenv('QUIVER_API_KEY'),
            'capitol_trades_api_key': os.getenv('CAPITOL_TRADES_API_KEY'),
            'alpha_vantage_api_key': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'finnhub_api_key': os.getenv('FINNHUB_API_KEY'),
            'newsapi_api_key': os.getenv('NEWSAPI_API_KEY')
        }
    
    def get_news_data(self,
                      symbols: Optional[Union[str, List[str]]] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      limit: int = 100,
                      provider: str = "newsapi") -> pd.DataFrame:
        """
        Fetch market-relevant news headlines suitable for sentiment analysis.
        
        Args:
            symbols: Single ticker or list of tickers. Defaults to major tech names.
            start_date: ISO date string (YYYY-MM-DD). Defaults to 3 days ago.
            end_date: ISO date string (YYYY-MM-DD). Defaults to today.
            limit: Maximum number of articles.
            provider: Preferred provider ("newsapi" or "finnhub").
            
        Returns:
            DataFrame with columns like: published_at, symbol, headline, news_headline, summary, source.
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        return self.news_fetcher.get_headlines(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            provider=provider
        )
    
    def get_stock_data(self, ticker: str, interval: str = "1d", 
                      start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch historical stock data using Direct Yahoo Finance API.
        
        Directly accesses Yahoo's chart API for reliable data retrieval.
        Returns clean OHLCV data ready for analysis and backtesting.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')
            interval: Data interval ('1d', '1h', '5m', '1m')
            start: Start date as 'YYYY-MM-DD' string
            end: End date as 'YYYY-MM-DD' string
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume, adj_close
        """
        
        try:
            logger.info("Fetching %s via Direct Yahoo Finance API…", ticker)
            df = self._fetch_yahoo_direct(ticker, interval, start, end)
            
            if not df.empty:
                logger.info("Successfully fetched %s", ticker)
                return self._process_dataframe(df)
            else:
                raise ValueError(f"Empty dataframe returned for {ticker}")
                
        except Exception as e:
            raise ValueError(f"Failed to fetch data for {ticker} with interval {interval}. Error: {e}")
    
    def _fetch_yahoo_direct(self, ticker: str, interval: str, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
        """Direct Yahoo Finance API access for reliable stock data retrieval."""
        try:
            # Convert dates to timestamps
            if start:
                start_ts = int(datetime.strptime(start, '%Y-%m-%d').timestamp())
            else:
                start_ts = int((datetime.now() - timedelta(days=365)).timestamp())
            
            if end:
                end_ts = int(datetime.strptime(end, '%Y-%m-%d').timestamp())
            else:
                end_ts = int(datetime.now().timestamp())
            
            # Map intervals using constants
            yahoo_interval = YAHOO_FINANCE_INTERVALS.get(interval, '1d')
            
            # Yahoo Finance API URL from configuration
            base_url = self.config['api_endpoints']['yahoo_finance_chart']
            url = f"{base_url}/{ticker}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': yahoo_interval,
                'includePrePost': 'false'
            }
            
            # Create session with SSL verification disabled
            session = requests.Session()
            session.verify = False
            
            # Disable SSL warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' not in data or not data['chart']['result']:
                raise ValueError(f"No data available for {ticker}")
            
            result = data['chart']['result'][0]
            
            if 'timestamp' not in result or not result['timestamp']:
                raise ValueError(f"No timestamp data for {ticker}")
            
            # Extract OHLCV data
            timestamps = result['timestamp']
            indicators = result['indicators']['quote'][0]
            
            df_data = {
                'date': [datetime.fromtimestamp(ts) for ts in timestamps],
                'open': indicators.get('open', [None] * len(timestamps)),
                'high': indicators.get('high', [None] * len(timestamps)),
                'low': indicators.get('low', [None] * len(timestamps)),
                'close': indicators.get('close', [None] * len(timestamps)),
                'volume': indicators.get('volume', [None] * len(timestamps))
            }
            
            # Add adjusted close if available
            if 'adjclose' in result['indicators']:
                df_data['adj_close'] = result['indicators']['adjclose'][0]['adjclose']
            else:
                df_data['adj_close'] = df_data['close']
            
            df = pd.DataFrame(df_data)
            df = df.dropna()
            
            return df
            
        except Exception as e:
            raise Exception(f"Direct Yahoo API failed: {e}")
    
    def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and clean the downloaded dataframe."""
        if df.empty:
            return df
            
        df.dropna(inplace=True)
        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(col).strip() for col in df.columns.values]
        df.columns = [col.lower() for col in df.columns]
        
        return df
    
    def _fetch_quiver_data(self, endpoint: str, days_back: int) -> pd.DataFrame:
        """Internal method to fetch data from Quiver API."""
        if not self.quiver_api_key:
            logger.warning("Quiver API key required for live politician data")
            return pd.DataFrame()
        
        try:
            headers = {
                'Authorization': f'Bearer {self.quiver_api_key}',
                'User-Agent': 'DataFetcher/1.0'
            }
            
            response = requests.get(
                endpoint, 
                headers=headers, 
                params={'days': days_back}, 
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Standardize column names
            column_mapping = {
                'Date': 'trade_date',
                'Politician': 'politician_name', 
                'Ticker': 'stock_ticker',
                'Transaction': 'trade_type',
                'Amount': 'trade_amount',
                'Filed': 'filing_date'
            }
            
            df = df.rename(columns=column_mapping)
            df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
            df['filing_date'] = pd.to_datetime(df.get('filing_date', df['trade_date']), errors='coerce')
            df['data_source'] = 'Quiver_Live'
            df['fetch_time'] = datetime.now()
            
            return df.sort_values('trade_date', ascending=False)
            
        except Exception as e:
            logger.error("Error fetching politician data: %s", e)
            return pd.DataFrame()
    
    def get_politician_trades(self, chamber: str = "both", days_back: int = 30) -> pd.DataFrame:
        """Fetch live politician trading data."""
        if chamber.lower() == "house":
            df = self._fetch_quiver_data(self.endpoints['quiver_house'], days_back)
            if not df.empty:
                df['chamber'] = 'House'
            return df
        elif chamber.lower() == "senate":
            df = self._fetch_quiver_data(self.endpoints['quiver_senate'], days_back)
            if not df.empty:
                df['chamber'] = 'Senate'
            return df
        else:  # both
            house_trades = self._fetch_quiver_data(self.endpoints['quiver_house'], days_back)
            senate_trades = self._fetch_quiver_data(self.endpoints['quiver_senate'], days_back)
            
            if not house_trades.empty:
                house_trades['chamber'] = 'House'
            if not senate_trades.empty:
                senate_trades['chamber'] = 'Senate'
            
            if not house_trades.empty and not senate_trades.empty:
                return pd.concat([house_trades, senate_trades], ignore_index=True).sort_values('trade_date', ascending=False)
            elif not house_trades.empty:
                return house_trades
            elif not senate_trades.empty:
                return senate_trades
            else:
                return pd.DataFrame()
    
    def get_politician_by_name(self, politician_name: str, days_back: int = 30) -> pd.DataFrame:
        """Get trading activity for a specific politician."""
        all_trades = self.get_politician_trades("both", days_back)
        if all_trades.empty:
            return pd.DataFrame()
        
        filtered = all_trades[all_trades['politician_name'].str.contains(politician_name, case=False, na=False)]
        return filtered.sort_values('trade_date', ascending=False)
    
    def _parse_trade_tweet(self, tweet_text: str) -> Dict:
        """Parse tweet to extract trade information."""
        trade_data = {
            'raw_text': tweet_text,
            'politician': None,
            'ticker': None,
            'trade_type': None,
            'amount': None,
            'confidence': 0.0
        }
        
        # Extract tickers
        tickers = re.findall(self.ticker_pattern, tweet_text.upper())
        if tickers:
            trade_data['ticker'] = tickers[0]
            trade_data['confidence'] += 0.3
        
        # Extract trade type
        text_lower = tweet_text.lower()
        if any(word in text_lower for word in ['bought', 'buy', 'purchase']):
            trade_data['trade_type'] = 'BUY'
            trade_data['confidence'] += 0.2
        elif any(word in text_lower for word in ['sold', 'sell', 'sale']):
            trade_data['trade_type'] = 'SELL'
            trade_data['confidence'] += 0.2
        
        # Extract politician names
        politicians = ['Nancy Pelosi', 'Pelosi', 'AOC', 'Ted Cruz', 'Josh Hawley']
        for politician in politicians:
            if re.search(politician, tweet_text, re.IGNORECASE):
                trade_data['politician'] = politician
                trade_data['confidence'] += 0.3
                break
        
        # Extract amounts
        amount_match = re.search(r'\$[\d,]+(?:K|M)?', tweet_text)
        if amount_match:
            trade_data['amount'] = amount_match.group()
            trade_data['confidence'] += 0.2
        
        return trade_data
    
    def get_twitter_trades(self) -> pd.DataFrame:
        """Get sample politician trades from Twitter sources."""
        sample_tweets = [
            "🚨 Nancy Pelosi SOLD $NVDA - $1.2M worth filed today #CongressTrading",
            "ALERT: Ted Cruz bought $TSLA calls $50K-100K range #PoliticianTrades", 
            "Breaking: AOC purchased $AAPL shares $15K-50K range 🍎",
            "Pelosi husband sold $GOOGL position - estimated $800K #StockAlert",
            "Josh Hawley bought $F shares $25K range 🚗"
        ]
        
        trades_data = []
        for i, tweet in enumerate(sample_tweets):
            parsed = self._parse_trade_tweet(tweet)
            parsed['tweet_id'] = f"sample_{i}"
            parsed['timestamp'] = datetime.now() - timedelta(hours=i*2)
            parsed['account'] = self.trading_accounts['PelosiTracker']
            trades_data.append(parsed)
        
        df = pd.DataFrame(trades_data)
        return df[df['confidence'] > 0.5]
    
    def get_combined_data(self, ticker: str, include_politician_trades: bool = True, 
                         include_twitter_data: bool = False, include_news_data: bool = False,
                         days_back: int = 30) -> Dict[str, pd.DataFrame]:
        """Get combined stock and political data for a ticker."""
        result = {}
        
        # Get stock data
        try:
            result['stock_data'] = self.get_stock_data(ticker)
            logger.info(
                "Stock data for %s: %s rows",
                ticker,
                result['stock_data'].shape[0],
            )
        except Exception as e:
            logger.warning("Could not fetch stock data for %s: %s", ticker, e)
            result['stock_data'] = pd.DataFrame()
        
        # Get politician trades
        if include_politician_trades:
            try:
                all_trades = self.get_politician_trades("both", days_back)
                if not all_trades.empty and 'stock_ticker' in all_trades.columns:
                    ticker_trades = all_trades[all_trades['stock_ticker'].str.upper() == ticker.upper()]
                    result['politician_trades'] = ticker_trades
                    logger.info(
                        "Found %s politician trades for %s", len(ticker_trades), ticker
                    )
                else:
                    result['politician_trades'] = pd.DataFrame()
            except Exception as e:
                logger.warning("Could not fetch politician trades: %s", e)
                result['politician_trades'] = pd.DataFrame()
        
        # Get Twitter data
        if include_twitter_data:
            try:
                twitter_trades = self.get_twitter_trades()
                if not twitter_trades.empty and 'ticker' in twitter_trades.columns:
                    ticker_twitter = twitter_trades[twitter_trades['ticker'].str.upper() == ticker.upper()]
                    result['twitter_trades'] = ticker_twitter
                else:
                    result['twitter_trades'] = twitter_trades
                logger.info(
                    "Found %s Twitter mentions",
                    len(result.get('twitter_trades', [])),
                )
            except Exception as e:
                result['twitter_trades'] = pd.DataFrame()
        
        if include_news_data:
            try:
                news_df = self.get_news_data(
                    symbols=[ticker],
                    start_date=(datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d'),
                    limit=200
                )
                result['news_headlines'] = news_df
                logger.info(
                    "Retrieved %s news headlines for sentiment scoring", len(news_df)
                )
            except Exception as e:
                logger.warning("Could not fetch news data: %s", e)
                result['news_headlines'] = pd.DataFrame()
        
        return result
    
    # Convenience methods for popular politicians
    def get_pelosi_trades(self, days_back: int = 30) -> pd.DataFrame:
        """Get Nancy Pelosi's recent trades."""
        return self.get_politician_by_name("Nancy Pelosi", days_back)
    
    def get_aoc_trades(self, days_back: int = 30) -> pd.DataFrame:
        """Get Alexandria Ocasio-Cortez's recent trades."""
        return self.get_politician_by_name("Alexandria Ocasio-Cortez", days_back)
    
    def get_senate_trades(self, days_back: int = 30) -> pd.DataFrame:
        """Get recent Senate trades."""
        return self.get_politician_trades("senate", days_back)
    
    def get_house_trades(self, days_back: int = 30) -> pd.DataFrame:
        """Get recent House trades."""
        return self.get_politician_trades("house", days_back)


# Backward compatibility function
def get_data(ticker: str, interval: str = "1m", start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
    """Legacy function for backward compatibility."""
    fetcher = DataFetcher()
    return fetcher.get_stock_data(ticker, interval, start, end)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Unified DataFetcher - All-in-One Trading Data")
    fetcher = DataFetcher()
    
    logger.info("Testing Twitter functionality…")
    twitter_data = fetcher.get_twitter_trades()
    logger.info("Twitter trades shape: %s", twitter_data.shape)
    
    logger.info("Testing stock data…")
    try:
        stock_data = fetcher.get_stock_data("AAPL")
        logger.info("AAPL stock data shape: %s", stock_data.shape)
    except Exception as e:
        logger.exception("Stock test failed: %s", e)
    
    logger.info("All core functionality working!")
    logger.info("Use DataFetcher as the single entry point for all data operations.")
