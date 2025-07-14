from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Optional, Union, Dict, Any


class Strategy(ABC):
    """
    Base class for all trading strategies.
    
    Strategies can now have filters applied at the strategy level to include/exclude
    stocks based on various criteria before generating signals. Includes advanced
    filtering capabilities like symbol-specific filters, dynamic filters, and 
    configuration-based setup.
    """
    
    def __init__(self):
        self.filters: List = []  # List of filter instances to apply
        self.filter_logic: str = "AND"  # How to combine multiple filters
        
        # Advanced filter capabilities
        self.symbol_filters: Dict[str, List] = {}  # Symbol-specific filters
        self.dynamic_filters: List = []  # Filters that change based on conditions
        self.filter_config: Dict[str, Any] = {}  # Filter configuration
        
    def set_filters(self, filters: List, logic: str = "AND") -> None:
        """
        Set filters to be applied before signal generation.
        
        Args:
            filters: List of filter instances (StockFilter, TimeFilter, etc.)
            logic: How to combine filters - "AND" or "OR"
        """
        self.filters = filters
        self.filter_logic = logic.upper()
        
    def add_filter(self, filter_instance) -> None:
        """Add a single filter to the strategy."""
        self.filters.append(filter_instance)
        
    def set_symbol_filters(self, symbol_filters: Dict[str, List]) -> None:
        """
        Set different filters for different symbols.
        
        Args:
            symbol_filters: Dict mapping symbol to list of filters
                           e.g., {"AAPL": [volume_filter], "MSFT": [price_filter]}
        """
        self.symbol_filters = symbol_filters
        
    def add_symbol_filter(self, symbol: str, filter_instance) -> None:
        """Add a filter for a specific symbol."""
        if symbol not in self.symbol_filters:
            self.symbol_filters[symbol] = []
        self.symbol_filters[symbol].append(filter_instance)
        
    def set_dynamic_filters(self, dynamic_filters: List) -> None:
        """
        Set filters that change based on market conditions.
        
        Args:
            dynamic_filters: List of filters that adapt to market conditions
        """
        self.dynamic_filters = dynamic_filters
        
    def configure_filters_from_config(self, filter_config: Dict[str, Any]) -> None:
        """
        Configure filters from YAML configuration.
        
        Args:
            filter_config: Filter configuration dictionary
        """
        self.filter_config = filter_config
        
        # Import here to avoid circular imports
        from config.filter_config import FilterConfigManager
        from filters import StockFilter, TimeFilter, LiquidityFilter
        
        # Initialize filters from config
        filters = []
        
        if 'stock_filter' in filter_config:
            stock_config = filter_config['stock_filter']
            stock_filter = StockFilter(
                min_volume=stock_config.get('min_volume', 1000000.0),
                min_price=stock_config.get('min_price', 5.0),
                max_price=stock_config.get('max_price'),
                min_market_cap=stock_config.get('min_market_cap'),
                max_volatility=stock_config.get('max_volatility'),
                exclude_symbols=stock_config.get('exclude_symbols', []),
                include_symbols=stock_config.get('include_symbols', [])
            )
            filters.append(stock_filter)
            
        if 'time_filter' in filter_config:
            time_config = filter_config['time_filter']
            time_filter = TimeFilter(
                exclude_dates=time_config.get('exclude_dates', []),
                include_dates=time_config.get('include_dates', []),
                start_time=time_config.get('start_time'),
                end_time=time_config.get('end_time'),
                exclude_earnings_periods=time_config.get('exclude_earnings_periods', False),
                exclude_market_holidays=time_config.get('exclude_market_holidays', True),
                min_trading_days=time_config.get('min_trading_days', 30)
            )
            filters.append(time_filter)
            
        if 'liquidity_filter' in filter_config:
            liquidity_config = filter_config['liquidity_filter']
            liquidity_filter = LiquidityFilter(
                min_avg_volume=liquidity_config.get('min_avg_volume', 1000000.0),
                volume_window=liquidity_config.get('volume_window', 20),
                max_bid_ask_spread=liquidity_config.get('max_bid_ask_spread'),
                min_dollar_volume=liquidity_config.get('min_dollar_volume')
            )
            filters.append(liquidity_filter)
            
        # Set the filters
        logic = filter_config.get('logic', 'AND')
        self.set_filters(filters, logic)
        
    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all configured filters to the data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Filtered DataFrame
        """
        if not self.filters:
            return df
            
        # Import here to avoid circular imports
        from filters import CompositeFilter
        
        # Use CompositeFilter to apply multiple filters with specified logic
        composite_filter = CompositeFilter(self.filters, self.filter_logic)
        return composite_filter.apply_filter(df)
    
    def _apply_symbol_specific_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply symbol-specific filters to the data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with symbol-specific filters applied
        """
        if not self.symbol_filters:
            return df
            
        filtered_dfs = []
        
        if 'symbol' in df.columns:
            # Multi-symbol data
            for symbol in df['symbol'].unique():
                symbol_df = df[df['symbol'] == symbol]
                
                if symbol in self.symbol_filters:
                    # Apply symbol-specific filters
                    from filters import CompositeFilter
                    composite_filter = CompositeFilter(
                        self.symbol_filters[symbol], 
                        self.filter_logic
                    )
                    symbol_df = composite_filter.apply_filter(symbol_df)
                    
                if not symbol_df.empty:
                    filtered_dfs.append(symbol_df)
                    
            return pd.concat(filtered_dfs, ignore_index=True) if filtered_dfs else pd.DataFrame()
        else:
            # Single symbol data - check if we have filters for this symbol
            # For single symbol, we'd need to know which symbol it is
            # This could be passed as a parameter or inferred from context
            return df
            
    def _apply_dynamic_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply dynamic filters based on market conditions.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with dynamic filters applied
        """
        if not self.dynamic_filters:
            return df
            
        # Apply dynamic filters
        from filters import CompositeFilter
        composite_filter = CompositeFilter(self.dynamic_filters, self.filter_logic)
        return composite_filter.apply_filter(df)
    
    def generate_signals_with_filters(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals with filter application.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Trading signals with filters applied
        """
        # Apply filters first
        filtered_df = self._apply_filters(df)
        
        if filtered_df.empty:
            # Return zero signals if no data passes filters
            return pd.Series(0, index=df.index)
            
        # Generate signals on filtered data
        signals = self.generate_signals(filtered_df)
        
        # Ensure signals align with original index
        # Set signals to 0 for filtered out data points
        full_signals = pd.Series(0, index=df.index)
        full_signals.loc[filtered_df.index] = signals
        
        return full_signals
        
    def generate_signals_with_advanced_filters(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals with advanced filter application.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Trading signals with advanced filters applied
        """
        # Apply standard filters first
        filtered_df = self._apply_filters(df)
        
        # Apply symbol-specific filters
        filtered_df = self._apply_symbol_specific_filters(filtered_df)
        
        # Apply dynamic filters
        filtered_df = self._apply_dynamic_filters(filtered_df)
        
        if filtered_df.empty:
            return pd.Series(0, index=df.index)
            
        # Generate signals on filtered data
        signals = self.generate_signals(filtered_df)
        
        # Align signals with original index
        full_signals = pd.Series(0, index=df.index)
        full_signals.loc[filtered_df.index] = signals
        
        return full_signals
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Return a pd.Series of trading signals (1, -1, or 0).
        
        Args:
            df: DataFrame with market data
            
        Returns:
            pd.Series with trading signals
        """
        pass
    
    def get_filter_info(self) -> Dict[str, Any]:
        """
        Get information about the filters applied to this strategy.
        
        Returns:
            Dictionary with filter information
        """
        if not self.filters:
            return {"filters": "None", "logic": "None"}
            
        filter_info = []
        for i, filter_obj in enumerate(self.filters):
            if hasattr(filter_obj, 'get_filter_info'):
                filter_info.append(filter_obj.get_filter_info())
            else:
                filter_info.append({"filter_type": type(filter_obj).__name__})
                
        return {
            "filters": filter_info,
            "logic": self.filter_logic,
            "filter_count": len(self.filters)
        }
        
    def get_advanced_filter_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about all filters.
        
        Returns:
            Dictionary with detailed filter information
        """
        base_info = self.get_filter_info()
        
        advanced_info = {
            "base_filters": base_info,
            "symbol_filters": {
                symbol: [
                    filter_obj.get_filter_info() if hasattr(filter_obj, 'get_filter_info') 
                    else {"filter_type": type(filter_obj).__name__}
                    for filter_obj in filters
                ]
                for symbol, filters in self.symbol_filters.items()
            },
            "dynamic_filters": [
                filter_obj.get_filter_info() if hasattr(filter_obj, 'get_filter_info')
                else {"filter_type": type(filter_obj).__name__}
                for filter_obj in self.dynamic_filters
            ],
            "filter_config": self.filter_config
        }
        
        return advanced_info
        
    def get_filter_requirements(self) -> Dict[str, Any]:
        """
        Define the filter requirements for this strategy.
        Default implementation returns no requirements.
        Override in subclasses to define specific requirements.
        
        Returns:
            Dictionary defining required and optional filters
        """
        return {
            "required": [],
            "optional": []
        }
        
    def validate_filters(self) -> bool:
        """
        Validate that all required filters are configured.
        
        Returns:
            True if all required filters are present
        """
        requirements = self.get_filter_requirements()
        
        required_filters = requirements.get('required', [])
        
        # Check if all required filters are present
        for required_filter in required_filters:
            if not any(
                type(filter_obj).__name__ == required_filter 
                for filter_obj in self.filters
            ):
                return False
                
        return True
