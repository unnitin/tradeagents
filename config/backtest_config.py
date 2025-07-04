"""
Backtest configuration management.

This module provides classes for loading and managing backtest configurations
from YAML files with validation and default value handling.
"""

import yaml
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union
from pathlib import Path


@dataclass
class BacktestConfig:
    """
    Configuration class for backtesting parameters.
    
    This class holds all configurable parameters for a backtest
    including initial capital, commission rates, position sizing,
    and risk management settings.
    """
    
    initial_capital: float = 100000.0
    commission_rate: float = 0.0005  # 0.05% per trade
    slippage_rate: float = 0.0001    # 0.01% slippage
    max_position_size: float = 0.25  # 25% of portfolio max
    position_sizing_method: str = "equal_weight"  # equal_weight, kelly, fixed_dollar
    risk_free_rate: float = 0.02     # 2% annual risk-free rate
    benchmark_symbol: str = "SPY"    # Benchmark for comparison
    
    # Risk management
    max_drawdown_limit: Optional[float] = None  # Stop trading if exceeded
    max_daily_loss: Optional[float] = None      # Daily loss limit
    max_positions: Optional[int] = None         # Maximum number of positions
    
    # Rebalancing
    rebalance_frequency: Optional[str] = None   # daily, weekly, monthly
    rebalance_threshold: Optional[float] = None # Rebalance if allocation drift exceeds this
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate configuration parameters."""
        if self.initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        
        if not 0 <= self.commission_rate <= 0.1:
            raise ValueError("Commission rate must be between 0 and 10%")
        
        if not 0 <= self.slippage_rate <= 0.1:
            raise ValueError("Slippage rate must be between 0 and 10%")
        
        if not 0 < self.max_position_size <= 1:
            raise ValueError("Max position size must be between 0 and 100%")
        
        if self.position_sizing_method not in ["equal_weight", "kelly", "fixed_dollar"]:
            raise ValueError("Position sizing method must be 'equal_weight', 'kelly', or 'fixed_dollar'")
        
        if self.risk_free_rate < 0 or self.risk_free_rate > 0.2:
            raise ValueError("Risk-free rate must be between 0 and 20%")
        
        if self.max_drawdown_limit is not None:
            if not 0.05 <= self.max_drawdown_limit <= 0.95:
                raise ValueError("Max drawdown limit must be between 5% and 95%")
        
        if self.max_daily_loss is not None:
            if not 0.01 <= self.max_daily_loss <= 0.5:
                raise ValueError("Max daily loss must be between 1% and 50%")
        
        if self.rebalance_frequency is not None:
            valid_frequencies = ["daily", "weekly", "monthly", "quarterly"]
            if self.rebalance_frequency not in valid_frequencies:
                raise ValueError(f"Rebalance frequency must be one of {valid_frequencies}")


class BacktestConfigManager:
    """
    Manager class for loading and handling backtest configurations.
    
    This class provides methods to load configurations from YAML files,
    validate settings, and create BacktestConfig instances.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config manager.
        
        Args:
            config_path: Path to the backtest.yaml config file
        """
        if config_path is None:
            # Default to config/backtest.yaml relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "backtest.yaml"
        
        self.config_path = Path(config_path)
        self._config_data = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                self._config_data = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Backtest config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing backtest config YAML: {e}")
    
    def get_config(self, config_name: str = "default") -> BacktestConfig:
        """
        Get a backtest configuration by name.
        
        Args:
            config_name: Name of the configuration to load (default, conservative, aggressive, etc.)
            
        Returns:
            BacktestConfig instance with the specified configuration
        """
        if config_name == "default":
            config_dict = self._config_data.get("default", {})
        else:
            config_dict = self._config_data.get("configurations", {}).get(config_name, {})
            if not config_dict:
                raise ValueError(f"Configuration '{config_name}' not found")
            
            # Merge with default values for any missing parameters
            default_config = self._config_data.get("default", {})
            merged_config = {**default_config, **config_dict}
            config_dict = merged_config
        
        # Convert to BacktestConfig instance
        return self._dict_to_config(config_dict)
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> BacktestConfig:
        """Convert dictionary to BacktestConfig instance."""
        # Filter only valid BacktestConfig fields
        valid_fields = set(BacktestConfig.__dataclass_fields__.keys())
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
        
        return BacktestConfig(**filtered_dict)
    
    def list_available_configs(self) -> list:
        """Get list of available configuration names."""
        configs = ["default"]
        if "configurations" in self._config_data:
            configs.extend(self._config_data["configurations"].keys())
        return configs
    
    def get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get validation rules from config."""
        return self._config_data.get("validation", {})
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance calculation settings."""
        return self._config_data.get("performance", {})
    
    def get_reporting_settings(self) -> Dict[str, Any]:
        """Get reporting and output settings."""
        return self._config_data.get("reporting", {})
    
    def validate_config(self, config: BacktestConfig) -> bool:
        """
        Validate a configuration against the rules in the YAML file.
        
        Args:
            config: BacktestConfig instance to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        validation_rules = self.get_validation_rules()
        
        for field_name, rules in validation_rules.items():
            if hasattr(config, field_name):
                value = getattr(config, field_name)
                if value is not None:  # Skip validation for None values
                    if "min" in rules and value < rules["min"]:
                        raise ValueError(f"{field_name} must be >= {rules['min']}, got {value}")
                    if "max" in rules and value > rules["max"]:
                        raise ValueError(f"{field_name} must be <= {rules['max']}, got {value}")
        
        return True
    
    def create_custom_config(self, base_config: str = "default", **overrides) -> BacktestConfig:
        """
        Create a custom configuration by overriding specific parameters.
        
        Args:
            base_config: Base configuration to start from
            **overrides: Parameters to override
            
        Returns:
            BacktestConfig instance with custom settings
        """
        base = self.get_config(base_config)
        
        # Update with overrides
        for key, value in overrides.items():
            if hasattr(base, key):
                setattr(base, key, value)
            else:
                raise ValueError(f"Invalid configuration parameter: {key}")
        
        # Validate the custom configuration
        self.validate_config(base)
        
        return base


# Convenience functions for easy access
def load_backtest_config(config_name: str = "default", config_path: Optional[str] = None) -> BacktestConfig:
    """
    Load a backtest configuration by name.
    
    Args:
        config_name: Name of the configuration to load
        config_path: Optional path to config file
        
    Returns:
        BacktestConfig instance
    """
    manager = BacktestConfigManager(config_path)
    return manager.get_config(config_name)


def create_backtest_config(**overrides) -> BacktestConfig:
    """
    Create a custom backtest configuration with parameter overrides.
    
    Args:
        **overrides: Configuration parameters to override
        
    Returns:
        BacktestConfig instance
    """
    manager = BacktestConfigManager()
    return manager.create_custom_config(**overrides) 