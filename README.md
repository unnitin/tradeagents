# **AstraQuant** 
Modular AI-Augmented Strategy Engine for Algo Trading

---

### 📌 Objective

To build a flexible, intelligent algorithmic trading engine that:

* Combines technical and LLM-based strategies
* Enables dynamic strategy composition via config or AI/agent input
* Supports clean modularity for data, features, signals, and execution
* Connects to stable broker back-ends, executes trades and has safety rails built in

---

### 🎯 Goals

| Goal                                  | Description                                                                 |
| ------------------------------------- | --------------------------------------------------------------------------- |
| 🧠 Intelligent Strategy Orchestration | Combine multiple strategies using logic, config, or AI-generated conditions |
| ⚙️ Strategy Modularity                | Each strategy encapsulated, reusable, and independently testable            |
| 🔍 Feature-Rich Data Layer            | Clean OHLCV + technical indicators + sentiment features                     |
| 📊 Backtest Support                   | Evaluate strategy combinations historically with performance metrics        |
| 🧪 LLM/NLP Integration                | Real-time or historical sentiment processing via FinBERT or GPT             |
| 🔄 Safety GuardRails             | Configurable guardrails to protect capital during turbulent markets      |
| 🔄 Runtime Configurability            | Use YAML or command-line flags to toggle weights, strategies, signals and easily change strategies with version control      |

---

### 🧱 System Architecture (Modules)

| Module                      | Responsibilities                                                            |
| --------------------------- | --------------------------------------------------------------------------- |
| `data/`                     | Data ingestion, resampling, feature generation (SMA, RSI, MACD, etc.)       |
| `strategies/`               | Self-contained signal generation logic (e.g., RSIReversion, MACDCross)      |
| `composer/`               | Combines strategies using weights, logic, or LLM-generated rules            |
| `utils/` | (Example) Score financial sentiment using FinBERT or LLM APIs                         |
| `backtest/`                 | (Planned) Simulate performance of strategy combinations                     |
| `execute/`                 | (Planned) Launch strategies in live markets                     |
| `monitor/`                 | (Planned) Measure effectiveness of strategies in live markets                     |
| `config.yaml`               | (Planned) Store tunable strategy combinations and thresholds                |
| `main.py`                   | Entry point; coordinates data pull, signal gen, logging, pipeline execution |

---

### 💡 Example Use Cases

* 💬 Use real-time news headlines to trigger RSI + Sentiment combos
* 📈 Use LLM to determine which strategies are active based on VIX or FOMC tone
* 🧪 Backtest Bollinger + MACD + sentiment over 6 months with volatility filters

---

### 🧪 MVP Scope

✅ Include in MVP:

* OHLCV + features (RSI, SMA, MACD, BB, ATR)
* Modular strategy classes
* LLM-based sentiment scoring (`FinBERT` etc.)
* Strategy composer with `weighted_sum` and `majority_vote`
* Back testing strategies on historical data with performance measurement 


❌ Exclude for now:

* Broker integration (Alpaca, InteractiveBrokers)
* Execution engine
* Web dashboard / dashboard of anytype
* Runtime logging
* Live alerting/Slack integration

---

### 🔐 Non-Goals

* No deployment as a service initially
* No machine learning model training (beyond inference)

---

### 🚀 Success Criteria

* [ ] Can run backtest with 3+ strategies via combined signal logic
* [ ] Signal accuracy and behavior matches each strategy’s expected pattern
* [ ] Sentiment-based strategy generates reasonable directional signals
* [ ] Runtime config allows switching weights and activations
* [ ] Logs performance and exceptions during data + strategy runs

---

### 🏗️ Code Quality Roadmap

Based on analysis of best practices from Google, Meta, Netflix, Airbnb, and other major tech companies, here are the planned improvements to enhance code quality, maintainability, and scalability:

#### **Phase 1: Foundation (High Impact, Low Effort)**

| Improvement | Description | Status |
|-------------|-------------|---------|
| 📦 **Modern Packaging** | Add `pyproject.toml` for Python packaging standards | 🔄 Planned |
| 🎨 **Code Formatting** | Implement `black` + `ruff` for consistent formatting | 🔄 Planned |
| 🏷️ **Type Hints** | Add comprehensive type annotations throughout | 🔄 Planned |
| 📝 **Structured Logging** | Replace print statements with structured logging | 🔄 Planned |

#### **Phase 2: Quality & Testing (Medium Impact, Medium Effort)**

| Improvement | Description | Status |
|-------------|-------------|---------|
| 🧪 **Enhanced Testing** | Migrate to `pytest` with coverage reporting | 🔄 Planned |
| ⚙️ **Configuration Management** | YAML-based config system for all parameters | 🔄 Planned |
| 🚨 **Error Handling** | Comprehensive exception handling with retries | 🔄 Planned |
| 🔄 **CI/CD Pipeline** | GitHub Actions for automated testing & quality checks | 🔄 Planned |

#### **Phase 3: Performance & Security (High Impact, High Effort)**

| Improvement | Description | Status |
|-------------|-------------|---------|
| ⚡ **Caching Layer** | Implement caching for expensive operations | 🔄 Planned |
| 🔒 **Security Hardening** | Secrets management, input validation, security scanning | 🔄 Planned |
| 📊 **Performance Monitoring** | Memory profiling and performance benchmarks | 🔄 Planned |
| 🔍 **Data Validation** | Schema validation for all external data inputs | 🔄 Planned |

#### **Architecture Improvements**

**Current Architecture:**
```
strategies/ → base.py (simple ABC)
utils/ → basic sentiment engine
tests/ → unittest-based
```

**Target Architecture:**
```
strategies/
├── base.py → Enhanced with validation, logging, config
├── factory.py → Strategy factory pattern
└── validators.py → Input validation schemas

config/
├── settings.py → Centralized configuration
├── environments/ → Environment-specific configs
└── schemas.py → Pydantic validation models

utils/
├── logging.py → Structured logging setup
├── caching.py → Performance caching layer
├── exceptions.py → Custom exception hierarchy
└── monitoring.py → Performance monitoring

tests/
├── unit/ → Pytest-based unit tests
├── integration/ → End-to-end testing
├── benchmarks/ → Performance tests
└── fixtures/ → Reusable test data
```

#### **Code Quality Standards**

Following industry best practices from major tech companies:

- **Line Length**: 120 characters (modern standard)
- **Type Coverage**: 100% type hints on public APIs
- **Test Coverage**: Minimum 90% code coverage
- **Documentation**: Google-style docstrings for all public functions
- **Error Handling**: No silent failures, comprehensive logging
- **Performance**: Sub-100ms latency for strategy signal generation
- **Security**: All external inputs validated, secrets managed securely

#### **Developer Experience Improvements**

| Tool | Purpose | Implementation |
|------|---------|---------------|
| 🔧 **Pre-commit Hooks** | Automated formatting & linting | `black`, `ruff`, `mypy` |
| 📦 **Dependency Management** | Modern dependency handling | `uv` or `poetry` |
| 🔍 **Static Analysis** | Type checking & code quality | `mypy`, `bandit` |
| 📊 **Coverage Reporting** | Test coverage visualization | `coverage.py` + HTML reports |
| 🚀 **Hot Reloading** | Development productivity | `watchdog` for file changes |

---

### 🏛️ Politician Trade Tracking

**Easy ways to track live politician stock trades in 2025**

#### 🚀 Quick Start (5 Minutes)

**Want to start RIGHT NOW?**

1. Open Twitter/X on your phone 📱
2. Search for `@PelosiTracker` 🔍
3. Follow the account and hit the bell icon 🔔
4. Done! You'll get alerts when politicians trade 🚨

#### 📊 All Options Ranked

##### 🥇 **Twitter/X Accounts** (EASIEST & FREE)

**Popular Accounts:**
- **@PelosiTracker** - 1M+ followers, most popular
- **@CongressTrading** - Multi-politician coverage
- **@CapitolTrades_** - Professional data posts
- **@QuiverQuant** - Data-driven insights

**✅ Pros:** 
- Completely FREE
- Real-time mobile alerts
- No setup required
- Community discussion

**⚠️ Cons:**
- Manual monitoring
- Still subject to 45-day filing delays
- Depends on accounts posting

##### 🥈 **Paid API Services**

**Quiver Quantitative** ⭐⭐⭐⭐⭐
- **Cost:** $10-20/month
- **URL:** https://api.quiverquant.com/
- **Best for:** Automated trading systems
- **Data:** Live House & Senate with API access

**TradeInsight.info**
- **Cost:** ~$20/month
- **URL:** https://pelositrade.com/
- **Best for:** Email notifications
- **Features:** Alerts 240+ politicians + 10K+ insiders

**Capitol Trades**
- **Cost:** $15-30/month
- **URL:** https://www.capitoltrades.com/
- **Best for:** Research and analysis
- **Data:** Comprehensive database

##### 🥉 **Hybrid Approach** (RECOMMENDED)

Combine multiple sources:
- 📱 Twitter for instant alerts (FREE)
- 💻 Quiver API for automation ($10/month)
- 📧 TradeInsight for email alerts ($20/month)

#### 🛠️ Implementation

##### Twitter Setup
1. **Follow Key Accounts:** @PelosiTracker, @CongressTrading, @CapitolTrades_, @QuiverQuant
2. **Enable Notifications:** Click bell icon → "All Tweets"
3. **Create Twitter List:** "Politician Trades" with all accounts
4. **Mobile Setup:** Enable push notifications for instant alerts

##### API Integration
```python
# Example: Using live politician tracker
from data.politician_trades_live import LivePoliticianTracker

# Initialize with API key
tracker = LivePoliticianTracker(quiver_api_key='your_key_here')

# Get recent trades
live_trades = tracker.get_all_recent_trades(days_back=7)
pelosi_trades = tracker.get_politician_recent_activity('Pelosi')
trending = tracker.get_trending_stocks_live()

# Set up alerts
alerts = tracker.create_live_alerts(['Pelosi', 'AOC', 'Cruz'])
```

##### Twitter Integration
```python
# Example: Monitor Twitter for trades
from data.twitter_politician_tracker import TwitterPoliticianTracker

tracker = TwitterPoliticianTracker()
trades = tracker.get_sample_trades()
alerts = tracker.create_twitter_alerts()
```

#### 🎯 Recommendations by Use Case

- **Casual Tracking (FREE):** Follow @PelosiTracker on Twitter + notifications
- **Active Trading ($10-30/month):** Twitter alerts + Quiver API + TradeInsight email
- **Automated Systems ($10-50/month):** Quiver API + Capitol Trades + Twitter sentiment

#### ⚠️ Important Notes

**Filing Delays:** Politicians have 45 days to report trades. Twitter accounts post when filings are made public.

**Legal Considerations:** All data comes from required SEC filings. Following trades is legal. Do your own research.

**Performance Disclaimers:** Past performance doesn't guarantee future results. Politicians may have access to non-public info.

#### 🚀 Getting Started Files

```bash
# Virtual environment setup
source venv/bin/activate

# Demo all options
python examples/easy_politician_tracking.py

# Test Twitter tracker
python data/twitter_politician_tracker.py

# Test live API tracker
python data/politician_trades_live.py
```

---

Running trades using AI, GenAI

algo-trading/        
|- data/        
│   └── fetch_data.py         # Get and preprocess market data        
│        
|- strategies/        
│   └── mean_reversion.py     # Example strategy implementation        
│        
|- backtest/        
│   └── backtest_engine.py    # Simulate trading        
│        
|- execution/        
│   └── broker_api.py         # Connect/send orders        
│        
|- risk/        
│   └── risk_manager.py       # Enforce risk rules        
│        
|- config/        
│   └── settings.yaml         # API keys, parameters, config              
│                        
|- main.py                   # Entry point for trading bot        
|- utils.py                  # Common helper functions
