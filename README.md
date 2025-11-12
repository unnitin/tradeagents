README.md
AstraQuant – AI-Augmented Trading Strategy Engine
AstraQuant is a modular algorithmic trading platform powered by AI agents. It enables you to generate, backtest, and deploy trading strategies that combine technical indicators, news sentiment, and even unconventional data like politicians’ stock trades. The system is designed to allow both human traders and AI agents to collaborate on building profitable strategies within a controlled, risk-managed framework.
<div align="center">


</div>
📈 What is AstraQuant?
AstraQuant is an “Investment Research Agent” that automates the process of developing a trading strategy:
It scans market data (prices, technical indicators) and reads news/sentiment to identify opportunities.
It incorporates unique data like public stock trades of lawmakers (so you can, for example, mirror what the most successful Congress members are doing in the market).
It uses AI agents (LLMs) to analyze textual data (news headlines, social media) and quantify sentiment (bullish vs bearish) in real-time.
It provides a strategy composer to combine multiple strategies or signals together, allowing creative hybrid strategies (e.g. “Trade when both RSI and political sentiment are bullish”).
It includes a backtesting engine to evaluate strategies on historical data with detailed performance metrics (Sharpe, drawdowns, etc.), so you can validate ideas before risking money.
In the future, it will connect to a live trading environment (paper or real trading) and monitor performance while adjusting strategies as needed.
Why combine AI with trading? Traditional algos rely on fixed formulas and can miss the big picture (e.g. a sudden news event). By contrast, AI (especially LLM-based agents) can interpret unstructured information such as news articles or social media buzz
arxiv.org
, which together with technical analysis creates a more adaptive trading system. Recent studies highlight that multi-agent AI frameworks, where different agents specialize in sentiment, technicals, etc., can outperform standard models
arxiv.org
 – AstraQuant is built on this principle.
🧰 Features & Modules
AstraQuant is organized into modular components, each focused on a part of the trading process:
Data Ingestion (data/): Fetches historical price data and live market info. Out-of-the-box it uses:
Yahoo Finance for price history (stocks and crypto)
GitHub
.
Quiver Quantitative for U.S. Congress trading disclosures (what stocks politicians are buying/selling)
GitHub
GitHub
.
(Plus hooks for news feeds or social media data – you can plug in a news API or use sample data provided.)
Adds technical indicators like SMA, RSI, MACD, Bollinger Bands, etc., to the data for strategy use.
Strategy Agents (strategies/): Self-contained strategy logic units. A few highlights:
Technical Strategies – e.g. SMACrossover, RSIReversion, BollingerBounce. These look at price patterns and indicators to generate buy/sell signals.
Sentiment Strategy – SentimentLLMStrategy uses an NLP model (FinBERT) to label news headlines as bullish or bearish, turning news into trade signals
GitHub
.
Insider/Politician Strategies – e.g. PoliticianFollowingStrategy mimics trades reported by politicians (buys when, say, a senator buys)
GitHub
; PelosiTrackingStrategy specifically follows one highly-watched trader (Nancy Pelosi); CongressMomentumStrategy spots when many politicians all trade the same way on a stock (a momentum signal).
All strategies share a common interface and can be configured with filters (e.g. only trade certain symbols or avoid penny stocks).
Strategy Composer (composer/): Combines multiple strategies into an ensemble:
Supports majority vote, weighted average, or unanimous decision methods
GitHub
GitHub
. For example, you can require that two out of three strategies agree before acting (majority vote), or weight one strategy’s signal higher than others.
Strategies and their combinations can be defined via a YAML config (no coding needed to adjust which strategies are active)
GitHub
GitHub
.
This is like your portfolio manager AI – it orchestrates the specialized agents.
Backtest Engine (backtest/): A high-fidelity simulator to test strategies on historical data:
Handles executing trades from signals with realistic constraints (position sizing, transaction costs, slippage).
Provides comprehensive metrics output: total and annual returns, volatility, Sharpe ratio, Sortino, max drawdown, VaR, win rate, and more
GitHub
GitHub
.
You can benchmark against an index (e.g. SPY for S&P 500) to see if you’re beating the market.
Supports filtering and risk settings during tests (e.g. apply a liquidity filter so it only trades stocks that had high volume historically, or set a max drawdown cut-off).
User Configuration (config/): Customize strategies, ensembles, and risk parameters easily:
Strategy config – enable/disable certain strategies, adjust parameters (like RSI threshold or which politicians to follow) through YAML.
Risk profiles – preset configurations (e.g. “conservative” might use tighter stop-loss and smaller position sizes than “aggressive”). See config/backtest.yaml for examples of different risk scenario settings
GitHub
.
API keys & environment – use .env or environment variables for sensitive keys (see Setup below).
Live Trading Integration (Planned): While the current focus is research and backtesting, the architecture is ready for live deployment:
A module execute/ (to be implemented) will connect to broker APIs (or crypto exchanges) to execute real trades based on the agent’s signals.
A monitor/ module is planned to track live performance and perhaps trigger agent adjustments if things go off track.
Mobile and Web frontends will interface via an API to get strategy suggestions and performance data in real-time.
🚀 Getting Started
1. Installation
First, clone the repository and install the required packages. We recommend using a Python virtual environment.
git clone https://github.com/unnitin/trade.git
cd trade
python3 -m venv venv && source venv/bin/activate   # create and activate virtual env
pip install -r requirements.txt
This will install all necessary Python libraries (pandas, numpy, PyYAML, requests, transformers, etc.). Note: The transformers library will be installed for NLP – by default it will try to use PyTorch. If you don’t have PyTorch, install it first (e.g. pip install torch for CPU-only version).
2. Configuration
API Keys: If you want to fetch live data for politicians’ trades or use certain data providers, set the following environment variables (for example in a .env file or your shell profile):
QUIVER_API_KEY – API key for Quiver Quantitative. Needed for live Congress trading data. (You can request a free key on their website.)
CAPITOL_TRADES_API_KEY – API key for CapitolTrades (alternative source, not mandatory).
ALPHA_VANTAGE_API_KEY – If you want to use Alpha Vantage for stock or crypto data (optional).
FINNHUB_API_KEY – If you want to use Finnhub for news or alternative data (optional).
The system will automatically pick up these keys. If a key is missing, related features will either use fallback data or return empty results with a warning (for example, missing Quiver API key means PoliticianFollowingStrategy will produce no signals and log a warning).
Config Files: Check the config/ directory:
strategies.yaml – define strategy ensembles and their parameters. You can edit this to try different strategy combinations.
backtest.yaml – define backtest settings like initial capital, commission rate, and risk parameters for different scenarios (default, conservative, aggressive).
filter_config.yaml (if present) – define any global filters to apply.
No code changes are needed to adjust basic settings – just edit the YAML and rerun the agents.
3. Usage Examples
We provide example scripts in the examples/ folder to demonstrate typical workflows.
Example 1: Backtest a Single Strategy
Let's say you want to test a simple RSI reversion strategy on Apple (AAPL):
from data.fetch_data import DataFetcher
from strategies import RSIReversion
from backtest.engine import BacktestEngine

# Fetch historical data for AAPL
df = DataFetcher().get_stock_data("AAPL", start="2022-01-01", end="2022-12-31")
df = df.set_index("date")  # use date as index for convenience

# Add technical features (if needed, RSIReversion might compute internally too)
# ... (e.g., compute RSI indicator if not done in strategy)

# Initialize strategy and backtest engine
strategy = RSIReversion(low_thresh=30, high_thresh=70)
engine = BacktestEngine(initial_capital=100_000)

# Run backtest
result = engine.run_backtest(strategy=strategy, data=df, symbol="AAPL")
print("Total Return:", f"{result.metrics.total_return*100:.2f}%")
print("Sharpe Ratio:", f"{result.metrics.sharpe_ratio:.2f}")
This will output performance metrics for that strategy in 2022. You can dig into result.trades for individual trades, etc.
Example 2: Combined Strategy with Voting
Combine a Moving Average Crossover and a Sentiment strategy on multiple stocks:
from composer import StrategyComposer
from backtest.engine import BacktestEngine

# Create a composer and add strategies
composer = StrategyComposer()
composer.add_strategy(SMACrossover(fast=20, slow=50), weight=0.5, name="sma_cross")
composer.add_strategy(SentimentLLMStrategy(sentiment_threshold=0.2), weight=0.5, name="news_sentiment")

# Fetch data for a few symbols
symbols = ["AAPL", "GOOGL", "MSFT"]
fetcher = DataFetcher()
market_data = {sym: fetcher.get_stock_data(sym, start="2023-01-01", end="2023-06-30") for sym in symbols}

# Backtest the combined strategy
engine = BacktestEngine(initial_capital=100_000)
combo_result = engine.run_composer_backtest(
    composer=composer, 
    data_dict=market_data, 
    combination_method="majority_vote"   # could also be 'weighted_average'
)

print("Combined Strategy Performance:")
for metric, value in combo_result.metrics.to_dict().items():
    print(f"{metric}: {value}")
This will simulate trading those three stocks whenever both strategies (or the majority, in this case 2 out of 2) agree on a signal. You’ll get an aggregated performance for the portfolio containing AAPL, GOOGL, MSFT.
Example 3: Using Politician Trade Signals
from strategies import PoliticianFollowingStrategy
from backtest.engine import BacktestEngine

# Strategy that follows trades of all politicians over last 30 days
politics_strat = PoliticianFollowingStrategy(days_back=30)

# Fetch data for a specific stock, e.g., NVDA (Nvidia)
df_nvda = DataFetcher().get_stock_data("NVDA", start="2023-01-01", end="2023-09-30")
df_nvda = df_nvda.set_index("date")

# Backtest the strategy on NVDA
engine = BacktestEngine(initial_capital=100_000)
result = engine.run_backtest(strategy=politics_strat, data=df_nvda, symbol="NVDA")

# The strategy will generate buy signals if any politician bought NVDA in the last 30 days (per the data),
# and sell signals if they sold.
print(f"NVDA - Politician-following strategy return: {result.metrics.total_return*100:.2f}%")
(Keep in mind you need the API key for this to fetch actual trades; otherwise, if no data is fetched, the strategy will do nothing and result in 0% return.) This is a simplistic example of “if you can’t beat them, join them” – tracking insider-style trades.
For more extensive examples, see the Jupyter notebooks or scripts in examples/:
complete_workflow_example.py – runs through an entire process: data fetch, adding indicators, running multiple strategies, combining them, and analyzing results.
strategy_composer_example.py – shows how to configure and run the strategy composer with config files.
advanced_filter_example.py – demonstrates using filters (e.g., only allow trades when volume > 1,000,000).
4. Interpreting Results
After a backtest, you’ll typically get a PerformanceMetrics summary. Key fields:
total_return – Total profit/loss as a fraction (0.25 = +25%).
sharpe_ratio – Risk-adjusted return (above 1.0 is decent; higher is better).
max_drawdown – Worst peak-to-valley loss during the period (as a negative fraction).
win_rate – Percentage of trades that were profitable.
beta – Correlation to the benchmark (e.g. if ~1, strategy moves with market; if 0, uncorrelated).
alpha – Excess return over what beta would predict, i.e., skill-based return.
etc.
Use these to gauge if a strategy is worth pursuing. A good strategy might have a modest but positive total_return with low drawdown and Sharpe above 1. Strategies that only work in hindsight or overfit may show great returns but likely will have unstable performance out-of-sample (be cautious!).
⚙️ Project Status and Roadmap
Current Status: The core framework is in place:
Core data ingestion, technical indicators, and backtest engine ✅
Several example strategies implemented (momentum, mean-reversion, sentiment, insider following) ✅
Configuration-driven strategy composition ✅
Basic sentiment analysis via FinBERT ✅
Extensive test coverage (>95 tests) for reliability ✅
In Progress / Next Up:
Safety Guardrails: Implementing more robust risk management (automated stop-loss logic, circuit breakers if too many losing trades) ⚙️ in progress.
Real-time Capabilities: Transitioning from pure backtesting to also allow paper trading mode where the system can pull the latest market data periodically and simulate strategy in near-real-time.
Front-end Integration: Developing a REST API so that a web or mobile interface can send a user’s strategy preferences to the backend and receive strategy suggestions or backtest results. (This is planned; currently, interaction is via code or console.)
UI/UX: Designing the web dashboard and iPhone app to view strategy analytics, enter preferences, and eventually approve live trades.
Additional AI: Exploring using GPT-4 (or similar) for generating human-readable explanations of strategy moves, or for parsing longer text (like Federal Reserve meeting minutes sentiment, etc.).
Long-term Ideas:
A marketplace of strategies where users can share AI-generated strategies and track their performance.
Deploying the agent on cloud infrastructure for continuous learning (e.g. retrain the sentiment model with latest data, or let the agents “compete” in a simulated environment to improve).
Expand to other data: earnings call transcripts (LLM reads them), alternative data like satellite imagery (for advanced users), etc., to truly create a holistic AI trader.
🛠 Development & Contribution
This project is set up to be contributor-friendly, including contributions by AI coding assistants. Key notes for developers:
Ensure you have Python 3.9+ and see Installation above for environment setup.
Run make test (or the equivalent commands) to ensure all tests pass after your changes.
We use Black for formatting and flake8 for linting. You can run make lint and make format to auto-fix style issues before committing.
When adding new strategies or features, include unit tests for them under tests/. If adding a new dependency, update requirements.txt.
Pull Requests: Please include a clear description of the change and any relevant issue/tag. We have a CI pipeline that will run tests and code quality checks on PRs
GitHub
GitHub
.
For significant changes, it’s a good idea to open an issue or discussion first to align on design (or check if it’s in the roadmap).
Using Cursor with AI (Codex): If you are leveraging AI to assist coding:
We have a spec.md (this document) that outlines the intended behavior – feed it to the AI to give it context.
Develop incrementally: e.g., “Implement a class that does X as per spec.md section Y” – many parts are decoupled so you can work on them one by one.
Always validate AI-generated code against tests and sanity-check logical correctness, especially for financial calculations.
✅ License & Disclaimer
This project is open-source under the MIT License – see LICENSE file for details.
Disclaimer: AstraQuant is for educational and research purposes. It is not financial advice and comes with no guarantee of performance. Always use caution when deploying trading algorithms. Past performance (especially backtest results) is not indicative of future results. If you do decide to hook this up to a live brokerage, use small amounts and observe thoroughly.