# examples/politician_tracking_example.py

"""
EASY POLITICIAN TRADE TRACKING GUIDE
=====================================

This script demonstrates the easiest ways to track politician trades,
from free Twitter alerts to paid API services.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.twitter_politician_tracker import TwitterPoliticianTracker
from data.politician_trades_live import LivePoliticianTracker, get_api_key_instructions


def show_all_options():
    """Show all politician tracking options from easiest to advanced."""
    print("🏛️  POLITICIAN TRADE TRACKING - ALL OPTIONS")
    print("=" * 70)
    
    print("\n🥇 OPTION 1: TWITTER/X (EASIEST & FREE)")
    print("-" * 45)
    print("✅ Pros: FREE, Real-time, Mobile alerts, No setup needed")
    print("⚠️  Cons: Manual monitoring, 45-day filing delays")
    print("📱 Setup: Just follow @PelosiTracker and enable notifications!")
    
    # Demo Twitter tracker
    twitter_tracker = TwitterPoliticianTracker()
    print("\n📊 Twitter Demo:")
    twitter_tracker.simulate_live_monitoring()
    
    print("\n" + "="*70)
    print("\n🥈 OPTION 2: PAID API SERVICES")
    print("-" * 35)
    
    # Show API options
    get_api_key_instructions()
    
    print("\n" + "="*70)
    print("\n🥉 OPTION 3: HYBRID APPROACH (RECOMMENDED)")
    print("-" * 45)
    print("🔸 Use Twitter for real-time alerts (free)")
    print("🔸 Use Quiver API for automated trading ($10/month)")
    print("🔸 Use TradeInsight for email notifications ($20/month)")
    print("🔸 Combine all three for comprehensive coverage")


def twitter_setup_guide():
    """Detailed Twitter setup guide."""
    print("\n📱 TWITTER SETUP GUIDE")
    print("=" * 30)
    
    steps = [
        "1️⃣  Go to Twitter/X and follow these accounts:",
        "   • @PelosiTracker (1M+ followers)",
        "   • @CongressTrading",
        "   • @CapitolTrades_", 
        "   • @QuiverQuant",
        "",
        "2️⃣  Enable notifications:",
        "   • Click the bell icon on each account",
        "   • Select 'All Tweets' for immediate alerts",
        "",
        "3️⃣  Create a Twitter List:",
        "   • Go to Lists → Create new list",
        "   • Name it 'Politician Trades'",
        "   • Add all the accounts above",
        "",
        "4️⃣  Mobile Setup:",
        "   • Download Twitter mobile app",
        "   • Enable push notifications",
        "   • You'll get alerts instantly!",
        "",
        "💡 ADVANCED: Use TweetDeck for desktop monitoring"
    ]
    
    for step in steps:
        print(step)


def simulate_trading_day():
    """Simulate what a day of politician trade monitoring looks like."""
    print("\n📈 TYPICAL DAY OF POLITICIAN TRADE MONITORING")
    print("=" * 55)
    
    timeline = [
        "9:00 AM - Market opens",
        "9:15 AM - 🔔 Twitter Alert: @PelosiTracker posts Nancy Pelosi bought $NVDA",
        "9:16 AM - Check stock price: $NVDA up 2% pre-market",
        "9:30 AM - Consider following the trade",
        "10:45 AM - 🔔 Email Alert: TradeInsight.info confirms the trade",
        "2:15 PM - 🔔 Twitter Alert: New AOC trade in $TSLA",
        "2:20 PM - Quick analysis: EV sector trending among politicians",
        "3:45 PM - Review performance of politician-followed stocks",
        "4:00 PM - Market closes, plan tomorrow's watchlist"
    ]
    
    for event in timeline:
        print(f"   {event}")
    
    print("\n💰 RESULT: Easy, real-time awareness of politician trades!")


def quick_start_guide():
    """5-minute quick start guide."""
    print("\n⚡ 5-MINUTE QUICK START")
    print("=" * 25)
    
    print("Want to start tracking politician trades RIGHT NOW? Here's how:")
    print()
    print("1. Open Twitter/X on your phone 📱")
    print("2. Search for '@PelosiTracker' 🔍") 
    print("3. Follow the account and hit the bell icon 🔔")
    print("4. Done! You'll get alerts when politicians trade 🚨")
    print()
    print("That's it! In 5 minutes you're tracking the most watched politician trades.")
    print()
    print("💡 NEXT STEPS:")
    print("   • Follow @CongressTrading for more politicians")
    print("   • Create a Twitter list for easy monitoring")
    print("   • Consider paid APIs for automated trading")


if __name__ == "__main__":
    # Show complete guide
    show_all_options()
    
    print("\n" + "="*70)
    
    # Quick start for impatient users
    quick_start_guide()
    
    print("\n" + "="*70)
    
    # Detailed Twitter setup
    twitter_setup_guide()
    
    print("\n" + "="*70)
    
    # Show what a typical day looks like
    simulate_trading_day()
    
    print("\n" + "="*70)
    print("\n🎯 FINAL RECOMMENDATION:")
    print("Start with Twitter for FREE real-time alerts,")
    print("then add paid APIs if you want automation.")
    print("Twitter is honestly the easiest way to get started! 📱✨") 