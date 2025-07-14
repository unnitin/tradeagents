#!/usr/bin/env python3
"""
Complete Trading Workflow Example

This example demonstrates the complete end-to-end trading workflow:
1. 📊 Data Fetching - Get historical stock data and market information
2. 📈 Strategy Creation - Define and configure trading strategies
3. 🔍 Filter Setup - Apply various filtering techniques
4. 🚀 Backtesting - Run comprehensive performance analysis
5. 📋 Results Analysis - Interpret and visualize results

This is a one-stop example showing how all components work together.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import all required modules
from data.fetch_data import DataFetcher
from strategies import SMACrossover, RSIReversion, MACDCross, BollingerBounce
from filters import StockFilter, TimeFilter, LiquidityFilter, CompositeFilter
from backtest.engine import BacktestEngine, BacktestConfig, create_backtest_engine
from backtest.results import save_results, load_results
from config.filter_config import FilterConfigManager


def print_section(title: str, description: str = ""):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"📊 {title}")
    print("=" * 80)
    if description:
        print(f"{description}\n")


def step_1_fetch_data():
    """Step 1: Fetch historical stock data for multiple symbols."""
    print_section(
        "STEP 1: DATA FETCHING",
        "Fetching historical stock data for our trading universe"
    )
    
    # Initialize data fetcher
    fetcher = DataFetcher()
    
    # Define our stock universe
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY']
    
    # Date range for our analysis
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    print(f"📈 Fetching data for symbols: {symbols}")
    print(f"📅 Date range: {start_date} to {end_date}")
    
    # Fetch data for each symbol
    stock_data = {}
    for symbol in symbols:
        try:
            print(f"   🔄 Fetching {symbol}...")
            data = fetcher.get_stock_data(
                ticker=symbol,
                start=start_date,
                end=end_date
            )
            
            # Don't add symbol column here since it will be added by concat keys
            stock_data[symbol] = data
            
            print(f"   ✅ {symbol}: {len(data)} records")
            
        except Exception as e:
            print(f"   ❌ Error fetching {symbol}: {e}")
            continue
    
    # Check if we have any data, if not use mock data
    if not stock_data:
        print("\n⚠️ No data fetched due to network issues. Using mock data for demonstration...")
        stock_data = create_mock_data(symbols, start_date, end_date)
    
    # Combine all data into a single DataFrame
    combined_data = pd.concat(stock_data.values(), keys=stock_data.keys())
    combined_data.index.names = ['Symbol', 'Date']
    combined_data = combined_data.reset_index()
    
    # Remove duplicate Symbol column if it exists
    if 'Symbol' in combined_data.columns and combined_data.columns.tolist().count('Symbol') > 1:
        combined_data = combined_data.loc[:, ~combined_data.columns.duplicated()]
    
    print(f"\n📊 Total records fetched: {len(combined_data)}")
    print(f"📈 Data columns: {list(combined_data.columns)}")
    
    return combined_data, stock_data


def create_mock_data(symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """Create mock stock data when real data is unavailable."""
    print("🔧 Generating mock data for demonstration...")
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    stock_data = {}
    
    for symbol in symbols:
        # Generate realistic price data
        initial_price = np.random.uniform(100, 300)
        returns = np.random.normal(0.001, 0.02, len(date_range))
        
        prices = [initial_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        closes = np.array(prices)
        opens = closes * np.random.uniform(0.99, 1.01, len(closes))
        highs = np.maximum(opens, closes) * np.random.uniform(1.0, 1.05, len(closes))
        lows = np.minimum(opens, closes) * np.random.uniform(0.95, 1.0, len(closes))
        volumes = np.random.uniform(1000000, 10000000, len(closes))
        
        # Create DataFrame
        data = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes,
            'Adj Close': closes
        }, index=date_range)
        
        # Add technical indicators
        data['sma_20'] = data['Close'].rolling(20).mean()
        data['sma_50'] = data['Close'].rolling(50).mean()
        data['rsi_14'] = calculate_rsi(data['Close'], 14)
        data['macd'], data['macd_signal'] = calculate_macd(data['Close'])
        data['bb_upper_20'], data['bb_lower_20'] = calculate_bollinger_bands(data['Close'], 20)
        
        # Don't add symbol column here since it will be added by concat keys
        stock_data[symbol] = data
        print(f"   ✅ {symbol}: {len(data)} mock records generated")
    
    return stock_data


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """Calculate MACD indicator."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    return macd, macd_signal


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> tuple:
    """Calculate Bollinger Bands."""
    rolling_mean = prices.rolling(window=period).mean()
    rolling_std = prices.rolling(window=period).std()
    upper_band = rolling_mean + (rolling_std * std_dev)
    lower_band = rolling_mean - (rolling_std * std_dev)
    return upper_band, lower_band


def step_2_create_strategies():
    """Step 2: Create and configure various trading strategies."""
    print_section(
        "STEP 2: STRATEGY CREATION",
        "Creating and configuring multiple trading strategies"
    )
    
    strategies = {
        'SMA_Crossover': SMACrossover(fast=10, slow=30),
        'RSI_Reversion': RSIReversion(rsi_col="rsi_14", low_thresh=30, high_thresh=70),
        'MACD_Cross': MACDCross(macd_col="macd", signal_col="macd_signal"),
        'Bollinger_Bounce': BollingerBounce(bb_window=20)
    }
    
    print("📈 Created strategies:")
    for name, strategy in strategies.items():
        print(f"   🔸 {name}: {strategy.__class__.__name__}")
        # Print basic info about the strategy
        strategy_params = {k: v for k, v in strategy.__dict__.items() if not k.startswith('_')}
        print(f"      Parameters: {strategy_params}")
    
    return strategies


def step_3_setup_filters(strategies: Dict):
    """Step 3: Configure advanced filtering for our strategies."""
    print_section(
        "STEP 3: FILTER CONFIGURATION",
        "Setting up basic, symbol-specific, and dynamic filters"
    )
    
    # Get one strategy to demonstrate filtering (all strategies have same capabilities)
    strategy = strategies['SMA_Crossover']
    
    print("🔍 Setting up basic filters...")
    # Basic filters
    stock_filter = StockFilter(
        min_price=10.0,
        max_price=500.0,
        min_volume=100000
    )
    
    time_filter = TimeFilter(
        start_time="09:30",
        end_time="16:00",
        exclude_market_holidays=True
    )
    
    liquidity_filter = LiquidityFilter(
        min_avg_volume=500000,
        min_dollar_volume=1000000
    )
    
    # Add basic filters to strategy
    strategy.add_filter(stock_filter)
    strategy.add_filter(time_filter)
    strategy.add_filter(liquidity_filter)
    
    print("🎯 Setting up symbol-specific filters...")
    # Symbol-specific filters - different rules for different stocks
    symbol_filters = {
        'AAPL': {
            'min_price': 150.0,
            'max_price': 200.0,
            'min_volume': 1000000
        },
        'GOOGL': {
            'min_price': 100.0,
            'max_price': 150.0,
            'min_volume': 500000
        },
        'TSLA': {
            'min_price': 200.0,
            'max_price': 300.0,
            'min_volume': 2000000
        }
    }
    
    strategy.set_symbol_filters(symbol_filters)
    
    print("⚡ Setting up dynamic filters...")
    # Dynamic filters - adapt based on market conditions
    def dynamic_volume_filter(data, context):
        """Increase volume requirements during high volatility."""
        if context.get('market_volatility', 0) > 0.02:
            return data['Volume'] > 2000000
        return data['Volume'] > 1000000
    
    def dynamic_price_filter(data, context):
        """Adjust price filters based on market trend."""
        if context.get('market_trend', 'neutral') == 'bullish':
            return data['Close'] > data['Open']  # Only long positions in bull market
        return True
    
    strategy.set_dynamic_filters({
        'volume_filter': dynamic_volume_filter,
        'price_filter': dynamic_price_filter
    })
    
    print("✅ Filter configuration complete!")
    # Print filter info if available
    try:
        filter_info = strategy.get_advanced_filter_info()
        print(f"   📊 Filter info: {filter_info}")
    except AttributeError:
        print("   📊 Filter info: Advanced filtering configured")
    
    return strategy


def step_4_run_backtest(strategy, stock_data: Dict):
    """Step 4: Execute comprehensive backtesting."""
    print_section(
        "STEP 4: BACKTESTING EXECUTION",
        "Running comprehensive backtest with our configured strategy"
    )
    
    # Create backtest engine
    engine = create_backtest_engine()
    
    # Configure backtest parameters
    config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.001,
        slippage_rate=0.001
    )
    
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    print("🚀 Running backtest...")
    print(f"   📅 Period: {start_date} to {end_date}")
    print(f"   💰 Initial capital: ${config.initial_capital:,.2f}")
    print(f"   💸 Commission: {config.commission_rate*100:.1f}%")
    
    # Run backtest for each stock
    all_results = {}
    
    for symbol, data in stock_data.items():
        print(f"\n   🔄 Testing {symbol}...")
        
        try:
            # Run backtest
            results = engine.run_backtest(
                strategy=strategy,
                symbols=[symbol],
                start_date=start_date,
                end_date=end_date
            )
            
            all_results[symbol] = results
            
            # Print key metrics
            metrics = results.metrics
            print(f"      📈 Total Return: {metrics.total_return*100:.2f}%")
            print(f"      📊 Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
            print(f"      🎯 Win Rate: {metrics.win_rate*100:.2f}%")
            print(f"      🔢 Total Trades: {metrics.total_trades}")
            
        except Exception as e:
            print(f"      ❌ Error testing {symbol}: {e}")
            continue
    
    return all_results


def step_5_analyze_results(results: Dict):
    """Step 5: Comprehensive results analysis and visualization."""
    print_section(
        "STEP 5: RESULTS ANALYSIS",
        "Analyzing backtest results and generating insights"
    )
    
    if not results:
        print("❌ No results to analyze!")
        return
    
    # Aggregate results
    total_return = 0
    total_trades = 0
    win_rates = []
    sharpe_ratios = []
    
    print("📊 Individual Stock Performance:")
    print("-" * 60)
    
    for symbol, result in results.items():
        metrics = result.metrics
        
        ret = metrics.total_return * 100
        sharpe = metrics.sharpe_ratio
        win_rate = metrics.win_rate * 100
        trades = metrics.total_trades
        
        total_return += ret
        total_trades += trades
        if sharpe != 0:
            sharpe_ratios.append(sharpe)
        if win_rate != 0:
            win_rates.append(win_rate)
        
        print(f"🔸 {symbol:6} | Return: {ret:6.2f}% | Sharpe: {sharpe:5.2f} | Win Rate: {win_rate:5.1f}% | Trades: {trades:3d}")
    
    # Portfolio summary
    print("\n📈 Portfolio Summary:")
    print("-" * 40)
    print(f"🎯 Average Return: {total_return/len(results):.2f}%")
    print(f"📊 Average Sharpe: {np.mean(sharpe_ratios):.2f}" if sharpe_ratios else "📊 Average Sharpe: N/A")
    print(f"🎲 Average Win Rate: {np.mean(win_rates):.1f}%" if win_rates else "🎲 Average Win Rate: N/A")
    print(f"🔢 Total Trades: {total_trades}")
    
    # Risk analysis
    print("\n⚠️ Risk Analysis:")
    print("-" * 30)
    returns = [results[symbol].metrics.total_return for symbol in results]
    if returns:
        volatility = np.std(returns) * 100
        print(f"📉 Return Volatility: {volatility:.2f}%")
        print(f"📊 Best Performance: {max(returns)*100:.2f}%")
        print(f"📊 Worst Performance: {min(returns)*100:.2f}%")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"complete_workflow_results_{timestamp}.json"
    
    try:
        # Save each result individually since save_results expects BacktestResults, not dict
        for symbol, result in results.items():
            symbol_results_file = f"complete_workflow_{symbol}_results_{timestamp}.pkl"
            save_results(result, symbol_results_file)
            print(f"💾 {symbol} results saved to: {symbol_results_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
    
    return results


def demonstrate_advanced_features():
    """Demonstrate additional advanced features."""
    print_section(
        "BONUS: ADVANCED FEATURES",
        "Showcasing additional capabilities"
    )
    
    print("🔧 Advanced Configuration Options:")
    print("   • Configuration-based filtering from YAML files")
    print("   • Custom filter validation and requirements")
    print("   • Multi-strategy portfolio backtesting")
    print("   • Real-time politician trade tracking")
    print("   • Social media sentiment integration")
    
    print("\n📚 Available Examples:")
    print("   • examples/backtest_example.py - Basic backtesting")
    print("   • examples/advanced_filter_example.py - Advanced filtering")
    print("   • examples/strategy_composer_example.py - Strategy composition")
    print("   • examples/politician_tracking_example.py - Political trades")
    print("   • examples/filter_config_example.py - Filter configuration")
    
    print("\n🚀 Next Steps:")
    print("   1. Experiment with different strategies and parameters")
    print("   2. Add your own custom filters and strategies")
    print("   3. Integrate real-time data feeds")
    print("   4. Implement live trading capabilities")
    print("   5. Add more sophisticated risk management")


def main():
    """Execute the complete trading workflow."""
    print("🎯 COMPLETE TRADING WORKFLOW DEMONSTRATION")
    print("=" * 80)
    print("This example shows the complete end-to-end process:")
    print("Data Fetching → Strategy Creation → Filter Setup → Backtesting → Analysis")
    
    try:
        # Step 1: Fetch data
        combined_data, stock_data = step_1_fetch_data()
        
        # Step 2: Create strategies
        strategies = step_2_create_strategies()
        
        # Step 3: Setup filters
        filtered_strategy = step_3_setup_filters(strategies)
        
        # Step 4: Run backtest
        results = step_4_run_backtest(filtered_strategy, stock_data)
        
        # Step 5: Analyze results
        step_5_analyze_results(results)
        
        # Bonus: Show advanced features
        demonstrate_advanced_features()
        
        print("\n✅ Complete workflow demonstration finished!")
        print("🎉 You've successfully run the entire trading pipeline!")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 