"""
Performance metrics calculation for backtesting.

This module provides comprehensive performance metrics calculation
including returns, risk metrics, and comparison to benchmarks.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from data import DataFetcher


@dataclass
class PerformanceMetrics:
    """Container for all performance metrics."""
    
    # Return metrics
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    value_at_risk_95: float
    conditional_var_95: float
    beta: float
    
    # Trade metrics
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    
    # Benchmark comparison
    benchmark_return: float
    alpha: float
    tracking_error: float
    information_ratio: float
    
    # Additional metrics
    start_date: str
    end_date: str
    trading_days: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for easy serialization."""
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'annualized_volatility': self.annualized_volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_duration': self.max_drawdown_duration,
            'value_at_risk_95': self.value_at_risk_95,
            'conditional_var_95': self.conditional_var_95,
            'beta': self.beta,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'benchmark_return': self.benchmark_return,
            'alpha': self.alpha,
            'tracking_error': self.tracking_error,
            'information_ratio': self.information_ratio,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'trading_days': self.trading_days
        }


def calculate_performance_metrics(portfolio_history: pd.DataFrame,
                                benchmark_symbol: str = "SPY",
                                risk_free_rate: float = 0.02,
                                start_date: str = "",
                                end_date: str = "") -> PerformanceMetrics:
    """
    Calculate comprehensive performance metrics for a backtest.
    
    Args:
        portfolio_history: DataFrame with portfolio values over time
        benchmark_symbol: Symbol to use as benchmark
        risk_free_rate: Risk-free rate for Sharpe ratio calculation
        start_date: Start date of backtest
        end_date: End date of backtest
        
    Returns:
        PerformanceMetrics object with all calculated metrics
    """
    if portfolio_history.empty or 'total_value' not in portfolio_history.columns:
        raise ValueError("Portfolio history must contain 'total_value' column")
    
    # Calculate returns
    portfolio_values = portfolio_history['total_value']
    returns = portfolio_values.pct_change().dropna()
    
    # Get benchmark data
    benchmark_returns = _get_benchmark_returns(benchmark_symbol, start_date, end_date)
    
    # Calculate return metrics
    total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
    
    # Annualized metrics
    trading_days = len(returns)
    years = trading_days / 252.0  # Assuming 252 trading days per year
    
    annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    annualized_volatility = returns.std() * np.sqrt(252)
    
    # Risk-adjusted metrics
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility > 0 else 0
    
    # Sortino ratio (downside deviation)
    downside_returns = returns[returns < 0]
    downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
    sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
    
    # Drawdown analysis
    max_drawdown, max_dd_duration = _calculate_drawdown_metrics(portfolio_values)
    
    # Calmar ratio
    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # Value at Risk (VaR) and Conditional VaR
    var_95 = float(np.percentile(returns, 5)) if len(returns) > 0 else 0.0
    cvar_95 = float(returns[returns <= var_95].mean()) if len(returns[returns <= var_95]) > 0 else 0.0
    
    # Beta calculation (if benchmark available)
    beta = _calculate_beta(returns, benchmark_returns)
    
    # Trade analysis (if trades available)
    trade_metrics = _calculate_trade_metrics(portfolio_history)
    
    # Benchmark comparison
    benchmark_total_return = _calculate_benchmark_return(benchmark_returns)
    alpha = annualized_return - (risk_free_rate + beta * (benchmark_total_return - risk_free_rate))
    
    # Tracking error and information ratio
    if len(benchmark_returns) > 0 and len(returns) == len(benchmark_returns):
        excess_returns = returns - benchmark_returns
        tracking_error = excess_returns.std() * np.sqrt(252)
        information_ratio = excess_returns.mean() * np.sqrt(252) / tracking_error if tracking_error > 0 else 0
    else:
        tracking_error = 0
        information_ratio = 0
    
    return PerformanceMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
        max_drawdown=max_drawdown,
        max_drawdown_duration=max_dd_duration,
        value_at_risk_95=var_95,
        conditional_var_95=cvar_95,
        beta=beta,
        total_trades=int(trade_metrics['total_trades']),
        win_rate=trade_metrics['win_rate'],
        profit_factor=trade_metrics['profit_factor'],
        avg_win=trade_metrics['avg_win'],
        avg_loss=trade_metrics['avg_loss'],
        benchmark_return=benchmark_total_return,
        alpha=alpha,
        tracking_error=tracking_error,
        information_ratio=information_ratio,
        start_date=start_date,
        end_date=end_date,
        trading_days=trading_days
    )


def _get_benchmark_returns(symbol: str, start_date: str, end_date: str) -> pd.Series:
    """Get benchmark returns for comparison."""
    try:
        fetcher = DataFetcher()
        benchmark_data = fetcher.get_stock_data(symbol, "1d", start_date, end_date)
        if not benchmark_data.empty and 'close' in benchmark_data.columns:
            return benchmark_data['close'].pct_change().dropna()
    except Exception:
        pass  # Benchmark data not available
    
    return pd.Series(dtype=float)


def _calculate_drawdown_metrics(portfolio_values: pd.Series) -> tuple[float, int]:
    """Calculate maximum drawdown and duration."""
    # Calculate running maximum (peak)
    peak = portfolio_values.expanding().max()
    
    # Calculate drawdown
    drawdown = (portfolio_values - peak) / peak
    
    # Maximum drawdown
    max_drawdown = drawdown.min()
    
    # Maximum drawdown duration
    # Find periods where we're in drawdown
    in_drawdown = drawdown < 0
    
    # Find the longest consecutive period of drawdown
    max_duration = 0
    current_duration = 0
    
    for is_dd in in_drawdown:
        if is_dd:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0
    
    return max_drawdown, max_duration


def _calculate_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate portfolio beta relative to benchmark."""
    if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
        return 0.0
    
    # Align returns
    min_length = min(len(portfolio_returns), len(benchmark_returns))
    portfolio_returns = portfolio_returns.iloc[-min_length:]
    benchmark_returns = benchmark_returns.iloc[-min_length:]
    
    if len(portfolio_returns) < 2 or benchmark_returns.var() == 0:
        return 0.0
    
    covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
    benchmark_variance = benchmark_returns.var()
    
    return covariance / benchmark_variance


def _calculate_trade_metrics(portfolio_history: pd.DataFrame) -> Dict[str, float]:
    """Calculate trade-related metrics."""
    # Default values if no trade data available
    default_metrics = {
        'total_trades': 0,
        'win_rate': 0.0,
        'profit_factor': 0.0,
        'avg_win': 0.0,
        'avg_loss': 0.0
    }
    
    # Check if we have trade information in portfolio history
    # This would need to be enhanced based on actual trade tracking
    if 'num_positions' in portfolio_history.columns:
        # Simple approximation based on position changes
        position_changes = portfolio_history['num_positions'].diff().abs().sum()
        default_metrics['total_trades'] = int(position_changes)
    
    return default_metrics


def _calculate_benchmark_return(benchmark_returns: pd.Series) -> float:
    """Calculate total benchmark return."""
    if len(benchmark_returns) == 0:
        return 0.0
    
    return (1 + benchmark_returns).prod() - 1


def calculate_rolling_metrics(portfolio_history: pd.DataFrame, 
                            window: int = 252) -> pd.DataFrame:
    """
    Calculate rolling performance metrics.
    
    Args:
        portfolio_history: Portfolio value history
        window: Rolling window size (default 252 trading days = 1 year)
        
    Returns:
        DataFrame with rolling metrics
    """
    if 'total_value' not in portfolio_history.columns:
        raise ValueError("Portfolio history must contain 'total_value' column")
    
    values = portfolio_history['total_value']
    returns = values.pct_change()
    
    rolling_metrics = pd.DataFrame(index=portfolio_history.index)
    
    # Rolling return
    rolling_metrics['rolling_return'] = returns.rolling(window).apply(
        lambda x: (1 + x).prod() - 1
    )
    
    # Rolling volatility
    rolling_metrics['rolling_volatility'] = returns.rolling(window).std() * np.sqrt(252)
    
    # Rolling Sharpe ratio (assuming 2% risk-free rate)
    rolling_metrics['rolling_sharpe'] = (
        rolling_metrics['rolling_return'] * 252 / window - 0.02
    ) / rolling_metrics['rolling_volatility']
    
    # Rolling maximum drawdown
    rolling_max = values.rolling(window).max()
    rolling_metrics['rolling_drawdown'] = (values - rolling_max) / rolling_max
    rolling_metrics['rolling_max_drawdown'] = rolling_metrics['rolling_drawdown'].rolling(window).min()
    
    return rolling_metrics


def compare_strategies(results_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Compare multiple strategy results.
    
    Args:
        results_dict: Dictionary mapping strategy names to BacktestResults
        
    Returns:
        DataFrame comparing key metrics across strategies
    """
    comparison_data = []
    
    for strategy_name, result in results_dict.items():
        if hasattr(result, 'metrics'):
            metrics = result.metrics
            comparison_data.append({
                'Strategy': strategy_name,
                'Total Return': f"{metrics.total_return:.2%}",
                'Annualized Return': f"{metrics.annualized_return:.2%}",
                'Volatility': f"{metrics.annualized_volatility:.2%}",
                'Sharpe Ratio': f"{metrics.sharpe_ratio:.2f}",
                'Max Drawdown': f"{metrics.max_drawdown:.2%}",
                'Calmar Ratio': f"{metrics.calmar_ratio:.2f}",
                'Win Rate': f"{metrics.win_rate:.2%}",
                'Total Trades': metrics.total_trades
            })
    
    return pd.DataFrame(comparison_data) 