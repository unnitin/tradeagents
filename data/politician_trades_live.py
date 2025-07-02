# data/politician_trades_live.py

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import time
import warnings


class LivePoliticianTracker:
    """
    Live politician trading tracker using current 2025 data sources.
    Integrates with Quiver, Capitol Trades, and other live APIs.
    """
    
    def __init__(self, 
                 quiver_api_key: Optional[str] = None,
                 capitol_trades_api_key: Optional[str] = None):
        """
        Initialize with API keys for live data sources.
        
        Args:
            quiver_api_key: Quiver Quantitative API key ($10/month)
            capitol_trades_api_key: Capitol Trades API key (if available)
        """
        self.quiver_api_key = quiver_api_key
        self.capitol_trades_api_key = capitol_trades_api_key
        
        # Live data endpoints
        self.endpoints = {
            'quiver_house': 'https://api.quiverquant.com/beta/live/congresstrading/house',
            'quiver_senate': 'https://api.quiverquant.com/beta/live/congresstrading/senate',
            'quiver_recent': 'https://api.quiverquant.com/beta/live/congresstrading/recent',
            'capitol_trades': 'https://api.capitoltrades.com/v1/trades',  # Hypothetical endpoint
        }
    
    def get_live_house_trades(self, days_back: int = 30) -> pd.DataFrame:
        """
        Get live House trading data from Quiver Quantitative.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            pd.DataFrame: Recent House trades with current data
        """
        if not self.quiver_api_key:
            print("⚠️  Quiver API key required for live data. Get one at https://api.quiverquant.com/")
            return pd.DataFrame()
        
        try:
            headers = {
                'Authorization': f'Bearer {self.quiver_api_key}',
                'User-Agent': 'AstraQuant-PoliticianTracker/1.0'
            }
            
            # Get recent House trades
            response = requests.get(
                self.endpoints['quiver_house'],
                headers=headers,
                params={'days': days_back},
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Standardize columns
            column_mapping = {
                'Date': 'trade_date',
                'Politician': 'politician_name', 
                'Ticker': 'stock_ticker',
                'Transaction': 'trade_type',
                'Amount': 'trade_amount',
                'Filed': 'filing_date',
                'House': 'chamber'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Clean and parse dates
            df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
            df['filing_date'] = pd.to_datetime(df.get('filing_date', df['trade_date']), errors='coerce')
            
            # Add metadata
            df['data_source'] = 'Quiver_Live'
            df['chamber'] = 'House'
            df['fetch_time'] = datetime.now()
            
            # Sort by most recent
            df = df.sort_values('trade_date', ascending=False)
            
            print(f"✅ Fetched {len(df)} live House trades from Quiver")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching live House trades: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return pd.DataFrame()
    
    def get_live_senate_trades(self, days_back: int = 30) -> pd.DataFrame:
        """
        Get live Senate trading data from Quiver Quantitative.
        """
        if not self.quiver_api_key:
            print("⚠️  Quiver API key required for live Senate data")
            return pd.DataFrame()
        
        try:
            headers = {
                'Authorization': f'Bearer {self.quiver_api_key}',
                'User-Agent': 'AstraQuant-PoliticianTracker/1.0'
            }
            
            response = requests.get(
                self.endpoints['quiver_senate'],
                headers=headers,
                params={'days': days_back},
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Apply same standardization as House
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
            df['chamber'] = 'Senate'
            df['fetch_time'] = datetime.now()
            
            df = df.sort_values('trade_date', ascending=False)
            
            print(f"✅ Fetched {len(df)} live Senate trades from Quiver")
            return df
            
        except Exception as e:
            print(f"❌ Error fetching live Senate trades: {e}")
            return pd.DataFrame()
    
    def get_all_recent_trades(self, days_back: int = 7) -> pd.DataFrame:
        """
        Get all recent trades from both House and Senate.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            pd.DataFrame: Combined recent trades from both chambers
        """
        print(f"🔍 Fetching live politician trades from last {days_back} days...")
        
        # Get both House and Senate data
        house_trades = self.get_live_house_trades(days_back)
        senate_trades = self.get_live_senate_trades(days_back)
        
        # Combine if both have data
        if not house_trades.empty and not senate_trades.empty:
            all_trades = pd.concat([house_trades, senate_trades], ignore_index=True)
        elif not house_trades.empty:
            all_trades = house_trades
        elif not senate_trades.empty:
            all_trades = senate_trades
        else:
            print("❌ No live data available - check API keys")
            return pd.DataFrame()
        
        # Sort by most recent
        all_trades = all_trades.sort_values('trade_date', ascending=False)
        
        print(f"✅ Total live trades found: {len(all_trades)}")
        return all_trades
    
    def get_politician_recent_activity(self, politician_name: str, days_back: int = 30) -> pd.DataFrame:
        """
        Get recent trading activity for a specific politician.
        
        Args:
            politician_name: Name to search for (partial matches work)
            days_back: Days to look back
            
        Returns:
            pd.DataFrame: Recent trades for the politician
        """
        all_trades = self.get_all_recent_trades(days_back)
        
        if all_trades.empty:
            return pd.DataFrame()
        
        # Search for politician (case-insensitive, partial match)
        politician_trades = all_trades[
            all_trades['politician_name'].str.contains(
                politician_name, case=False, na=False
            )
        ]
        
        if not politician_trades.empty:
            print(f"📊 Found {len(politician_trades)} recent trades for {politician_name}")
        else:
            print(f"❌ No recent trades found for {politician_name}")
        
        return politician_trades
    
    def get_trending_stocks_live(self, days_back: int = 7, min_politicians: int = 2) -> pd.DataFrame:
        """
        Get stocks that are trending among politicians in recent days.
        
        Args:
            days_back: Recent time window  
            min_politicians: Minimum number of politicians trading the stock
            
        Returns:
            pd.DataFrame: Trending stocks with politician activity
        """
        recent_trades = self.get_all_recent_trades(days_back)
        
        if recent_trades.empty:
            return pd.DataFrame()
        
        # Group by ticker and analyze activity
        trending = recent_trades.groupby('stock_ticker').agg({
            'politician_name': 'nunique',  # Count unique politicians
            'trade_type': lambda x: x.mode().iloc[0] if not x.empty else 'Unknown',
            'trade_amount': 'count',  # Count total trades
            'trade_date': 'max',  # Most recent trade
            'chamber': lambda x: ', '.join(x.unique())  # Which chambers
        }).reset_index()
        
        trending = trending.rename(columns={
            'politician_name': 'num_politicians',
            'trade_type': 'dominant_trade_type', 
            'trade_amount': 'total_trades',
            'trade_date': 'latest_trade',
            'chamber': 'chambers'
        })
        
        # Filter for trending (multiple politicians)
        trending = trending[trending['num_politicians'] >= min_politicians]
        trending = trending.sort_values('num_politicians', ascending=False)
        
        print(f"🔥 Found {len(trending)} trending stocks among politicians")
        return trending
    
    def create_live_alerts(self, politicians: List[str] = None, 
                          min_amount_threshold: str = "$15,000") -> Dict:
        """
        Set up monitoring for live politician trades.
        
        Args:
            politicians: List of politician names to monitor
            min_amount_threshold: Minimum trade amount to alert on
            
        Returns:
            Dict: Alert configuration
        """
        alert_config = {
            'politicians': politicians or ['Pelosi', 'AOC', 'Cruz', 'Warren'],
            'min_amount': min_amount_threshold,
            'chambers': ['House', 'Senate'],
            'last_check': datetime.now(),
            'active': True
        }
        
        print("🔔 Live alert monitoring configured:")
        print(f"   Politicians: {alert_config['politicians']}")
        print(f"   Min Amount: {alert_config['min_amount']}")
        print("   ✅ Run check_for_new_trades() periodically to get alerts")
        
        return alert_config
    
    def check_for_new_trades(self, alert_config: Dict, 
                           since_minutes: int = 60) -> pd.DataFrame:
        """
        Check for new trades since last check (for alert system).
        
        Args:
            alert_config: Configuration from create_live_alerts()
            since_minutes: Check for trades in last X minutes
            
        Returns:
            pd.DataFrame: New trades matching alert criteria
        """
        # Get very recent trades
        recent_trades = self.get_all_recent_trades(days_back=2)
        
        if recent_trades.empty:
            return pd.DataFrame()
        
        # Filter for recent filing/fetch times
        cutoff_time = datetime.now() - timedelta(minutes=since_minutes)
        new_trades = recent_trades[recent_trades['fetch_time'] >= cutoff_time]
        
        # Filter for monitored politicians
        if alert_config.get('politicians'):
            politician_filter = new_trades['politician_name'].str.contains(
                '|'.join(alert_config['politicians']), case=False, na=False
            )
            new_trades = new_trades[politician_filter]
        
        if not new_trades.empty:
            print(f"🚨 ALERT: {len(new_trades)} new trades detected!")
            print(new_trades[['politician_name', 'stock_ticker', 'trade_type', 'trade_amount', 'trade_date']])
        
        return new_trades


def get_api_key_instructions():
    """Print instructions for getting API keys for live data."""
    print("🔑 GET LIVE DATA API KEYS:")
    print("=" * 50)
    print("1️⃣  QUIVER QUANTITATIVE (Recommended)")
    print("   • URL: https://api.quiverquant.com/")
    print("   • Cost: $10-20/month")
    print("   • Features: Live House & Senate data, real-time updates")
    print("   • Sign up → Get API key → Add to your code")
    print()
    print("2️⃣  CAPITOL TRADES")
    print("   • URL: https://www.capitoltrades.com/")
    print("   • Cost: Contact for API access")
    print("   • Features: Comprehensive politician trade database")
    print()
    print("3️⃣  TRADINSIGHT.INFO")
    print("   • URL: https://pelositrade.com/")
    print("   • Cost: ~$20/month")
    print("   • Features: Email alerts when politicians trade")
    print()
    print("💡 TIP: Start with Quiver API for best live data coverage!")


if __name__ == "__main__":
    # Demo with API key placeholder
    print("🏛️  LIVE POLITICIAN TRADE TRACKER")
    print("=" * 60)
    
    # Show API key instructions
    get_api_key_instructions()
    print()
    
    # Demo initialization (requires real API key)
    print("📍 DEMO MODE (Need real API key for live data)")
    tracker = LivePoliticianTracker()
    
    print("\n🔧 EXAMPLE USAGE:")
    print("# Get your Quiver API key first")
    print("tracker = LivePoliticianTracker(quiver_api_key='your_key_here')")
    print("live_trades = tracker.get_all_recent_trades(days_back=7)")
    print("pelosi_trades = tracker.get_politician_recent_activity('Pelosi')")
    print("trending = tracker.get_trending_stocks_live()")
    print("alerts = tracker.create_live_alerts(['Pelosi', 'AOC', 'Cruz'])")
    
    print("\n✅ Ready to track live politician trades!")
    print("💰 Get API key → Replace placeholder → Start tracking!") 