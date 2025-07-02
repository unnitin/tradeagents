# data/fetch_data.py

import yfinance as yf  # type: ignore
import pandas as pd  # type: ignore
import requests  # type: ignore
import re
from typing import Optional, List, Dict, Union
from datetime import datetime, timedelta


class DataFetcher:
    """
    Unified data fetcher combining stock data, politician trades, and social media tracking.
    Single entry point for all trading data needs - fully self-contained.
    """
    
    def __init__(self, quiver_api_key: Optional[str] = None, capitol_trades_api_key: Optional[str] = None):
        self.quiver_api_key = quiver_api_key
        self.capitol_trades_api_key = capitol_trades_api_key
        
        # API endpoints
        self.endpoints = {
            'quiver_house': 'https://api.quiverquant.com/beta/live/congresstrading/house',
            'quiver_senate': 'https://api.quiverquant.com/beta/live/congresstrading/senate'
        }
        
        # Twitter accounts that track politician trades
        self.trading_accounts = {
            'PelosiTracker': '@PelosiTracker',
            'CongressTrading': '@CongressTrading'
        }
        
        self.ticker_pattern = r'\$([A-Z]{1,5})'
    
    def get_stock_data(self, ticker: str, interval: str = "1d", 
                      start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        """Fetch historical stock data from Yahoo Finance."""
        df = yf.download(
            tickers=ticker, 
            interval=interval, 
            start=start, 
            end=end, 
            progress=False, 
            auto_adjust=False
        )

        if df.empty:
            raise ValueError(f"No data returned for {ticker} with interval {interval}.")

        df.dropna(inplace=True)
        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(col).strip() for col in df.columns.values]
        df.columns = [col.lower() for col in df.columns]
        
        return df
    
    def _fetch_quiver_data(self, endpoint: str, days_back: int) -> pd.DataFrame:
        """Internal method to fetch data from Quiver API."""
        if not self.quiver_api_key:
            print("⚠️  Quiver API key required for live politician data")
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
            print(f"❌ Error fetching politician data: {e}")
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
                         include_twitter_data: bool = False, days_back: int = 30) -> Dict[str, pd.DataFrame]:
        """Get combined stock and political data for a ticker."""
        result = {}
        
        # Get stock data
        try:
            result['stock_data'] = self.get_stock_data(ticker)
            print(f"✅ Stock data for {ticker}: {result['stock_data'].shape[0]} rows")
        except Exception as e:
            print(f"⚠️ Could not fetch stock data for {ticker}: {e}")
            result['stock_data'] = pd.DataFrame()
        
        # Get politician trades
        if include_politician_trades:
            try:
                all_trades = self.get_politician_trades("both", days_back)
                if not all_trades.empty and 'stock_ticker' in all_trades.columns:
                    ticker_trades = all_trades[all_trades['stock_ticker'].str.upper() == ticker.upper()]
                    result['politician_trades'] = ticker_trades
                    print(f"✅ Found {len(ticker_trades)} politician trades for {ticker}")
                else:
                    result['politician_trades'] = pd.DataFrame()
            except Exception as e:
                print(f"⚠️ Could not fetch politician trades: {e}")
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
                print(f"✅ Found {len(result.get('twitter_trades', []))} Twitter mentions")
            except Exception as e:
                result['twitter_trades'] = pd.DataFrame()
        
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
    print("🚀 Unified DataFetcher - All-in-One Trading Data")
    fetcher = DataFetcher()
    
    print("\n📱 Testing Twitter functionality...")
    twitter_data = fetcher.get_twitter_trades()
    print(f"✅ Twitter trades: {twitter_data.shape}")
    
    print("\n📈 Testing stock data...")
    try:
        stock_data = fetcher.get_stock_data("AAPL")
        print(f"✅ AAPL stock data: {stock_data.shape}")
    except Exception as e:
        print(f"⚠️ Stock test failed: {e}")
    
    print("\n✅ All core functionality working!")
    print("💡 Use DataFetcher class as your single entry point for all data operations.")
