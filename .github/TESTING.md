# Testing Guide

This document describes how to run tests locally and what our CI/CD pipeline does.

## Quick Start

### Run All Tests Locally
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m unittest discover tests/ -v
```

### Run Specific Test Categories
```bash
# Run only unit tests
python -m unittest discover tests/unit_test/ -v

# Run only integration tests
python -m unittest discover tests/integration/ -v

# Run specific test files
python -m unittest tests.unit_test.test_composer -v
python -m unittest tests.unit_test.test_strategies -v
python -m unittest tests.unit_test.test_data -v
python -m unittest tests.integration.test_integration -v

# Run a specific test
python -m unittest tests.unit_test.test_composer.TestComposerFunctionality.test_strategy_registration -v
```

### Using the Test Runner Script
```bash
# Run all tests with the custom runner
python tests/run_tests.py --all

# Run only unit tests
python tests/run_tests.py --unit

# Run only integration tests
python tests/run_tests.py --integration

# Run fast tests (no external data dependencies)
python tests/run_tests.py --fast

# Run with verbose output
python tests/run_tests.py --unit --verbose

# Run specific test
python tests/run_tests.py --test tests.unit_test.test_composer
```

## Test Structure

```
tests/
├── __init__.py           # Main test package
├── run_tests.py          # Custom test runner script
├── unit_test/            # Unit tests for individual components
│   ├── __init__.py
│   ├── test_composer.py  # Strategy composer functionality
│   ├── test_data.py      # Data fetching and processing
│   └── test_strategies.py # Individual strategy implementations
└── integration/          # Integration tests for full system
    ├── __init__.py
    └── test_integration.py # End-to-end system tests
```

### Test Categories

#### 1. Composer Tests (`test_composer.py`)
- Strategy registration and initialization
- Signal combination methods (majority vote, weighted, unanimous)
- Configuration loading and validation
- Error handling for invalid inputs
- Convenience function testing

#### 2. Data Tests (`test_data.py`) 
- Yahoo Finance data fetching with dynamic dates
- Technical indicator calculations (SMA, EMA, RSI, MACD, etc.)
- Data preprocessing and resampling
- Edge case handling (NaN data, insufficient data)

#### 3. Strategy Tests (`test_strategies.py`)
- Signal format validation (returns -1, 0, 1)
- Strategy logic correctness 
- Edge case handling
- Performance with different data conditions

## CI/CD Pipeline

Our automated testing pipeline runs on every pull request and push to main:

### 1. **Quick Tests** (on development branches)
- Runs on every push to feature branches
- Fast syntax and import checks
- Core test suite execution
- Python 3.10 only for speed

### 2. **Full CI/CD Pipeline** (on main/PR)
- **Multi-Python Testing**: Tests on Python 3.9, 3.10, 3.11
- **Code Quality**: Black formatting, isort imports, pylint analysis
- **Security**: Safety vulnerability checks, Bandit security linting
- **Integration Tests**: Full composer functionality testing
- **Deployment Ready**: Creates deployment artifacts

## Writing New Tests

### Test File Naming
- Test files must start with `test_`
- Test methods must start with `test_`
- Use descriptive names: `test_strategy_generates_correct_signals`

### Strategy Test Template
```python
def test_new_strategy_format(self):
    """Test that NewStrategy returns proper signal format."""
    strategy = NewStrategy(param1=value1)
    signals = strategy.generate_signals(self.df)
    
    # Test return type
    self.assertIsInstance(signals, pd.Series)
    
    # Test signal values
    unique_signals = set(signals.dropna().unique())
    self.assertTrue(unique_signals.issubset({-1, 0, 1}))
    
    # Test length
    self.assertEqual(len(signals), len(self.df))
```

### Composer Test Template
```python
def test_new_combination_method(self):
    """Test new combination method works correctly."""
    composer = create_composer()
    
    # Test method exists
    self.assertTrue(hasattr(composer, 'new_method'))
    
    # Test with sample data
    signals = composer.execute_combination('test_combo', self.df)
    self.assertIsInstance(signals, pd.Series)
```

## Local Development Workflow

### 1. Before Making Changes
```bash
# Run tests to ensure starting point is clean
python -m unittest discover tests/ -v
```

### 2. During Development
```bash
# Run specific tests frequently
python -m unittest tests.test_strategies.TestStrategiesBasic.test_new_strategy_format -v

# Quick syntax check
python -m py_compile strategies/new_strategy.py
```

### 3. Before Committing
```bash
# Run full test suite
python -m unittest discover tests/ -v

# Check imports work
python -c "from strategies import NewStrategy; print('✅ Import successful')"

# Test composer integration
python -c "from composer import create_composer; c = create_composer(); print('✅ Composer integration works')"
```

## Test Data Management

### Dynamic Date Testing
Our tests use dynamic dates to avoid Yahoo Finance data availability issues:

```python
from datetime import datetime, timedelta

# Always use recent dates
end_date = datetime.now()
start_date = end_date - timedelta(days=10)
df = get_data("AAPL", start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
```

### Sample Data Creation
For strategy tests, create predictable sample data:

```python
def setUp(self):
    # Create controlled test data
    self.df = pd.DataFrame({
        'close': [10, 11, 12, 13, 14],  # Predictable values
        'sma_20': [10, 10.5, 11, 11.5, 12],
        'volume': [1000, 1100, 1200, 1300, 1400]
    })
```

## Debugging Failed Tests

### Common Issues

1. **Import Errors**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"
   
   # Test imports manually
   python -c "from strategies import SMACrossover"
   ```

2. **Data Availability**
   ```bash
   # Test Yahoo Finance directly
   python -c "from data import get_data; print(get_data('AAPL', period='5d').head())"
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --force-reinstall
   ```

## Performance Testing

For performance-sensitive code:

```python
import time

def test_strategy_performance(self):
    """Test strategy executes within reasonable time."""
    large_df = create_large_dataset(10000)  # 10k rows
    
    start_time = time.time()
    signals = strategy.generate_signals(large_df)
    execution_time = time.time() - start_time
    
    self.assertLess(execution_time, 1.0)  # Should complete in under 1 second
```

## CI/CD Trigger Conditions

- **Quick Tests**: Every push to feature branches
- **Full Pipeline**: Pull requests to main, pushes to main
- **Integration Tests**: Only on pull requests
- **Deployment**: Only when merging to main with all tests passing

## Troubleshooting CI/CD

If CI/CD fails:

1. **Check the Actions tab** in your GitHub repository
2. **Look at the specific failed step** in the workflow
3. **Reproduce locally** using the same commands
4. **Check for environment differences** (Python version, dependencies)

Example local reproduction:
```bash
# Reproduce the exact CI environment
python3.10 -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
python -m unittest discover tests/ -v
``` 