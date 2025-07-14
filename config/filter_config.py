"""
Filter configuration classes for backtesting.

This module contains configuration classes for various filters used in backtesting.
"""

import yaml
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from pathlib import Path


@dataclass
class FilterConfig:
    """Configuration for filtering parameters."""
    min_volume: float = 1000000.0      # Minimum daily trading volume
    min_price: float = 5.0             # Minimum stock price
    max_price: Optional[float] = None  # Maximum stock price
    min_market_cap: Optional[float] = None  # Minimum market capitalization
    max_volatility: Optional[float] = None  # Maximum volatility threshold
    exclude_symbols: Optional[List[str]] = None  # Symbols to exclude
    include_symbols: Optional[List[str]] = None  # Only include these symbols
    
    def __post_init__(self):
        if self.exclude_symbols is None:
            self.exclude_symbols = []
        if self.include_symbols is None:
            self.include_symbols = []


class FilterConfigManager:
    """Manager for loading and handling filter configurations from YAML files."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the filter configuration manager.
        
        Args:
            config_path: Path to the filter configuration YAML file
        """
        if config_path is None:
            # Default to filters.yaml in the same directory
            config_dir = Path(__file__).parent
            self.config_path = config_dir / "filters.yaml"
        else:
            self.config_path = Path(config_path)
        
        self._config_data: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self._config_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Filter configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration file: {e}")
    
    def get_config(self, config_name: str = "default") -> Dict[str, Any]:
        """
        Get a specific filter configuration.
        
        Args:
            config_name: Name of the configuration to retrieve
            
        Returns:
            Dictionary containing the configuration
        """
        if self._config_data is None:
            self._load_config()
        
        assert self._config_data is not None  # Type checker hint
        
        if config_name == "default":
            return self._config_data.get("default", {})
        
        configurations = self._config_data.get("configurations", {})
        if config_name not in configurations:
            available_configs = list(configurations.keys())
            raise ValueError(f"Configuration '{config_name}' not found. Available: {available_configs}")
        
        return configurations[config_name]
    
    def get_stock_filter_config(self, config_name: str = "default") -> FilterConfig:
        """
        Get a stock filter configuration as a FilterConfig object.
        
        Args:
            config_name: Name of the configuration to retrieve
            
        Returns:
            FilterConfig object with the specified configuration
        """
        config = self.get_config(config_name)
        stock_config = config.get("stock_filter", {})
        
        return FilterConfig(
            min_volume=stock_config.get("min_volume", 1000000.0),
            min_price=stock_config.get("min_price", 5.0),
            max_price=stock_config.get("max_price"),
            min_market_cap=stock_config.get("min_market_cap"),
            max_volatility=stock_config.get("max_volatility"),
            exclude_symbols=stock_config.get("exclude_symbols", []),
            include_symbols=stock_config.get("include_symbols", [])
        )
    
    def get_time_filter_config(self, config_name: str = "default") -> Dict[str, Any]:
        """
        Get time filter configuration.
        
        Args:
            config_name: Name of the configuration to retrieve
            
        Returns:
            Dictionary containing time filter parameters
        """
        config = self.get_config(config_name)
        return config.get("time_filter", {})
    
    def get_liquidity_filter_config(self, config_name: str = "default") -> Dict[str, Any]:
        """
        Get liquidity filter configuration.
        
        Args:
            config_name: Name of the configuration to retrieve
            
        Returns:
            Dictionary containing liquidity filter parameters
        """
        config = self.get_config(config_name)
        return config.get("liquidity_filter", {})
    
    def get_combination_config(self, combination_name: str) -> Dict[str, Any]:
        """
        Get a filter combination configuration.
        
        Args:
            combination_name: Name of the combination to retrieve
            
        Returns:
            Dictionary containing the combination configuration
        """
        if self._config_data is None:
            self._load_config()
        
        assert self._config_data is not None  # Type checker hint
        
        combinations = self._config_data.get("combinations", {})
        if combination_name not in combinations:
            available_combinations = list(combinations.keys())
            raise ValueError(f"Combination '{combination_name}' not found. Available: {available_combinations}")
        
        return combinations[combination_name]
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get validation rules for filter parameters.
        
        Returns:
            Dictionary containing validation rules
        """
        if self._config_data is None:
            self._load_config()
        
        assert self._config_data is not None  # Type checker hint
        
        return self._config_data.get("validation", {})
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get global filter settings.
        
        Returns:
            Dictionary containing global settings
        """
        if self._config_data is None:
            self._load_config()
        
        assert self._config_data is not None  # Type checker hint
        
        return self._config_data.get("settings", {})
    
    def list_available_configs(self) -> List[str]:
        """
        List all available filter configurations.
        
        Returns:
            List of available configuration names
        """
        if self._config_data is None:
            self._load_config()
        
        assert self._config_data is not None  # Type checker hint
        
        configs = ["default"]
        configurations = self._config_data.get("configurations", {})
        configs.extend(list(configurations.keys()))
        
        return configs
    
    def list_available_combinations(self) -> List[str]:
        """
        List all available filter combinations.
        
        Returns:
            List of available combination names
        """
        if self._config_data is None:
            self._load_config()
        
        assert self._config_data is not None  # Type checker hint
        
        combinations = self._config_data.get("combinations", {})
        return list(combinations.keys())
    
    def validate_config(self, config_name: str = "default") -> bool:
        """
        Validate a configuration against the validation rules.
        
        Args:
            config_name: Name of the configuration to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        config = self.get_config(config_name)
        validation_rules = self.get_validation_rules()
        
        # Validate stock filter
        stock_filter = config.get("stock_filter", {})
        stock_rules = validation_rules.get("stock_filter", {})
        
        for param, value in stock_filter.items():
            if param in stock_rules and value is not None:
                rules = stock_rules[param]
                if "min" in rules and value < rules["min"]:
                    raise ValueError(f"Stock filter {param} ({value}) below minimum ({rules['min']})")
                if "max" in rules and value > rules["max"]:
                    raise ValueError(f"Stock filter {param} ({value}) above maximum ({rules['max']})")
        
        # Validate time filter
        time_filter = config.get("time_filter", {})
        time_rules = validation_rules.get("time_filter", {})
        
        for param, value in time_filter.items():
            if param in time_rules and value is not None:
                rules = time_rules[param]
                if "min" in rules and value < rules["min"]:
                    raise ValueError(f"Time filter {param} ({value}) below minimum ({rules['min']})")
                if "max" in rules and value > rules["max"]:
                    raise ValueError(f"Time filter {param} ({value}) above maximum ({rules['max']})")
        
        # Validate liquidity filter
        liquidity_filter = config.get("liquidity_filter", {})
        liquidity_rules = validation_rules.get("liquidity_filter", {})
        
        for param, value in liquidity_filter.items():
            if param in liquidity_rules and value is not None:
                rules = liquidity_rules[param]
                if "min" in rules and value < rules["min"]:
                    raise ValueError(f"Liquidity filter {param} ({value}) below minimum ({rules['min']})")
                if "max" in rules and value > rules["max"]:
                    raise ValueError(f"Liquidity filter {param} ({value}) above maximum ({rules['max']})")
        
        return True


def load_filter_config(config_name: str = "default", config_path: Optional[str] = None) -> FilterConfig:
    """
    Load a filter configuration from YAML file.
    
    Args:
        config_name: Name of the configuration to load
        config_path: Path to the configuration file
        
    Returns:
        FilterConfig object with the loaded configuration
    """
    manager = FilterConfigManager(config_path)
    return manager.get_stock_filter_config(config_name)


def create_filter_config_manager(config_path: Optional[str] = None) -> FilterConfigManager:
    """
    Create a filter configuration manager.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        FilterConfigManager instance
    """
    return FilterConfigManager(config_path) 