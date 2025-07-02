"""
Demo script for the Strategy Composer module.

This script demonstrates how to use the composer to:
1. Load strategies from configuration
2. Combine multiple strategies
3. Execute individual strategies (like quiver strategies)
4. Get trading signals for backtesting/execution
"""

import pandas as pd
import numpy as np
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

def main():
    """Main demonstration function."""
    print("=== Strategy Composer Demo ===\n")
    
    # Create sample data
    print("1. Creating sample market data...")
    df = create_sample_data()
    print(f"   Generated {len(df)} days of sample data")
    print(f"   Data range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"   Sample close prices: {df['close'].head(3).values}")
    
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
        signal_dates = signals[signals != 0].head(5)
        if len(signal_dates) > 0:
            print(f"   📅 Sample signals:")
            for date, signal in signal_dates.items():
                action = "BUY" if signal == 1 else "SELL"
                price = df.loc[date, 'close']
                print(f"      - {date.date()}: {action} at ${price:.2f}")
        
    except Exception as e:
        print(f"   ✗ Error executing combination: {e}")
    
    # Test individual strategy (sentiment_only - like quiver strategies)
    print("\n4. Testing individual strategy execution...")
    
    # First, let's create a simple news dataframe for sentiment strategy
    news_df = df.copy()
    # Add some dummy news headlines for demonstration
    sample_headlines = [
        "Company reports strong quarterly earnings, beats expectations",
        "Market volatility continues amid economic uncertainty",
        "Positive outlook for technology sector growth",
        "Regulatory concerns weigh on stock performance",
        "Strong consumer demand drives revenue growth"
    ]
    news_df['news_headline'] = np.random.choice(sample_headlines, len(news_df))
    
    # Note: sentiment_only is disabled in config, so let's try with an enabled strategy instead
    print("   Testing individual strategy combinations...")
    
    # Get info about combinations
    for combo_name in composer.list_available_combinations():
        combo_info = composer.get_combination_info(combo_name)
        print(f"   📋 {combo_name}:")
        print(f"      - Method: {combo_info.get('method')}")
        print(f"      - Strategies: {', '.join(combo_info.get('strategies', []))}")
        if combo_info.get('filters'):
            print(f"      - Filters: {', '.join(combo_info.get('filters'))}")
    
    print("\n5. Using convenience function...")
    try:
        # Use the convenience function to get signals
        quick_signals = get_signals('technical_ensemble', df)
        print(f"   ✓ Quick signals generated: {len(quick_signals)} total")
        print(f"   ✓ Signals match previous execution: {signals.equals(quick_signals)}")
    except Exception as e:
        print(f"   ✗ Error with convenience function: {e}")
    
    print("\n=== Demo Complete ===")
    print("The composer is ready to integrate with:")
    print("  → Backtesting modules")  
    print("  → Live execution systems")
    print("  → Portfolio management systems")

if __name__ == "__main__":
    main() 