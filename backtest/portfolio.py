"""
Portfolio management for backtesting.

This module provides the Portfolio class that manages positions, cash,
and trade execution during backtesting simulation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Position:
    """Represents a position in a security."""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    entry_date: Optional[datetime] = None
    
    def update_price(self, new_price: float) -> None:
        """Update current price and unrealized P&L."""
        self.current_price = new_price
        self.unrealized_pnl = (new_price - self.avg_price) * self.quantity
    
    def get_market_value(self) -> float:
        """Get current market value of the position."""
        return self.current_price * self.quantity
    
    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl


@dataclass
class Trade:
    """Represents a completed trade."""
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    timestamp: datetime
    commission: float = 0.0
    slippage: float = 0.0
    
    def get_total_cost(self) -> float:
        """Get total cost including commission and slippage."""
        return (self.price * self.quantity) + self.commission + self.slippage


class Portfolio:
    """
    Portfolio management for backtesting.
    
    This class manages:
    - Cash and position tracking
    - Trade execution with costs
    - Portfolio valuation
    - Performance tracking
    """
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 commission_rate: float = 0.001,
                 slippage_rate: float = 0.0005):
        """
        Initialize portfolio.
        
        Args:
            initial_capital: Starting capital
            commission_rate: Commission rate per trade (as decimal)
            slippage_rate: Slippage rate per trade (as decimal)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        # Portfolio state
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        
        # Performance tracking
        self.portfolio_value_history = []
        self.daily_returns = []
        
    def reset(self, initial_capital: Optional[float] = None) -> None:
        """Reset portfolio to initial state."""
        if initial_capital is not None:
            self.initial_capital = initial_capital
        
        self.cash = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.portfolio_value_history = []
        self.daily_returns = []
    
    def buy(self, symbol: str, quantity: int, price: float, timestamp: datetime) -> bool:
        """
        Execute a buy order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares to buy
            price: Price per share
            timestamp: Trade timestamp
            
        Returns:
            True if trade was executed, False otherwise
        """
        # Calculate costs
        gross_cost = quantity * price
        commission = gross_cost * self.commission_rate
        slippage = gross_cost * self.slippage_rate
        total_cost = gross_cost + commission + slippage
        
        # Check if we have enough cash
        if total_cost > self.cash:
            return False
        
        # Execute trade
        self.cash -= total_cost
        
        # Update position
        if symbol in self.positions:
            # Add to existing position
            old_pos = self.positions[symbol]
            total_quantity = old_pos.quantity + quantity
            total_cost_basis = (old_pos.avg_price * old_pos.quantity) + gross_cost
            new_avg_price = total_cost_basis / total_quantity
            
            self.positions[symbol].quantity = total_quantity
            self.positions[symbol].avg_price = new_avg_price
            self.positions[symbol].current_price = price
        else:
            # Create new position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                current_price=price,
                entry_date=timestamp
            )
        
        # Record trade
        trade = Trade(
            symbol=symbol,
            side='BUY',
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            commission=commission,
            slippage=slippage
        )
        self.trade_history.append(trade)
        
        return True
    
    def sell(self, symbol: str, quantity: int, price: float, timestamp: datetime) -> bool:
        """
        Execute a sell order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares to sell
            price: Price per share
            timestamp: Trade timestamp
            
        Returns:
            True if trade was executed, False otherwise
        """
        # Check if we have the position
        if symbol not in self.positions or self.positions[symbol].quantity < quantity:
            return False
        
        # Calculate proceeds
        gross_proceeds = quantity * price
        commission = gross_proceeds * self.commission_rate
        slippage = gross_proceeds * self.slippage_rate
        net_proceeds = gross_proceeds - commission - slippage
        
        # Update cash
        self.cash += net_proceeds
        
        # Update position
        position = self.positions[symbol]
        
        # Calculate realized P&L
        realized_pnl = (price - position.avg_price) * quantity
        position.realized_pnl += realized_pnl
        
        # Update position quantity
        position.quantity -= quantity
        
        # Remove position if fully sold
        if position.quantity == 0:
            del self.positions[symbol]
        else:
            # Update current price
            position.current_price = price
        
        # Record trade
        trade = Trade(
            symbol=symbol,
            side='SELL',
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            commission=commission,
            slippage=slippage
        )
        self.trade_history.append(trade)
        
        return True
    
    def update_portfolio_value(self, market_data: pd.DataFrame) -> float:
        """
        Update portfolio value based on current market prices.
        
        Args:
            market_data: DataFrame with current market prices
            
        Returns:
            Current portfolio value
        """
                 # Update position prices
        for symbol, position in self.positions.items():
            symbol_data = market_data[market_data['symbol'] == symbol]
            if not symbol_data.empty:
                # Get the last close price for this symbol
                current_price = float(symbol_data['close'].iloc[-1] if hasattr(symbol_data['close'], 'iloc') 
                                     else symbol_data['close'].tolist()[-1])
                position.update_price(current_price)
        
        # Calculate total portfolio value
        positions_value = sum(pos.get_market_value() for pos in self.positions.values())
        total_value = self.cash + positions_value
        
        # Record portfolio value
        self.portfolio_value_history.append(total_value)
        
        return total_value
    
    def get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state."""
        positions_value = sum(pos.get_market_value() for pos in self.positions.values())
        total_value = self.cash + positions_value
        
        return {
            'cash': self.cash,
            'positions_value': positions_value,
            'total_value': total_value,
            'num_positions': len(self.positions),
            'positions': {symbol: {
                'quantity': pos.quantity,
                'avg_price': pos.avg_price,
                'current_price': pos.current_price,
                'market_value': pos.get_market_value(),
                'unrealized_pnl': pos.unrealized_pnl,
                'realized_pnl': pos.realized_pnl
            } for symbol, pos in self.positions.items()}
        }
    
    def get_position(self, symbol: str) -> int:
        """Get current position size for a symbol."""
        if symbol in self.positions:
            return self.positions[symbol].quantity
        return 0
    
    def get_available_cash(self) -> float:
        """Get available cash for trading."""
        return self.cash
    
    def get_total_value(self) -> float:
        """Get total portfolio value."""
        positions_value = sum(pos.get_market_value() for pos in self.positions.values())
        return self.cash + positions_value
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get trade history as list of dictionaries."""
        return [
            {
                'symbol': trade.symbol,
                'side': trade.side,
                'quantity': trade.quantity,
                'price': trade.price,
                'timestamp': trade.timestamp,
                'commission': trade.commission,
                'slippage': trade.slippage,
                'total_cost': trade.get_total_cost()
            }
            for trade in self.trade_history
        ]
    
    def get_realized_pnl(self) -> float:
        """Get total realized P&L."""
        return sum(pos.realized_pnl for pos in self.positions.values())
    
    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)."""
        return self.get_realized_pnl() + self.get_unrealized_pnl()
    
    def get_total_commissions(self) -> float:
        """Get total commissions paid."""
        return sum(trade.commission for trade in self.trade_history)
    
    def get_total_slippage(self) -> float:
        """Get total slippage costs."""
        return sum(trade.slippage for trade in self.trade_history)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        total_value = self.get_total_value()
        total_return = (total_value - self.initial_capital) / self.initial_capital
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'cash': self.cash,
            'positions_value': sum(pos.get_market_value() for pos in self.positions.values()),
            'num_positions': len(self.positions),
            'num_trades': len(self.trade_history),
            'realized_pnl': self.get_realized_pnl(),
            'unrealized_pnl': self.get_unrealized_pnl(),
            'total_pnl': self.get_total_pnl(),
            'total_commissions': self.get_total_commissions(),
            'total_slippage': self.get_total_slippage()
        } 