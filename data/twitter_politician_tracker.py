# data/twitter_politician_tracker.py

import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd


class TwitterPoliticianTracker:
    """
    Free alternative to track politician trades via Twitter/X accounts.
    Monitors popular accounts like @PelosiTracker for trade alerts.
    """
    
    def __init__(self):
        """Initialize Twitter politician tracker."""
        # Popular accounts that track politician trades
        self.trading_accounts = {
            'PelosiTracker': '@PelosiTracker',
            'CongressTrading': '@CongressTrading', 
            'CapitolTrades': '@CapitolTrades_',
            'QuiverQuant': '@QuiverQuant'
        }
        
        # Keywords to identify trade posts
        self.trade_keywords = [
            'bought', 'sold', 'purchase', 'sale', 'trade', 'filing',
            '$', 'shares', 'stock', 'options', 'calls', 'puts'
        ]
        
        # Stock ticker pattern (e.g., $NVDA, $TSLA, etc.)
        self.ticker_pattern = r'\$([A-Z]{1,5})'
        
    def parse_trade_tweet(self, tweet_text: str) -> Dict:
        """
        Parse a tweet to extract trade information.
        
        Args:
            tweet_text: Raw tweet text
            
        Returns:
            Dict: Parsed trade data
        """
        trade_data = {
            'raw_text': tweet_text,
            'politician': None,
            'ticker': None,
            'trade_type': None,
            'amount': None,
            'date': None,
            'confidence': 0.0
        }
        
        # Extract stock tickers
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
        
        # Extract politician name (common patterns)
        politician_patterns = [
            r'Nancy Pelosi', r'Pelosi', r'AOC', r'Alexandria Ocasio-Cortez',
            r'Ted Cruz', r'Elizabeth Warren', r'Josh Hawley'
        ]
        
        for pattern in politician_patterns:
            if re.search(pattern, tweet_text, re.IGNORECASE):
                trade_data['politician'] = pattern.replace(r'\\b', '').replace(r'\\s+', ' ')
                trade_data['confidence'] += 0.3
                break
        
        # Extract amounts (rough patterns)
        amount_patterns = [
            r'\$[\d,]+(?:K|M)?',  # $1,000, $1.5M, etc.
            r'[\d,]+\s*(?:thousand|million|k|m)',  # 1,000 thousand, 1.5 million
        ]
        
        for pattern in amount_patterns:
            amounts = re.findall(pattern, tweet_text, re.IGNORECASE)
            if amounts:
                trade_data['amount'] = amounts[0]
                trade_data['confidence'] += 0.2
                break
        
        return trade_data
    
    def get_sample_trades(self) -> pd.DataFrame:
        """
        Return sample trades that would typically be found on Twitter.
        This simulates what you'd get from live Twitter feeds.
        """
        sample_tweets = [
            "🚨 Nancy Pelosi SOLD $NVDA - $1.2M worth of shares filed today. Stock down 3% since trade. #CongressTrading",
            "ALERT: Ted Cruz bought $TSLA calls worth $50K-100K range. Filed 2 days ago. 📈 #PoliticianTrades",
            "Breaking: AOC purchased $AAPL shares - $15K-50K range. Trade executed last week. 🍎",
            "Pelosi's husband sold $GOOGL position - estimated $800K. Market reacting. #StockAlert",
            "Josh Hawley filed disclosure: Bought $F (Ford) shares $25K range. Auto sector play? 🚗"
        ]
        
        trades_data = []
        for i, tweet in enumerate(sample_tweets):
            parsed = self.parse_trade_tweet(tweet)
            parsed['tweet_id'] = f"sample_{i}"
            parsed['timestamp'] = datetime.now() - timedelta(hours=i*2)
            parsed['account'] = self.trading_accounts['PelosiTracker']
            trades_data.append(parsed)
        
        df = pd.DataFrame(trades_data)
        df = df[df['confidence'] > 0.5]  # Filter for high-confidence trades
        
        print(f"📱 Parsed {len(df)} high-confidence trades from Twitter")
        return df
    
    def create_twitter_alerts(self, keywords: List[str] = None) -> Dict:
        """
        Set up configuration for Twitter-based alerts.
        
        Args:
            keywords: Additional keywords to monitor
            
        Returns:
            Dict: Alert configuration
        """
        default_keywords = ['Pelosi', 'bought', 'sold', '$', 'filing']
        alert_keywords = keywords or default_keywords
        
        alert_config = {
            'accounts_to_monitor': list(self.trading_accounts.values()),
            'keywords': alert_keywords,
            'min_confidence': 0.6,
            'notify_immediately': True,
            'created_at': datetime.now()
        }
        
        print("🔔 Twitter Alert Configuration:")
        print(f"   Monitoring: {len(alert_config['accounts_to_monitor'])} accounts")
        print(f"   Keywords: {alert_config['keywords']}")
        print("   💡 Set up Twitter notifications for these accounts!")
        
        return alert_config
    
    def get_setup_instructions(self) -> str:
        """Return instructions for setting up Twitter monitoring."""
        instructions = """
        📱 TWITTER POLITICIAN TRADE SETUP:
        ================================
        
        1️⃣  FOLLOW KEY ACCOUNTS:
           • @PelosiTracker (1M+ followers)
           • @CongressTrading  
           • @CapitolTrades_
           • @QuiverQuant
        
        2️⃣  ENABLE NOTIFICATIONS:
           • Turn on tweet notifications for these accounts
           • Create Twitter lists for easier monitoring
           • Use TweetDeck for multiple account monitoring
        
        3️⃣  SET UP KEYWORDS:
           • Use Twitter's search: "from:@PelosiTracker (bought OR sold)"
           • Monitor hashtags: #CongressTrading #PoliticianTrades
           • Set up Google Alerts for "politician stock trades"
        
        4️⃣  MOBILE ALERTS:
           • Download Twitter mobile app
           • Enable push notifications
           • Create custom Twitter lists
        
        💰 COST: FREE!
        ⚡ SPEED: Real-time (as fast as accounts post)
        📊 DATA: Immediate but limited to what accounts share
        
        🚨 LIMITATIONS:
           • Still subject to 45-day filing delays
           • Depends on account owners posting
           • Manual interpretation needed
           • No historical data API
        """
        return instructions
    
    def simulate_live_monitoring(self) -> None:
        """
        Simulate what live Twitter monitoring would look like.
        """
        print("🔴 LIVE TWITTER MONITORING SIMULATION")
        print("=" * 50)
        
        # Get sample trades
        sample_trades = self.get_sample_trades()
        
        print("\n📱 Recent Twitter Alerts:")
        for _, trade in sample_trades.iterrows():
            confidence_emoji = "🔥" if trade['confidence'] > 0.8 else "⚠️"
            print(f"\n{confidence_emoji} TRADE ALERT ({trade['confidence']:.1%} confidence)")
            print(f"   Politician: {trade['politician']}")
            print(f"   Ticker: ${trade['ticker']}")
            print(f"   Action: {trade['trade_type']}")
            print(f"   Amount: {trade['amount']}")
            print(f"   Source: {trade['account']}")
            print(f"   Raw: {trade['raw_text'][:80]}...")
        
        print("\n✅ This is what you'd see with live Twitter monitoring!")
        print("💡 Much easier than API integration - just follow the accounts!")


if __name__ == "__main__":
    print("📱 TWITTER POLITICIAN TRADE TRACKER")
    print("=" * 60)
    
    tracker = TwitterPoliticianTracker()
    
    # Show setup instructions
    print(tracker.get_setup_instructions())
    
    # Run simulation
    tracker.simulate_live_monitoring()
    
    # Show alert config
    alerts = tracker.create_twitter_alerts()
    
    print("\n🎯 BOTTOM LINE:")
    print("Twitter is the EASIEST way to track politician trades!")
    print("Just follow @PelosiTracker and enable notifications. 🔔") 