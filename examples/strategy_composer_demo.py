"""
Strategy Composer Demo

This script demonstrates how to use the composer to:
1. Load strategies from configuration
2. Combine multiple strategies  
3. Execute individual strategies (like quiver strategies)
4. Get trading signals for backtesting/execution
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the parent directory to the path so we can import from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from composer import create_composer, get_signals

def create_sample_data():
    """Create sample market data for demonstration."""
    # Create sample price data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Generate realistic price data
    price = 100
    prices = []
    for _ in range(len(dates)):
        price += np.random.normal(0, 2)  # Random walk with noise
        prices.append(price)
    
    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'volume': np.random.randint(1000000, 5000000, len(dates))
    })
    df.set_index('date', inplace=True)
    
    # Add technical indicators (normally would be done by data preprocessing)
    df['sma_20'] = df['close'].rolling(20).mean()
    df['sma_50'] = df['close'].rolling(50).mean()
    df['rsi'] = calculate_rsi(df['close'])
    df['macd'], df['macd_signal'] = calculate_macd(df['close'])
    df['bb_upper'], df['bb_lower'] = calculate_bollinger_bands(df['close'])
    df['atr'] = calculate_atr(df)
    
    return df

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    return macd, macd_signal

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, lower

def calculate_atr(df, period=14):
    """Calculate Average True Range."""
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()

def demo_politician_tracking():
    """Demonstrate politician tracking strategies."""
    print("\n" + "="*60)
    print("🏛️  POLITICIAN TRACKING STRATEGIES DEMO")
    print("="*60)
    
    df = create_sample_data()
    
    print("📋 Available Politician Tracking Strategies:")
    print("   • PoliticianFollowingStrategy - Follow all politicians")
    print("   • PelosiTrackingStrategy - Focus on Nancy Pelosi trades")
    print("   • CongressMomentumStrategy - Detect Congress momentum")
    
    try:
        composer = create_composer()
        
        # Test politician combinations (even though they're disabled by default)
        politician_combos = ['pelosi_only', 'politician_ensemble', 'hybrid_political']
        
        for combo_name in politician_combos:
            print(f"\n🔍 Testing: {combo_name}")
            print("-" * 40)
            
            try:
                combo_info = composer.get_combination_info(combo_name)
                print(f"   Method: {combo_info.get('method')}")
                strategies_list = combo_info.get('strategies', [])
                if strategies_list:
                    print(f"   Strategies: {', '.join(strategies_list)}")
                
                # Try to get signals (will likely show warning about API access)
                signals = get_signals(combo_name, df)
                
                # Show signal statistics
                total_signals = (signals != 0).sum()
                buy_signals = (signals == 1).sum()
                sell_signals = (signals == -1).sum()
                
                print(f"   📈 Buy signals: {buy_signals}")
                print(f"   📉 Sell signals: {sell_signals}")
                print(f"   📊 Total signals: {total_signals}")
                
                if total_signals > 0:
                    print(f"   ✅ Generated {total_signals} signals")
                else:
                    print("   ⚠️  No signals (strategies disabled - need API access)")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Could not initialize composer: {e}")
    
    print("\n💡 Politician Tracking Benefits:")
    print("   • Follow Congress trades for market insights")
    print("   • Detect patterns in political trading behavior")
    print("   • Combine with technical analysis for hybrid approach")
    print("   • Track specific politicians (Pelosi, Cruz, etc.)")
    
    print("\n⚙️  To Enable Politician Tracking:")
    print("   1. Get Quiver API key (quiverquant.com)")
    print("   2. Set enabled: true in config/strategies.yaml")
    print("   3. Configure your preferred politicians and parameters")

def main():
    """Main demonstration function."""
    print("=== Strategy Composer Demo ===\n")
    
    # Create sample data
    print("1. Creating sample market data...")
    df = create_sample_data()
    print(f"   Generated {len(df)} days of sample data")
    print(f"   Data range: {df.index[0]} to {df.index[-1]}")
    print(f"   Sample close prices: {df['close'].iloc[:3].values}")
    
    # Create composer
    print("\n2. Initializing Strategy Composer...")
    try:
        composer = create_composer()
        print("   ✓ Composer initialized successfully")
        print(f"   ✓ Loaded {len(composer.list_available_strategies())} strategies")
        print(f"   ✓ Available combinations: {composer.list_available_combinations()}")
    except Exception as e:
        print(f"   ✗ Error initializing composer: {e}")
        return
    
    # Execute technical ensemble combination
    print("\n3. Executing 'technical_ensemble' combination...")
    try:
        signals = composer.execute_combination('technical_ensemble', df)
        print(f"   ✓ Generated {len(signals)} signals")
        
        # Analyze signals
        buy_signals = (signals == 1).sum()
        sell_signals = (signals == -1).sum()
        hold_signals = (signals == 0).sum()
        
        print(f"   📊 Signal breakdown:")
        print(f"      - Buy signals (1):  {buy_signals}")
        print(f"      - Sell signals (-1): {sell_signals}")
        print(f"      - Hold signals (0):  {hold_signals}")
        
        # Show some sample signals
        signal_dates = signals[signals != 0].iloc[:5]
        if len(signal_dates) > 0:
            print(f"   📅 Sample signals:")
            for date, signal in signal_dates.items():
                action = "BUY" if signal == 1 else "SELL"
                price = df.loc[date, 'close']
                print(f"      - {date}: {action} at ${price:.2f}")
        
    except Exception as e:
        print(f"   ✗ Error executing combination: {e}")
    
    # Test individual strategy (sentiment_only - like quiver strategies)
    print("\n4. Testing individual strategy execution...")
    try:
        # Test sentiment-based strategy
        signals = get_signals('sentiment_only', df)
        print(f"   ✓ Sentiment strategy generated {len(signals)} signals")
        
        sentiment_signals = (signals != 0).sum()
        print(f"   📊 Active sentiment signals: {sentiment_signals}")
        
        if sentiment_signals > 0:
            print("   ✅ Sentiment analysis working")
        else:
            print("   ⚠️  No sentiment signals (may need API access)")
            
    except Exception as e:
        print(f"   ✗ Error with sentiment strategy: {e}")
    
    # Test combination methods
    print("\n5. Testing different combination methods...")
    try:
        methods = ['majority_vote', 'weighted_average', 'unanimous']
        for method in methods:
            print(f"\n   🔄 Testing {method} method...")
            try:
                # This would test different combination approaches
                signals = composer.execute_combination('technical_ensemble', df, method=method)
                active_signals = (signals != 0).sum()
                print(f"      ✓ {method}: {active_signals} active signals")
            except Exception as e:
                print(f"      ✗ {method}: {e}")
                
    except Exception as e:
        print(f"   ✗ Error testing combination methods: {e}")
    
    # Demonstrate politician tracking
    demo_politician_tracking()
    
    # Summary
    print("\n" + "="*60)
    print("📊 DEMO SUMMARY")
    print("="*60)
    print("✅ Successfully demonstrated:")
    print("   • Strategy composer initialization")
    print("   • Technical ensemble execution")
    print("   • Signal generation and analysis")
    print("   • Multiple combination methods")
    print("   • Politician tracking capabilities")
    print("   • Individual strategy execution")
    
    print("\n🎯 Next Steps:")
    print("   • Integrate with backtest module for performance analysis")
    print("   • Configure API keys for real-time data")
    print("   • Customize strategy parameters in config/strategies.yaml")
    print("   • Add your own custom strategies")
    print("   • Use with live trading systems")
    
    print("\n📝 Notes:")
    print("   • Some strategies require API access (Quiver, news APIs)")
    print("   • Politician tracking is disabled by default")
    print("   • All strategies can be backtested using the backtest module")
    print("   • See config/strategies.yaml for configuration options")

if __name__ == "__main__":
    main() 