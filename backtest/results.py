"""
Backtest results management and analysis.

This module provides classes and functions for storing, analyzing,
and reporting backtest results including performance metrics,
trade history, and comparison capabilities.
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import pickle
import os

from .metrics import PerformanceMetrics
from config import BacktestConfig


@dataclass
class BacktestResults:
    """
    Container for comprehensive backtest results.
    
    This class stores all results from a backtest including:
    - Strategy information
    - Performance metrics
    - Portfolio history
    - Trade history
    - Configuration details
    """
    
    strategy_name: str
    symbols: List[str]
    start_date: str
    end_date: str
    config: BacktestConfig
    portfolio_history: pd.DataFrame
    metrics: PerformanceMetrics
    trades: List[Dict[str, Any]]
    data_info: Dict[str, Any]
    
    # Metadata
    created_at: datetime = None
    backtest_id: Optional[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Initialize metadata after creation."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.backtest_id is None:
            self.backtest_id = f"{self.strategy_name}_{self.created_at.strftime('%Y%m%d_%H%M%S')}"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the backtest results."""
        return {
            'backtest_id': self.backtest_id,
            'strategy_name': self.strategy_name,
            'symbols': self.symbols,
            'date_range': f"{self.start_date} to {self.end_date}",
            'total_return': f"{self.metrics.total_return:.2%}",
            'annualized_return': f"{self.metrics.annualized_return:.2%}",
            'sharpe_ratio': f"{self.metrics.sharpe_ratio:.2f}",
            'max_drawdown': f"{self.metrics.max_drawdown:.2%}",
            'total_trades': self.metrics.total_trades,
            'win_rate': f"{self.metrics.win_rate:.2%}",
            'trading_days': self.metrics.trading_days,
            'created_at': self.created_at.isoformat()
        }
    
    def get_performance_summary(self) -> pd.DataFrame:
        """Get performance metrics as a formatted DataFrame."""
        metrics_dict = self.metrics.to_dict()
        
        # Format metrics for display
        formatted_metrics = []
        
        # Return metrics
        formatted_metrics.extend([
            ('Total Return', f"{metrics_dict['total_return']:.2%}"),
            ('Annualized Return', f"{metrics_dict['annualized_return']:.2%}"),
            ('Annualized Volatility', f"{metrics_dict['annualized_volatility']:.2%}"),
        ])
        
        # Risk-adjusted metrics
        formatted_metrics.extend([
            ('Sharpe Ratio', f"{metrics_dict['sharpe_ratio']:.2f}"),
            ('Sortino Ratio', f"{metrics_dict['sortino_ratio']:.2f}"),
            ('Calmar Ratio', f"{metrics_dict['calmar_ratio']:.2f}"),
        ])
        
        # Risk metrics
        formatted_metrics.extend([
            ('Maximum Drawdown', f"{metrics_dict['max_drawdown']:.2%}"),
            ('Max DD Duration (days)', str(metrics_dict['max_drawdown_duration'])),
            ('VaR 95%', f"{metrics_dict['value_at_risk_95']:.2%}"),
            ('Beta', f"{metrics_dict['beta']:.2f}"),
        ])
        
        # Trade metrics
        formatted_metrics.extend([
            ('Total Trades', str(metrics_dict['total_trades'])),
            ('Win Rate', f"{metrics_dict['win_rate']:.2%}"),
            ('Profit Factor', f"{metrics_dict['profit_factor']:.2f}"),
        ])
        
        # Benchmark comparison
        formatted_metrics.extend([
            ('Benchmark Return', f"{metrics_dict['benchmark_return']:.2%}"),
            ('Alpha', f"{metrics_dict['alpha']:.2%}"),
            ('Information Ratio', f"{metrics_dict['information_ratio']:.2f}"),
        ])
        
        return pd.DataFrame(formatted_metrics, columns=['Metric', 'Value'])
    
    def get_trade_analysis(self) -> Dict[str, Any]:
        """Analyze trade history and return statistics."""
        if not self.trades:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'avg_trade_size': 0,
                'largest_trade': 0,
                'smallest_trade': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        buy_trades = trades_df[trades_df['side'] == 'BUY']
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        
        analysis = {
            'total_trades': len(trades_df),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'symbols_traded': trades_df['symbol'].nunique() if 'symbol' in trades_df.columns else 0,
            'avg_trade_size': trades_df['quantity'].mean() if 'quantity' in trades_df.columns else 0,
            'largest_trade': trades_df['quantity'].max() if 'quantity' in trades_df.columns else 0,
            'smallest_trade': trades_df['quantity'].min() if 'quantity' in trades_df.columns else 0,
            'total_volume': trades_df['quantity'].sum() if 'quantity' in trades_df.columns else 0,
            'avg_price': trades_df['price'].mean() if 'price' in trades_df.columns else 0,
            'total_commissions': trades_df['commission'].sum() if 'commission' in trades_df.columns else 0,
            'total_slippage': trades_df['slippage'].sum() if 'slippage' in trades_df.columns else 0
        }
        
        return analysis
    
    def get_monthly_returns(self) -> pd.DataFrame:
        """Calculate monthly returns from portfolio history."""
        if self.portfolio_history.empty or 'total_value' not in self.portfolio_history.columns:
            return pd.DataFrame()
        
        # Set date as index if it's not already
        portfolio_df = self.portfolio_history.copy()
        if 'date' in portfolio_df.columns:
            portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
            portfolio_df.set_index('date', inplace=True)
        
        # Calculate daily returns
        daily_returns = portfolio_df['total_value'].pct_change()
        
        # Aggregate to monthly returns
        monthly_returns = (1 + daily_returns).resample('M').prod() - 1
        
        return monthly_returns.to_frame('Monthly Return')
    
    def get_drawdown_analysis(self) -> pd.DataFrame:
        """Calculate detailed drawdown analysis."""
        if self.portfolio_history.empty or 'total_value' not in self.portfolio_history.columns:
            return pd.DataFrame()
        
        portfolio_values = self.portfolio_history['total_value']
        
        # Calculate running maximum (peak)
        peak = portfolio_values.expanding().max()
        
        # Calculate drawdown
        drawdown = (portfolio_values - peak) / peak
        
        # Create drawdown DataFrame
        drawdown_df = pd.DataFrame({
            'Portfolio Value': portfolio_values,
            'Peak Value': peak,
            'Drawdown': drawdown,
            'Drawdown %': drawdown * 100
        })
        
        if 'date' in self.portfolio_history.columns:
            drawdown_df.index = pd.to_datetime(self.portfolio_history['date'])
        
        return drawdown_df
    
    def compare_to_benchmark(self, benchmark_symbol: str = "SPY") -> Dict[str, Any]:
        """Compare strategy performance to benchmark."""
        try:
            from data import DataFetcher
            
            fetcher = DataFetcher()
            benchmark_data = fetcher.get_stock_data(
                benchmark_symbol, "1d", self.start_date, self.end_date
            )
            
            if benchmark_data.empty:
                return {'error': f'Could not fetch benchmark data for {benchmark_symbol}'}
            
            # Calculate benchmark returns
            benchmark_returns = benchmark_data['close'].pct_change().dropna()
            benchmark_total_return = (benchmark_data['close'].iloc[-1] / benchmark_data['close'].iloc[0]) - 1
            
            # Calculate portfolio returns
            portfolio_returns = self.portfolio_history['total_value'].pct_change().dropna()
            
            # Align returns for comparison
            min_length = min(len(portfolio_returns), len(benchmark_returns))
            portfolio_returns = portfolio_returns.iloc[-min_length:]
            benchmark_returns = benchmark_returns.iloc[-min_length:]
            
            # Calculate comparison metrics
            excess_returns = portfolio_returns - benchmark_returns
            
            comparison = {
                'strategy_return': self.metrics.total_return,
                'benchmark_return': benchmark_total_return,
                'excess_return': self.metrics.total_return - benchmark_total_return,
                'strategy_volatility': self.metrics.annualized_volatility,
                'benchmark_volatility': benchmark_returns.std() * np.sqrt(252),
                'strategy_sharpe': self.metrics.sharpe_ratio,
                'benchmark_sharpe': (benchmark_total_return - 0.02) / (benchmark_returns.std() * np.sqrt(252)),
                'correlation': portfolio_returns.corr(benchmark_returns),
                'beta': self.metrics.beta,
                'alpha': self.metrics.alpha,
                'tracking_error': excess_returns.std() * np.sqrt(252),
                'information_ratio': self.metrics.information_ratio
            }
            
            return comparison
            
        except Exception as e:
            return {'error': f'Benchmark comparison failed: {str(e)}'}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for serialization."""
        return {
            'strategy_name': self.strategy_name,
            'symbols': self.symbols,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'config': asdict(self.config),
            'portfolio_history': self.portfolio_history.to_dict('records'),
            'metrics': self.metrics.to_dict(),
            'trades': self.trades,
            'data_info': self.data_info,
            'created_at': self.created_at.isoformat(),
            'backtest_id': self.backtest_id,
            'notes': self.notes
        }


def save_results(results: BacktestResults, 
                filepath: Optional[str] = None,
                format: str = 'pickle') -> str:
    """
    Save backtest results to file.
    
    Args:
        results: BacktestResults object to save
        filepath: Optional file path (auto-generated if None)
        format: File format ('pickle', 'json', or 'excel')
        
    Returns:
        Path to saved file
    """
    if filepath is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backtest_{results.strategy_name}_{timestamp}"
        
        if format == 'pickle':
            filepath = f"{filename}.pkl"
        elif format == 'json':
            filepath = f"{filename}.json"
        elif format == 'excel':
            filepath = f"{filename}.xlsx"
        else:
            raise ValueError("Format must be 'pickle', 'json', or 'excel'")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    if format == 'pickle':
        with open(filepath, 'wb') as f:
            pickle.dump(results, f)
    
    elif format == 'json':
        results_dict = results.to_dict()
        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)
    
    elif format == 'excel':
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([results.get_summary()]).T
            summary_df.columns = ['Value']
            summary_df.to_excel(writer, sheet_name='Summary')
            
            # Performance metrics
            performance_df = results.get_performance_summary()
            performance_df.to_excel(writer, sheet_name='Performance', index=False)
            
            # Portfolio history
            results.portfolio_history.to_excel(writer, sheet_name='Portfolio History', index=False)
            
            # Trade history
            if results.trades:
                trades_df = pd.DataFrame(results.trades)
                trades_df.to_excel(writer, sheet_name='Trades', index=False)
            
            # Monthly returns
            monthly_returns = results.get_monthly_returns()
            if not monthly_returns.empty:
                monthly_returns.to_excel(writer, sheet_name='Monthly Returns')
            
            # Drawdown analysis
            drawdown_df = results.get_drawdown_analysis()
            if not drawdown_df.empty:
                drawdown_df.to_excel(writer, sheet_name='Drawdown Analysis')
    
    return filepath


def load_results(filepath: str) -> BacktestResults:
    """
    Load backtest results from file.
    
    Args:
        filepath: Path to results file
        
    Returns:
        BacktestResults object
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Results file not found: {filepath}")
    
    if filepath.endswith('.pkl'):
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    
    elif filepath.endswith('.json'):
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct objects from dictionary
        # This would need more complex reconstruction logic
        # For now, just return the raw data
        return data
    
    else:
        raise ValueError("Unsupported file format. Use .pkl or .json files.")


def compare_multiple_results(results_list: List[BacktestResults]) -> pd.DataFrame:
    """
    Compare multiple backtest results.
    
    Args:
        results_list: List of BacktestResults objects
        
    Returns:
        DataFrame comparing key metrics across all results
    """
    comparison_data = []
    
    for result in results_list:
        metrics = result.metrics
        summary = {
            'Strategy': result.strategy_name,
            'Symbols': ', '.join(result.symbols),
            'Date Range': f"{result.start_date} to {result.end_date}",
            'Total Return': f"{metrics.total_return:.2%}",
            'Annualized Return': f"{metrics.annualized_return:.2%}",
            'Volatility': f"{metrics.annualized_volatility:.2%}",
            'Sharpe Ratio': f"{metrics.sharpe_ratio:.2f}",
            'Sortino Ratio': f"{metrics.sortino_ratio:.2f}",
            'Calmar Ratio': f"{metrics.calmar_ratio:.2f}",
            'Max Drawdown': f"{metrics.max_drawdown:.2%}",
            'Max DD Duration': metrics.max_drawdown_duration,
            'Total Trades': metrics.total_trades,
            'Win Rate': f"{metrics.win_rate:.2%}",
            'Alpha': f"{metrics.alpha:.2%}",
            'Beta': f"{metrics.beta:.2f}",
            'Information Ratio': f"{metrics.information_ratio:.2f}",
            'Trading Days': metrics.trading_days
        }
        comparison_data.append(summary)
    
    return pd.DataFrame(comparison_data)


def create_performance_report(results: BacktestResults) -> str:
    """
    Create a comprehensive text report of backtest results.
    
    Args:
        results: BacktestResults object
        
    Returns:
        Formatted text report
    """
    report = []
    
    # Header
    report.append("=" * 60)
    report.append("BACKTEST PERFORMANCE REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Basic info
    report.append(f"Strategy: {results.strategy_name}")
    report.append(f"Symbols: {', '.join(results.symbols)}")
    report.append(f"Period: {results.start_date} to {results.end_date}")
    report.append(f"Trading Days: {results.metrics.trading_days}")
    report.append(f"Backtest ID: {results.backtest_id}")
    report.append(f"Created: {results.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Performance summary
    report.append("PERFORMANCE SUMMARY")
    report.append("-" * 20)
    report.append(f"Total Return: {results.metrics.total_return:.2%}")
    report.append(f"Annualized Return: {results.metrics.annualized_return:.2%}")
    report.append(f"Annualized Volatility: {results.metrics.annualized_volatility:.2%}")
    report.append(f"Sharpe Ratio: {results.metrics.sharpe_ratio:.2f}")
    report.append(f"Sortino Ratio: {results.metrics.sortino_ratio:.2f}")
    report.append(f"Calmar Ratio: {results.metrics.calmar_ratio:.2f}")
    report.append("")
    
    # Risk metrics
    report.append("RISK METRICS")
    report.append("-" * 12)
    report.append(f"Maximum Drawdown: {results.metrics.max_drawdown:.2%}")
    report.append(f"Max DD Duration: {results.metrics.max_drawdown_duration} days")
    report.append(f"Value at Risk (95%): {results.metrics.value_at_risk_95:.2%}")
    report.append(f"Conditional VaR (95%): {results.metrics.conditional_var_95:.2%}")
    report.append(f"Beta: {results.metrics.beta:.2f}")
    report.append("")
    
    # Trading metrics
    report.append("TRADING METRICS")
    report.append("-" * 15)
    report.append(f"Total Trades: {results.metrics.total_trades}")
    report.append(f"Win Rate: {results.metrics.win_rate:.2%}")
    report.append(f"Profit Factor: {results.metrics.profit_factor:.2f}")
    report.append(f"Average Win: {results.metrics.avg_win:.2%}")
    report.append(f"Average Loss: {results.metrics.avg_loss:.2%}")
    report.append("")
    
    # Benchmark comparison
    report.append("BENCHMARK COMPARISON")
    report.append("-" * 19)
    report.append(f"Benchmark Return: {results.metrics.benchmark_return:.2%}")
    report.append(f"Alpha: {results.metrics.alpha:.2%}")
    report.append(f"Tracking Error: {results.metrics.tracking_error:.2%}")
    report.append(f"Information Ratio: {results.metrics.information_ratio:.2f}")
    report.append("")
    
    # Configuration
    report.append("CONFIGURATION")
    report.append("-" * 13)
    report.append(f"Initial Capital: ${results.config.initial_capital:,.0f}")
    report.append(f"Commission Rate: {results.config.commission_rate:.3%}")
    report.append(f"Slippage Rate: {results.config.slippage_rate:.3%}")
    report.append(f"Max Position Size: {results.config.max_position_size:.1%}")
    report.append(f"Position Sizing: {results.config.position_sizing_method}")
    report.append("")
    
    # Trade analysis
    trade_analysis = results.get_trade_analysis()
    if trade_analysis['total_trades'] > 0:
        report.append("TRADE ANALYSIS")
        report.append("-" * 14)
        report.append(f"Total Trades: {trade_analysis['total_trades']}")
        report.append(f"Buy Trades: {trade_analysis['buy_trades']}")
        report.append(f"Sell Trades: {trade_analysis['sell_trades']}")
        report.append(f"Symbols Traded: {trade_analysis['symbols_traded']}")
        report.append(f"Average Trade Size: {trade_analysis['avg_trade_size']:.0f} shares")
        report.append(f"Total Volume: {trade_analysis['total_volume']:,.0f} shares")
        report.append(f"Total Commissions: ${trade_analysis['total_commissions']:,.2f}")
        report.append(f"Total Slippage: ${trade_analysis['total_slippage']:,.2f}")
        report.append("")
    
    # Notes
    if results.notes:
        report.append("NOTES")
        report.append("-" * 5)
        report.append(results.notes)
        report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report) 