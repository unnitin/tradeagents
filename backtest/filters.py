"""
Filtering functionality for backtesting.

This module provides filters for stock selection and time period filtering
based on configurable attributes like liquidity, trading volume, and market conditions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime, time
from config.filter_config import FilterConfig


class BaseFilter(ABC):
    """Base class for all filters."""
    
    @abstractmethod
    def apply_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply the filter to the data and return filtered DataFrame."""
        pass
    
    @abstractmethod
    def get_filter_info(self) -> Dict[str, Any]:
        """Return information about the filter configuration."""
        pass


class StockFilter(BaseFilter):
    """
    Filter stocks based on various criteria.
    
    This filter can exclude stocks based on:
    - Trading volume thresholds
    - Price ranges
    - Market capitalization
    - Volatility measures
    - Explicit include/exclude lists
    """
    
    def __init__(self, 
                 min_volume: float = 1000000.0,
                 min_price: float = 5.0,
                 max_price: Optional[float] = None,
                 min_market_cap: Optional[float] = None,
                 max_volatility: Optional[float] = None,
                 exclude_symbols: Optional[List[str]] = None,
                 include_symbols: Optional[List[str]] = None):
        """
        Initialize stock filter.
        
        Args:
            min_volume: Minimum daily trading volume
            min_price: Minimum stock price
            max_price: Maximum stock price (None for no limit)
            min_market_cap: Minimum market cap (None for no limit)
            max_volatility: Maximum volatility threshold (None for no limit)
            exclude_symbols: List of symbols to exclude
            include_symbols: List of symbols to include (None for all)
        """
        self.config = FilterConfig(
            min_volume=min_volume,
            min_price=min_price,
            max_price=max_price,
            min_market_cap=min_market_cap,
            max_volatility=max_volatility,
            exclude_symbols=exclude_symbols or [],
            include_symbols=include_symbols or []
        )
    
    def apply_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Apply stock filters to the data.
        
        Args:
            data: DataFrame with stock data
            
        Returns:
            Filtered DataFrame
        """
        if data.empty:
            return data
        
        filtered_data: pd.DataFrame = data.copy()
        
        # Apply volume filter
        if 'volume' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['volume'] >= self.config.min_volume]
        
        # Apply price filters
        if 'close' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['close'] >= self.config.min_price]
            
            if self.config.max_price is not None:
                filtered_data = filtered_data[filtered_data['close'] <= self.config.max_price]
        
        # Apply volatility filter (if ATR or similar is available)
        if self.config.max_volatility is not None:
            if 'atr_14' in filtered_data.columns:
                # Use ATR as volatility proxy
                atr_threshold = self.config.max_volatility
                filtered_data = filtered_data[filtered_data['atr_14'] <= atr_threshold]
            elif 'volatility' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['volatility'] <= self.config.max_volatility]
        
        # Apply symbol-based filters
        if 'symbol' in filtered_data.columns:
            # Exclude specific symbols
            if self.config.exclude_symbols:
                filtered_data = filtered_data[~filtered_data['symbol'].isin(self.config.exclude_symbols)]
            
            # Include only specific symbols
            if self.config.include_symbols:
                filtered_data = filtered_data[filtered_data['symbol'].isin(self.config.include_symbols)]
        else:
            # Handle case where symbols are in the index
            if self.config.exclude_symbols:
                filtered_data = filtered_data[~filtered_data.index.isin(self.config.exclude_symbols)]
            
            # Include only specific symbols
            if self.config.include_symbols:
                filtered_data = filtered_data[filtered_data.index.isin(self.config.include_symbols)]
        
        return filtered_data
    
    def get_filter_info(self) -> Dict[str, Any]:
        """Get information about the filter configuration."""
        return {
            'filter_type': 'StockFilter',
            'min_volume': self.config.min_volume,
            'min_price': self.config.min_price,
            'max_price': self.config.max_price,
            'min_market_cap': self.config.min_market_cap,
            'max_volatility': self.config.max_volatility,
            'exclude_symbols': self.config.exclude_symbols,
            'include_symbols': self.config.include_symbols,
            'num_exclude': len(self.config.exclude_symbols),
            'num_include': len(self.config.include_symbols) if self.config.include_symbols else 'all'
        }


class TimeFilter(BaseFilter):
    """
    Filter data based on time periods.
    
    This filter can exclude data based on:
    - Specific dates or date ranges
    - Time of day (for intraday data)
    - Market conditions (e.g., exclude during high volatility periods)
    - Earnings announcement periods
    """
    
    def __init__(self,
                 exclude_dates: Optional[List[str]] = None,
                 include_dates: Optional[List[str]] = None,
                 start_time: Optional[str] = None,
                 end_time: Optional[str] = None,
                 exclude_earnings_periods: bool = False,
                 exclude_market_holidays: bool = True,
                 min_trading_days: int = 30):
        """
        Initialize time filter.
        
        Args:
            exclude_dates: List of dates to exclude (YYYY-MM-DD format)
            include_dates: List of dates to include (None for all)
            start_time: Start time for intraday filtering (HH:MM format)
            end_time: End time for intraday filtering (HH:MM format)
            exclude_earnings_periods: Whether to exclude earnings periods
            exclude_market_holidays: Whether to exclude market holidays
            min_trading_days: Minimum number of trading days required
        """
        self.exclude_dates = [pd.to_datetime(d) for d in (exclude_dates or [])]
        self.include_dates = [pd.to_datetime(d) for d in (include_dates or [])] if include_dates else None
        self.start_time = pd.to_datetime(start_time, format='%H:%M').time() if start_time else None
        self.end_time = pd.to_datetime(end_time, format='%H:%M').time() if end_time else None
        self.exclude_earnings_periods = exclude_earnings_periods
        self.exclude_market_holidays = exclude_market_holidays
        self.min_trading_days = min_trading_days
        
        # Common market holidays (simplified list)
        self.market_holidays = [
            '2024-01-01',  # New Year's Day
            '2024-01-15',  # Martin Luther King Jr. Day
            '2024-02-19',  # Presidents Day
            '2024-03-29',  # Good Friday
            '2024-05-27',  # Memorial Day
            '2024-06-19',  # Juneteenth
            '2024-07-04',  # Independence Day
            '2024-09-02',  # Labor Day
            '2024-11-28',  # Thanksgiving
            '2024-12-25',  # Christmas
        ]
        self.market_holidays = [pd.to_datetime(d) for d in self.market_holidays]
    
    def apply_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Apply time filters to the data.
        
        Args:
            data: DataFrame with time-indexed or date column data
            
        Returns:
            Filtered DataFrame
        """
        if data.empty:
            return data
        
        filtered_data = data.copy()
        
        # Get date column or index
        if 'date' in filtered_data.columns:
            date_col = pd.to_datetime(filtered_data['date'])
        elif isinstance(filtered_data.index, pd.DatetimeIndex):
            date_col = filtered_data.index
        else:
            # No time information available
            return filtered_data
        
        # Apply exclusion filters
        if self.exclude_dates:
            if isinstance(date_col, pd.DatetimeIndex):
                mask = ~date_col.normalize().isin([d.normalize() for d in self.exclude_dates])
            else:
                mask = ~date_col.dt.normalize().isin([d.normalize() for d in self.exclude_dates])
            filtered_data = filtered_data[mask]
            if 'date' in filtered_data.columns:
                date_col = pd.to_datetime(filtered_data['date'])
            else:
                date_col = filtered_data.index
        
        if self.include_dates is not None:
            if isinstance(date_col, pd.DatetimeIndex):
                mask = date_col.normalize().isin([d.normalize() for d in self.include_dates])
            else:
                mask = date_col.dt.normalize().isin([d.normalize() for d in self.include_dates])
            filtered_data = filtered_data[mask]
            if 'date' in filtered_data.columns:
                date_col = pd.to_datetime(filtered_data['date'])
            else:
                date_col = filtered_data.index
        
        # Exclude market holidays
        if self.exclude_market_holidays:
            # Check for market holidays
            if self.market_holidays:
                # Convert to datetime if needed
                if not pd.api.types.is_datetime64_any_dtype(date_col):
                    date_col = pd.to_datetime(date_col)
                
                # Filter out market holidays
                if isinstance(date_col, pd.DatetimeIndex):
                    mask = ~date_col.normalize().isin([h.normalize() for h in self.market_holidays])
                else:
                    mask = ~date_col.dt.normalize().isin([h.normalize() for h in self.market_holidays])
                filtered_data = filtered_data[mask]
        
        # Apply time-of-day filters (for intraday data)
        if self.start_time is not None or self.end_time is not None:
            time_col = date_col.time
            
            if self.start_time is not None:
                mask_start = time_col >= self.start_time
                filtered_data = filtered_data[mask_start]
                if 'date' in filtered_data.columns:
                    date_col = pd.to_datetime(filtered_data['date'])
                    time_col = date_col.time
                else:
                    date_col = filtered_data.index
                    time_col = date_col.time
            
            if self.end_time is not None:
                mask_end = time_col <= self.end_time
                filtered_data = filtered_data[mask_end]
        
        # Check minimum trading days requirement
        if 'symbol' in filtered_data.columns:
            # Group by symbol and check trading days
            symbol_counts = filtered_data.groupby('symbol').size()
            valid_symbols = symbol_counts[symbol_counts >= self.min_trading_days].index
            filtered_data = filtered_data[filtered_data['symbol'].isin(valid_symbols)]
        else:
            # Single symbol case
            if len(filtered_data) < self.min_trading_days:
                return pd.DataFrame()  # Return empty if not enough data
        
        return filtered_data
    
    def get_filter_info(self) -> Dict[str, Any]:
        """Get information about the filter configuration."""
        return {
            'filter_type': 'TimeFilter',
            'exclude_dates': [d.strftime('%Y-%m-%d') for d in self.exclude_dates],
            'include_dates': [d.strftime('%Y-%m-%d') for d in self.include_dates] if self.include_dates else 'all',
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'exclude_earnings_periods': self.exclude_earnings_periods,
            'exclude_market_holidays': self.exclude_market_holidays,
            'min_trading_days': self.min_trading_days
        }


class LiquidityFilter(BaseFilter):
    """
    Filter stocks based on liquidity measures.
    
    This filter focuses specifically on liquidity-related metrics:
    - Average daily volume
    - Bid-ask spreads (if available)
    - Price impact measures
    - Market depth
    """
    
    def __init__(self,
                 min_avg_volume: float = 1000000.0,
                 volume_window: int = 20,
                 max_bid_ask_spread: Optional[float] = None,
                 min_dollar_volume: Optional[float] = None):
        """
        Initialize liquidity filter.
        
        Args:
            min_avg_volume: Minimum average daily volume
            volume_window: Window for calculating average volume
            max_bid_ask_spread: Maximum bid-ask spread percentage
            min_dollar_volume: Minimum dollar volume (price * volume)
        """
        self.min_avg_volume = min_avg_volume
        self.volume_window = volume_window
        self.max_bid_ask_spread = max_bid_ask_spread
        self.min_dollar_volume = min_dollar_volume
    
    def apply_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply liquidity filters to the data."""
        if data.empty or 'volume' not in data.columns:
            return data
        
        filtered_data = data.copy()
        
        # Calculate average volume
        if 'symbol' in filtered_data.columns:
            # Group by symbol for multi-symbol data
            filtered_data['avg_volume'] = filtered_data.groupby('symbol')['volume'].transform(
                lambda x: x.rolling(self.volume_window, min_periods=1).mean()
            )
        else:
            # Single symbol data
            filtered_data['avg_volume'] = filtered_data['volume'].rolling(
                self.volume_window, min_periods=1
            ).mean()
        
        # Filter by average volume
        filtered_data = filtered_data[filtered_data['avg_volume'] >= self.min_avg_volume]
        
        # Filter by dollar volume if specified
        if self.min_dollar_volume is not None and 'close' in filtered_data.columns:
            dollar_volume = filtered_data['volume'] * filtered_data['close']
            filtered_data = filtered_data[dollar_volume >= self.min_dollar_volume]
        
        # Filter by bid-ask spread if available
        if (self.max_bid_ask_spread is not None and 
            'bid' in filtered_data.columns and 'ask' in filtered_data.columns):
            spread_pct = (filtered_data['ask'] - filtered_data['bid']) / filtered_data['close']
            filtered_data = filtered_data[spread_pct <= self.max_bid_ask_spread]
        
        # Clean up temporary columns
        if 'avg_volume' in filtered_data.columns:
            filtered_data = filtered_data.drop('avg_volume', axis=1)
        
        return filtered_data
    
    def get_filter_info(self) -> Dict[str, Any]:
        """Get information about the filter configuration."""
        return {
            'filter_type': 'LiquidityFilter',
            'min_avg_volume': self.min_avg_volume,
            'volume_window': self.volume_window,
            'max_bid_ask_spread': self.max_bid_ask_spread,
            'min_dollar_volume': self.min_dollar_volume
        }


class CompositeFilter(BaseFilter):
    """
    Combine multiple filters with AND/OR logic.
    
    This filter allows combining multiple filters with different logic:
    - AND: All filters must pass
    - OR: At least one filter must pass
    """
    
    def __init__(self, filters: List[BaseFilter], logic: str = "AND"):
        """
        Initialize composite filter.
        
        Args:
            filters: List of filters to combine
            logic: Combination logic ("AND" or "OR")
        """
        self.filters = filters
        self.logic = logic.upper()
        
        if self.logic not in ["AND", "OR"]:
            raise ValueError("Logic must be 'AND' or 'OR'")
    
    def apply_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply composite filter logic."""
        if not self.filters:
            return data
        
        if self.logic == "AND":
            # Apply all filters sequentially (AND logic)
            filtered_data = data.copy()
            for filter_obj in self.filters:
                filtered_data = filter_obj.apply_filter(filtered_data)
                if filtered_data.empty:
                    break
            return filtered_data
        
        else:  # OR logic
            # Apply each filter separately and combine results
            results = []
            for filter_obj in self.filters:
                result = filter_obj.apply_filter(data)
                if not result.empty:
                    results.append(result)
            
            if not results:
                return pd.DataFrame()
            
            # Combine all results and remove duplicates, preserve original index
            combined = pd.concat(results, ignore_index=False)
            return combined.drop_duplicates()
    
    def get_filter_info(self) -> Dict[str, Any]:
        """Get information about the composite filter."""
        return {
            'filter_type': 'CompositeFilter',
            'logic': self.logic,
            'num_filters': len(self.filters),
            'filters': [f.get_filter_info() for f in self.filters]
        } 