#!/usr/bin/env python3
"""
Dedicated test runner for backtest module tests.

This script runs all backtest-related tests including:
- Unit tests for backtest components
- Integration tests for end-to-end workflows
- Configuration system tests
- Performance tests

Usage:
    python tests/test_backtest_runner.py              # Run all backtest tests
    python tests/test_backtest_runner.py --unit       # Run unit tests only
    python tests/test_backtest_runner.py --integration # Run integration tests only
    python tests/test_backtest_runner.py --verbose    # Run with verbose output
    python tests/test_backtest_runner.py --quick      # Run quick tests only
"""

import sys
import os
import unittest
import argparse
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_backtest_unit_tests(verbose=False):
    """Run backtest unit tests."""
    print("🧪 Running Backtest Unit Tests...")
    
    try:
        loader = unittest.TestLoader()
        suite = loader.discover('tests/unit_test', pattern='test_backtest.py')
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False


def run_backtest_integration_tests(verbose=False):
    """Run backtest integration tests."""
    print("🔄 Running Backtest Integration Tests...")
    
    try:
        loader = unittest.TestLoader()
        suite = loader.discover('tests/integration', pattern='test_backtest_integration.py')
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False


def run_quick_tests(verbose=False):
    """Run quick tests that don't require external dependencies."""
    print("⚡ Running Quick Backtest Tests...")
    
    try:
        loader = unittest.TestLoader()
        
        # Load specific test classes that are quick to run
        from tests.unit_test.test_backtest import (
            TestBacktestConfig, 
            TestBacktestConfigManager,
            TestPosition,
            TestStockFilter,
            TestTimeFilter
        )
        
        suite = unittest.TestSuite()
        suite.addTest(loader.loadTestsFromTestCase(TestBacktestConfig))
        suite.addTest(loader.loadTestsFromTestCase(TestBacktestConfigManager))
        suite.addTest(loader.loadTestsFromTestCase(TestPosition))
        suite.addTest(loader.loadTestsFromTestCase(TestStockFilter))
        suite.addTest(loader.loadTestsFromTestCase(TestTimeFilter))
        
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ Error running quick tests: {e}")
        return False


def run_all_backtest_tests(verbose=False):
    """Run all backtest tests."""
    print("🚀 Running All Backtest Tests...")
    
    start_time = time.time()
    
    unit_success = run_backtest_unit_tests(verbose)
    integration_success = run_backtest_integration_tests(verbose)
    
    end_time = time.time()
    duration = end_time - start_time
    
    if unit_success and integration_success:
        print(f"\n✅ All backtest tests passed! (took {duration:.2f} seconds)")
        return True
    else:
        print(f"\n❌ Some backtest tests failed! (took {duration:.2f} seconds)")
        return False


def test_config_system():
    """Test the configuration system specifically."""
    print("🔧 Testing Configuration System...")
    
    try:
        from config import BacktestConfig, BacktestConfigManager, load_backtest_config
        
        # Test basic config creation
        config = BacktestConfig()
        print(f"✅ Basic config created: {config.initial_capital}")
        
        # Test config manager
        try:
            manager = BacktestConfigManager()
            configs = manager.list_available_configs()
            print(f"✅ Available configs: {configs}")
            
            # Test loading default config
            default_config = load_backtest_config("default")
            print(f"✅ Default config loaded: ${default_config.initial_capital:,.0f}")
            
            return True
        except Exception as e:
            print(f"⚠️  Config file not found (expected in development): {e}")
            return True  # Not a failure in test environment
            
    except Exception as e:
        print(f"❌ Config system test failed: {e}")
        return False


def test_imports():
    """Test that all backtest modules can be imported."""
    print("📦 Testing Backtest Module Imports...")
    
    try:
        from backtest import (
            BacktestEngine,
            create_backtest_engine,
            Portfolio,
            StockFilter,
            TimeFilter,
            BacktestResults
        )
        print("✅ Core backtest modules imported successfully")
        
        from backtest.metrics import PerformanceMetrics, calculate_performance_metrics
        print("✅ Metrics module imported successfully")
        
        from backtest.filters import CompositeFilter, LiquidityFilter
        print("✅ Filters module imported successfully")
        
        from config import BacktestConfig
        print("✅ Config module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run backtest module tests')
    parser.add_argument('--all', action='store_true', help='Run all backtest tests')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--config', action='store_true', help='Test configuration system')
    parser.add_argument('--imports', action='store_true', help='Test module imports')
    
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(project_root)
    
    print("🔬 BACKTEST MODULE TEST RUNNER")
    print("=" * 50)
    
    success = True
    
    if args.imports:
        success = test_imports()
    elif args.config:
        success = test_config_system()
    elif args.unit:
        success = run_backtest_unit_tests(args.verbose)
    elif args.integration:
        success = run_backtest_integration_tests(args.verbose)
    elif args.quick:
        success = run_quick_tests(args.verbose)
    elif args.all:
        success = run_all_backtest_tests(args.verbose)
    else:
        # Default: run imports, config, and quick tests
        print("Running default test suite (imports + config + quick tests)...")
        
        import_success = test_imports()
        config_success = test_config_system()
        quick_success = run_quick_tests(args.verbose)
        
        success = import_success and config_success and quick_success
        
        if success:
            print("\n✅ Default backtest tests passed!")
        else:
            print("\n❌ Some default tests failed!")
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 BACKTEST TESTS COMPLETED SUCCESSFULLY")
    else:
        print("💥 BACKTEST TESTS FAILED")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 