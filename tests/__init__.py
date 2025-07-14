"""
Test suite for the trading strategies system.

This package contains comprehensive tests organized into:
- unit_test: Tests for individual components
- integration: Tests for complete system workflows

Usage:
    # Run all tests
    python -m unittest discover tests/ -v
    
    # Run only unit tests
    python -m unittest discover tests/unit_test/ -v
    
    # Run only integration tests
    python -m unittest discover tests/integration/ -v
    
    # Run specific test file
    python -m unittest tests.unit_test.test_composer -v
    python -m unittest tests.integration.test_integration -v
"""

__all__ = [
    'unit_test',
    'integration'
]
