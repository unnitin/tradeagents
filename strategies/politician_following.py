import pandas as pd
from .base import Strategy
from data import DataFetcher


class PoliticianFollowingStrategy(Strategy):
    """
    Strategy that follows politician trades by generating buy/sell signals
    when politicians make trades in specific stocks.
    """
    
    def __init__(self, politician_names: list = None, days_back: int = 7, 
                 min_trade_amount: str = "$1,000", signal_delay_days: int = 1):
        """
        Initialize politician following strategy.
        
        Args:
            politician_names: List of politician names to follow (None = all)
            days_back: Number of days to look back for trades
            min_trade_amount: Minimum trade amount to consider
            signal_delay_days: Days to wait after trade filing before signal
        """
        self.politician_names = politician_names or []
        self.days_back = days_back
        self.min_trade_amount = min_trade_amount
        self.signal_delay_days = signal_delay_days
        self.data_fetcher = DataFetcher()
        
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on politician trades.
        
        Args:
            df: DataFrame with market data (must have ticker info)
            
        Returns:
            pd.Series of trading signals (1=buy, -1=sell, 0=hold)
        """
        signal = pd.Series(0, index=df.index)
        
        try:
            # Get recent politician trades
            politician_trades = self.data_fetcher.get_politician_trades("both", self.days_back)
            
            if politician_trades.empty:
                return signal
            
            # Filter by specific politicians if specified
            if self.politician_names:
                politician_filter = politician_trades['politician_name'].str.contains(
                    '|'.join(self.politician_names), case=False, na=False
                )
                politician_trades = politician_trades[politician_filter]
            
            # Process each trade
            for _, trade in politician_trades.iterrows():
                trade_date = pd.to_datetime(trade['trade_date'])
                
                # Calculate signal date (add delay)
                signal_date = trade_date + pd.Timedelta(days=self.signal_delay_days)
                
                # Find the closest trading day for signal
                if signal_date in df.index:
                    target_date = signal_date
                else:
                    # Find next available trading day
                    future_dates = df.index[df.index >= signal_date]
                    if len(future_dates) > 0:
                        target_date = future_dates[0]
                    else:
                        continue
                
                # Generate signal based on trade type
                trade_type = str(trade.get('trade_type', '')).upper()
                if 'BUY' in trade_type or 'PURCHASE' in trade_type:
                    signal[target_date] = 1  # Follow the buy
                elif 'SELL' in trade_type or 'SALE' in trade_type:
                    signal[target_date] = -1  # Follow the sell
                    
        except Exception as e:
            print(f"Warning: Could not fetch politician trades: {e}")
            # Return neutral signals if data fetch fails
            return signal
            
        return signal


class PelosiTrackingStrategy(Strategy):
    """
    Specialized strategy for tracking Nancy Pelosi's trades.
    """
    
    def __init__(self, days_back: int = 14, signal_delay_days: int = 2):
        """
        Initialize Pelosi tracking strategy.
        
        Args:
            days_back: Days to look back for Pelosi trades
            signal_delay_days: Days to wait after trade before signal
        """
        self.days_back = days_back
        self.signal_delay_days = signal_delay_days
        self.data_fetcher = DataFetcher()
        
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate signals based on Nancy Pelosi's trades."""
        signal = pd.Series(0, index=df.index)
        
        try:
            # Get Pelosi trades specifically
            pelosi_trades = self.data_fetcher.get_politician_by_name("Nancy Pelosi", self.days_back)
            
            if pelosi_trades.empty:
                return signal
            
            # Process Pelosi trades
            for _, trade in pelosi_trades.iterrows():
                trade_date = pd.to_datetime(trade['trade_date'])
                signal_date = trade_date + pd.Timedelta(days=self.signal_delay_days)
                
                # Find target trading day
                if signal_date in df.index:
                    target_date = signal_date
                else:
                    future_dates = df.index[df.index >= signal_date]
                    if len(future_dates) > 0:
                        target_date = future_dates[0]
                    else:
                        continue
                
                # Generate signal (Pelosi effect - her trades often signal market moves)
                trade_type = str(trade.get('trade_type', '')).upper()
                if 'BUY' in trade_type or 'PURCHASE' in trade_type:
                    signal[target_date] = 1  # Strong buy signal for Pelosi buys
                elif 'SELL' in trade_type or 'SALE' in trade_type:
                    signal[target_date] = -1  # Strong sell signal for Pelosi sells
                    
        except Exception as e:
            print(f"Warning: Could not fetch Pelosi trades: {e}")
            
        return signal


class CongressMomentumStrategy(Strategy):
    """
    Strategy that identifies momentum when multiple politicians trade the same direction.
    """
    
    def __init__(self, days_back: int = 30, min_politicians: int = 2, 
                 momentum_window: int = 7):
        """
        Initialize Congress momentum strategy.
        
        Args:
            days_back: Days to look back for trades
            min_politicians: Minimum number of politicians needed for signal
            momentum_window: Days within which trades must occur for momentum
        """
        self.days_back = days_back
        self.min_politicians = min_politicians
        self.momentum_window = momentum_window
        self.data_fetcher = DataFetcher()
        
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate signals based on Congress trading momentum."""
        signal = pd.Series(0, index=df.index)
        
        try:
            # Get all politician trades
            all_trades = self.data_fetcher.get_politician_trades("both", self.days_back)
            
            if all_trades.empty:
                return signal
            
            # Group trades by date windows to find momentum
            all_trades['trade_date'] = pd.to_datetime(all_trades['trade_date'])
            all_trades = all_trades.sort_values('trade_date')
            
            # Check each date in our signal range
            for date in df.index:
                # Look for trades in momentum window before this date
                window_start = date - pd.Timedelta(days=self.momentum_window)
                window_trades = all_trades[
                    (all_trades['trade_date'] >= window_start) & 
                    (all_trades['trade_date'] <= date)
                ]
                
                if len(window_trades) < self.min_politicians:
                    continue
                
                # Count buy vs sell signals
                buy_politicians = set()
                sell_politicians = set()
                
                for _, trade in window_trades.iterrows():
                    politician = trade['politician_name']
                    trade_type = str(trade.get('trade_type', '')).upper()
                    
                    if 'BUY' in trade_type or 'PURCHASE' in trade_type:
                        buy_politicians.add(politician)
                    elif 'SELL' in trade_type or 'SALE' in trade_type:
                        sell_politicians.add(politician)
                
                # Generate momentum signal
                if len(buy_politicians) >= self.min_politicians:
                    signal[date] = 1  # Bullish momentum
                elif len(sell_politicians) >= self.min_politicians:
                    signal[date] = -1  # Bearish momentum
                    
        except Exception as e:
            print(f"Warning: Could not analyze Congress momentum: {e}")
            
        return signal 