#!/usr/bin/env python3
"""
Test runner script for the trading strategies system.

This script provides convenient ways to run different test suites:
- Unit tests only
- Integration tests only 
- All tests
- Specific test files

Usage:
    python tests/run_tests.py --all          # Run all tests
    python tests/run_tests.py --unit         # Run unit tests only
    python tests/run_tests.py --integration  # Run integration tests only
    python tests/run_tests.py --fast         # Run fast unit tests only
    python tests/run_tests.py --verbose      # Run with verbose output
"""

import sys
import os
import unittest
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_unit_tests(verbose=False):
    """Run all unit tests."""
    print("🧪 Running Unit Tests...")
    loader = unittest.TestLoader()
    suite = loader.discover('tests/unit_test', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_integration_tests(verbose=False):
    """Run all integration tests."""
    print("🔄 Running Integration Tests...")
    loader = unittest.TestLoader()
    suite = loader.discover('tests/integration', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_fast_tests(verbose=False):
    """Run only fast unit tests (excluding data fetching tests)."""
    print("⚡ Running Fast Tests...")
    loader = unittest.TestLoader()
    
    # Load specific test modules that don't require external data
    from tests.unit_test.test_composer import TestComposerFunctionality
    from tests.unit_test.test_strategies import TestStrategies
    
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestComposerFunctionality))
    suite.addTest(loader.loadTestsFromTestCase(TestStrategies))
    
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_all_tests(verbose=False):
    """Run all tests."""
    print("🚀 Running All Tests...")
    
    unit_success = run_unit_tests(verbose)
    integration_success = run_integration_tests(verbose)
    
    if unit_success and integration_success:
        print("\n✅ All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False


def run_specific_test(test_name, verbose=False):
    """Run a specific test by name."""
    print(f"🎯 Running specific test: {test_name}")
    
    # Try to run the test
    try:
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_name)
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ Error running test {test_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run trading strategies tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--fast', action='store_true', help='Run fast unit tests only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test', type=str, help='Run specific test (e.g., tests.unit_test.test_composer)')
    
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(project_root)
    
    success = True
    
    if args.test:
        success = run_specific_test(args.test, args.verbose)
    elif args.unit:
        success = run_unit_tests(args.verbose)
    elif args.integration:
        success = run_integration_tests(args.verbose)
    elif args.fast:
        success = run_fast_tests(args.verbose)
    elif args.all:
        success = run_all_tests(args.verbose)
    else:
        # Default: run all tests
        success = run_all_tests(args.verbose)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 