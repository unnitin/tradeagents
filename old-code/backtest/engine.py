"""
Core backtesting engine for evaluating trading strategy performance.

This module provides the main BacktestEngine class that orchestrates
the entire backtesting process including strategy execution, 
portfolio management, and performance analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Any
from dataclasses import dataclass
import warnings

from strategies.base import Strategy
from data import DataFetcher
from .portfolio import Portfolio
from .metrics import PerformanceMetrics, calculate_performance_metrics
from filters import StockFilter, TimeFilter
from .results import BacktestResults
from config import BacktestConfig

# Import composer for strategy combination support
try:
    from composer import StrategyComposer, create_composer
    COMPOSER_AVAILABLE = True
except ImportError:
    COMPOSER_AVAILABLE = False
    StrategyComposer = None


class BacktestEngine:
    """
    Main backtesting engine for evaluating trading strategy performance.
    
    This class orchestrates the entire backtesting process including:
    - Strategy signal generation
    - Portfolio management and position sizing
    - Transaction cost calculation
    - Performance metric calculation
    - Results storage and analysis
    """
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize the backtest engine.
        
        Args:
            config: Configuration object with backtesting parameters
        """
        self.config = config or BacktestConfig()
        self.data_fetcher = DataFetcher()
        self.portfolio = Portfolio(
            initial_capital=self.config.initial_capital,
            commission_rate=self.config.commission_rate,
            slippage_rate=self.config.slippage_rate
        )
        
        # Cache for storing data and results
        self._data_cache = {}
        self._results_cache = {}
    
    def run_backtest(self, 
                    strategy: Strategy,
                    symbols: Union[str, List[str]],
                    start_date: str,
                    end_date: str,
                    stock_filter: Optional[StockFilter] = None,
                    time_filter: Optional[TimeFilter] = None,
                    data_interval: str = "1d") -> BacktestResults:
        """
        Run a complete backtest for the given strategy and parameters.
        
        Args:
            strategy: Trading strategy to backtest
            symbols: Stock symbol(s) to test on
            start_date: Start date for backtest (YYYY-MM-DD format)
            end_date: End date for backtest (YYYY-MM-DD format)
            stock_filter: Optional filter for stock selection
            time_filter: Optional filter for time periods
            data_interval: Data frequency ("1d", "1h", etc.)
            
        Returns:
            BacktestResults object containing all backtest results
        """
        # Ensure symbols is a list
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # Validate date range
        self._validate_date_range(start_date, end_date)
        
        # Get and filter data
        data = self._get_filtered_data(symbols, start_date, end_date, 
                                     stock_filter, time_filter, data_interval)
        
        if data.empty:
            raise ValueError("No data available after filtering")
        
        # Initialize portfolio for this backtest
        self.portfolio.reset(self.config.initial_capital)
        
        # Run the backtest simulation
        portfolio_history = self._run_simulation(strategy, data, symbols)
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(portfolio_history, data, start_date, end_date)
        
        # Create results object
        results = BacktestResults(
            strategy_name=strategy.__class__.__name__,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            config=self.config,
            portfolio_history=portfolio_history,
            metrics=metrics,
            trades=self.portfolio.get_trade_history(),
            data_info=self._get_data_info(data, stock_filter, time_filter)
        )
        
        return results
    
    def run_multiple_strategies(self,
                               strategies: List[Strategy],
                               symbols: Union[str, List[str]],
                               start_date: str,
                               end_date: str,
                               **kwargs) -> Dict[str, BacktestResults]:
        """
        Run backtests for multiple strategies with the same parameters.
        
        Args:
            strategies: List of trading strategies to test
            symbols: Stock symbol(s) to test on
            start_date: Start date for backtest
            end_date: End date for backtest
            **kwargs: Additional arguments passed to run_backtest
            
        Returns:
            Dictionary mapping strategy names to BacktestResults
        """
        results = {}
        
        for strategy in strategies:
            try:
                result = self.run_backtest(strategy, symbols, start_date, end_date, **kwargs)
                results[strategy.__class__.__name__] = result
            except Exception as e:
                warnings.warn(f"Strategy {strategy.__class__.__name__} failed: {e}")
                continue
        
        return results
    
    def run_composer_backtest(self,
                             combination_name: str,
                             symbols: Union[str, List[str]],
                             start_date: str,
                             end_date: str,
                             composer: Optional['StrategyComposer'] = None,
                             config_path: str = "config/strategies.yaml",
                             **kwargs) -> BacktestResults:
        """
        Run a backtest using a strategy combination from the composer.
        
        Args:
            combination_name: Name of the strategy combination to test
            symbols: Stock symbol(s) to test on
            start_date: Start date for backtest (YYYY-MM-DD format)
            end_date: End date for backtest (YYYY-MM-DD format)
            composer: Optional pre-initialized composer instance
            config_path: Path to composer configuration file
            **kwargs: Additional arguments passed to run_backtest
            
        Returns:
            BacktestResults object containing all backtest results
        """
        if not COMPOSER_AVAILABLE:
            raise ImportError("Composer module not available. Please ensure it's properly installed.")
        
        # Initialize composer if not provided
        if composer is None:
            composer = create_composer(config_path)
        
        # Ensure symbols is a list
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # Validate date range
        self._validate_date_range(start_date, end_date)
        
        # Get and filter data
        stock_filter = kwargs.get('stock_filter')
        time_filter = kwargs.get('time_filter')
        data_interval = kwargs.get('data_interval', '1d')
        
        data = self._get_filtered_data(symbols, start_date, end_date, 
                                     stock_filter, time_filter, data_interval)
        
        if data.empty:
            raise ValueError("No data available after filtering")
        
        # Initialize portfolio for this backtest
        self.portfolio.reset(self.config.initial_capital)
        
        # Run the backtest simulation using composer signals
        portfolio_history = self._run_composer_simulation(composer, combination_name, data, symbols)
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(portfolio_history, data, start_date, end_date)
        
        # Get combination info for strategy name
        try:
            combo_info = composer.get_combination_info(combination_name)
            strategy_name = f"Composer_{combination_name}({combo_info.get('method', 'unknown')})"
        except Exception:
            strategy_name = f"Composer_{combination_name}"
        
        # Create results object
        results = BacktestResults(
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            config=self.config,
            portfolio_history=portfolio_history,
            metrics=metrics,
            trades=self.portfolio.get_trade_history(),
            data_info=self._get_composer_data_info(data, stock_filter, time_filter, 
                                                 combination_name, combo_info)
        )
        
        return results
    
    def run_multiple_composer_backtests(self,
                                       combination_names: List[str],
                                       symbols: Union[str, List[str]],
                                       start_date: str,
                                       end_date: str,
                                       composer: Optional['StrategyComposer'] = None,
                                       config_path: str = "config/strategies.yaml",
                                       **kwargs) -> Dict[str, BacktestResults]:
        """
        Run backtests for multiple composer combinations with the same parameters.
        
        Args:
            combination_names: List of combination names to test
            symbols: Stock symbol(s) to test on
            start_date: Start date for backtest
            end_date: End date for backtest
            composer: Optional pre-initialized composer instance
            config_path: Path to composer configuration file
            **kwargs: Additional arguments passed to run_composer_backtest
            
        Returns:
            Dictionary mapping combination names to BacktestResults
        """
        if not COMPOSER_AVAILABLE:
            raise ImportError("Composer module not available. Please ensure it's properly installed.")
        
        # Initialize composer if not provided (reuse for efficiency)
        if composer is None:
            composer = create_composer(config_path)
        
        results = {}
        
        for combination_name in combination_names:
            try:
                result = self.run_composer_backtest(
                    combination_name, symbols, start_date, end_date, 
                    composer=composer, **kwargs
                )
                results[combination_name] = result
            except Exception as e:
                warnings.warn(f"Combination {combination_name} failed: {e}")
                continue
        
        return results
    
    def _validate_date_range(self, start_date: str, end_date: str) -> None:
        """Validate that the date range is valid."""
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        if start >= end:
            raise ValueError("Start date must be before end date")
        
        if end > datetime.now():
            warnings.warn("End date is in the future, using current date")
    
    def _get_filtered_data(self, 
                          symbols: List[str],
                          start_date: str,
                          end_date: str,
                          stock_filter: Optional[StockFilter],
                          time_filter: Optional[TimeFilter],
                          data_interval: str) -> pd.DataFrame:
        """Get and filter data for backtesting."""
        # Create cache key
        cache_key = f"{'-'.join(symbols)}_{start_date}_{end_date}_{data_interval}"
        
        if cache_key in self._data_cache:
            data = self._data_cache[cache_key].copy()
        else:
            # Fetch data for all symbols
            data_dict = {}
            for symbol in symbols:
                try:
                    symbol_data = self.data_fetcher.get_stock_data(
                        symbol, data_interval, start_date, end_date
                    )
                    if not symbol_data.empty:
                        symbol_data['symbol'] = symbol
                        data_dict[symbol] = symbol_data
                except Exception as e:
                    warnings.warn(f"Failed to fetch data for {symbol}: {e}")
            
            if not data_dict:
                return pd.DataFrame()
            
            # Combine all symbol data
            data = pd.concat(data_dict.values(), ignore_index=True)
            
            # Add technical indicators required by strategies
            data = self._add_technical_indicators(data)
            
            # Cache the data
            self._data_cache[cache_key] = data.copy()
        
        # Apply filters
        if stock_filter:
            data = stock_filter.apply_filter(data)
        
        if time_filter:
            data = time_filter.apply_filter(data)
        
        return data
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators required by strategies."""
        from data import add_sma, add_ema, add_rsi, add_bollinger_bands, add_macd, add_atr
        
        # Group by symbol and add indicators
        result_dfs = []
        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol].copy()
            
            # Add all common technical indicators
            try:
                symbol_data = add_sma(symbol_data, 20)
                symbol_data = add_sma(symbol_data, 50)
                symbol_data = add_ema(symbol_data, 20)
                symbol_data = add_rsi(symbol_data, 14)
                symbol_data = add_bollinger_bands(symbol_data, 20)
                symbol_data = add_macd(symbol_data)
                symbol_data = add_atr(symbol_data, 14)
            except Exception as e:
                warnings.warn(f"Failed to add technical indicators for {symbol}: {e}")
            
            result_dfs.append(symbol_data)
        
        return pd.concat(result_dfs, ignore_index=True)
    
    def _run_simulation(self, 
                       strategy: Strategy,
                       data: pd.DataFrame,
                       symbols: List[str]) -> pd.DataFrame:
        """Run the main backtesting simulation."""
        portfolio_history = []
        
        # Group data by date for time-based processing
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data = data.sort_values(['date', 'symbol'])
            dates = data['date'].unique()
        else:
            # Assume index is datetime
            dates = data.index.unique()
        
        for date in dates:
            if 'date' in data.columns:
                day_data = data[data['date'] == date]
            else:
                day_data = data.loc[data.index == date]
            
            # Generate signals for each symbol
            for symbol in symbols:
                symbol_data = day_data[day_data['symbol'] == symbol]
                
                if symbol_data.empty:
                    continue
                
                # Get historical data up to current date for signal generation
                historical_data = self._get_historical_data(data, symbol, date)
                
                if len(historical_data) < 50:  # Need enough data for indicators
                    continue
                
                # Generate trading signal
                try:
                    signals = strategy.generate_signals(historical_data)
                    current_signal = signals.iloc[-1] if not signals.empty else 0
                except Exception as e:
                    warnings.warn(f"Signal generation failed for {symbol} on {date}: {e}")
                    current_signal = 0
                
                # Execute trades based on signal
                if current_signal != 0:
                    self._execute_trade(symbol, current_signal, symbol_data.iloc[-1], date)
            
            # Update portfolio and record state
            portfolio_value = self.portfolio.update_portfolio_value(day_data)
            portfolio_state = self.portfolio.get_portfolio_state()
            portfolio_state['date'] = date
            portfolio_state['total_value'] = portfolio_value
            portfolio_history.append(portfolio_state)
        
        return pd.DataFrame(portfolio_history)
    
    def _get_historical_data(self, data: pd.DataFrame, symbol: str, current_date) -> pd.DataFrame:
        """Get historical data up to current date for a symbol."""
        if 'date' in data.columns:
            symbol_data = data[
                (data['symbol'] == symbol) & 
                (data['date'] <= current_date)
            ].copy()
        else:
            symbol_data = data[
                (data['symbol'] == symbol) & 
                (data.index <= current_date)
            ].copy()
        
        return symbol_data.sort_values('date' if 'date' in symbol_data.columns else symbol_data.index)
    
    def _execute_trade(self, symbol: str, signal: int, market_data: pd.Series, date) -> None:
        """Execute a trade based on the signal."""
        current_price = market_data['close']
        
        if signal == 1:  # Buy signal
            # Calculate position size
            position_size = self._calculate_position_size(symbol, current_price)
            if position_size > 0:
                self.portfolio.buy(symbol, position_size, current_price, date)
        
        elif signal == -1:  # Sell signal
            # Sell existing position
            current_position = self.portfolio.get_position(symbol)
            if current_position > 0:
                self.portfolio.sell(symbol, current_position, current_price, date)
    
    def _calculate_position_size(self, symbol: str, price: float) -> int:
        """Calculate position size based on the configured method."""
        available_cash = self.portfolio.get_available_cash()
        max_position_value = self.portfolio.get_total_value() * self.config.max_position_size
        
        if self.config.position_sizing_method == "fixed_percentage":
            target_value = min(available_cash, max_position_value)
            shares = int(target_value / price)
        
        elif self.config.position_sizing_method == "equal_weight":
            # Equal weight across all positions
            target_value = available_cash / 10  # Assume max 10 positions
            shares = int(target_value / price)
        
        else:  # Default to fixed percentage
            target_value = min(available_cash, max_position_value)
            shares = int(target_value / price)
        
        return max(0, shares)
    
    def _run_composer_simulation(self,
                                composer,
                                combination_name: str,
                                data: pd.DataFrame,
                                symbols: List[str]) -> pd.DataFrame:
        """
        Run backtest simulation using composer-generated signals.
        
        Args:
            composer: Initialized composer instance
            combination_name: Name of the combination to execute
            data: Market data DataFrame
            symbols: List of symbols being tested
            
        Returns:
            DataFrame with portfolio history
        """
        portfolio_history = []
        
        # Group data by date for chronological processing
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data = data.sort_values(['date', 'symbol'])
            dates = data['date'].unique()
        else:
            dates = data.index.unique()
        
        for date in dates:
            if 'date' in data.columns:
                day_data = data[data['date'] == date]
            else:
                day_data = data.loc[data.index == date]
            
            # Get historical data up to current date for signal generation
            historical_data = self._get_historical_data_for_composer(data, date)
            
            if historical_data.empty or len(historical_data) < 50:  # Need minimum data for indicators
                continue
            
            try:
                # Generate signals using composer for this date
                signals = composer.execute_combination(combination_name, historical_data)
                
                # Get the latest signal for current date
                if not signals.empty:
                    if isinstance(signals.index, pd.DatetimeIndex) and date in signals.index:
                        latest_signal = signals.loc[date]
                    else:
                        latest_signal = signals.iloc[-1] if len(signals) > 0 else 0
                    
                    # Execute trades for each symbol
                    for symbol in symbols:
                        symbol_data = day_data[day_data['symbol'] == symbol]
                        if not symbol_data.empty:
                            signal = int(latest_signal) if np.isscalar(latest_signal) else int(latest_signal.iloc[0] if hasattr(latest_signal, 'iloc') else latest_signal)
                            self._execute_trade(symbol, signal, symbol_data.iloc[-1], date)
                
            except Exception as e:
                warnings.warn(f"Signal generation failed for {date}: {e}")
                continue
            
            # Update portfolio value with current market data
            try:
                portfolio_value = self.portfolio.update_portfolio_value(day_data)
                portfolio_state = self.portfolio.get_portfolio_state()
                portfolio_state['date'] = date
                portfolio_state['total_value'] = portfolio_value
                portfolio_history.append(portfolio_state)
            except Exception as e:
                warnings.warn(f"Portfolio update failed for {date}: {e}")
                continue
        
        return pd.DataFrame(portfolio_history)
    
    def _get_historical_data_for_composer(self, data: pd.DataFrame, current_date) -> pd.DataFrame:
        """Get historical data up to current date for composer signal generation."""
        if 'date' in data.columns:
            # Filter data up to current date
            historical_data = data[data['date'] <= current_date].copy()
            
            # For composer, we need clean OHLCV data
            # If single symbol, remove symbol column and set date as index
            if len(data['symbol'].unique()) == 1:
                symbol_data = historical_data.drop(['symbol'], axis=1, errors='ignore')
                if 'date' in symbol_data.columns:
                    symbol_data = symbol_data.set_index('date')
                return symbol_data.sort_index()
            else:
                # Multi-symbol case - composer can handle this format
                return historical_data.sort_values('date')
        else:
            # Date is index
            return data.loc[data.index <= current_date].copy().sort_index()
    
    def _get_composer_data_info(self,
                               data: pd.DataFrame,
                               stock_filter: Optional[StockFilter],
                               time_filter: Optional[TimeFilter],
                               combination_name: str,
                               combo_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get data info for composer-based backtest."""
        base_info = self._get_data_info(data, stock_filter, time_filter)
        
        # Add composer-specific information
        composer_info = {
            'combination_name': combination_name,
            'combination_method': combo_info.get('method', 'unknown'),
            'strategies_used': combo_info.get('strategies', []),
            'filters_used': combo_info.get('filters', []),
            'composer_weights': combo_info.get('weights', {}),
            'is_composer_backtest': True
        }
        
        # Merge with base info
        base_info.update(composer_info)
        return base_info
    
    def _calculate_metrics(self, 
                          portfolio_history: pd.DataFrame,
                          data: pd.DataFrame,
                          start_date: str,
                          end_date: str) -> PerformanceMetrics:
        """Calculate performance metrics for the backtest."""
        return calculate_performance_metrics(
            portfolio_history, 
            self.config.benchmark_symbol,
            self.config.risk_free_rate,
            start_date,
            end_date
        )
    
    def _get_data_info(self, 
                      data: pd.DataFrame,
                      stock_filter: Optional[StockFilter],
                      time_filter: Optional[TimeFilter]) -> Dict[str, Any]:
        """Get information about the data used in the backtest."""
        return {
            'total_records': len(data),
            'symbols': data['symbol'].unique().tolist() if 'symbol' in data.columns else [],
            'date_range': {
                'start': data['date'].min() if 'date' in data.columns else data.index.min(),
                'end': data['date'].max() if 'date' in data.columns else data.index.max()
            },
            'stock_filter_applied': stock_filter is not None,
            'time_filter_applied': time_filter is not None,
            'missing_data_periods': self._count_missing_data(data)
        }
    
    def _count_missing_data(self, data: pd.DataFrame) -> int:
        """Count missing data periods."""
        return data.isnull().sum().sum()


def create_backtest_engine(config: Optional[BacktestConfig] = None) -> BacktestEngine:
    """
    Convenience function to create a BacktestEngine instance.
    
    Args:
        config: Optional configuration object
        
    Returns:
        BacktestEngine instance ready for use
    """
    return BacktestEngine(config) 