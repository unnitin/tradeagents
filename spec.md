# AI-Driven Investment Strategy Agent – Technical Specification

---

## Overview & Objectives
This specification outlines a system for agentified algorithmic investing, where AI agents autonomously
generate, evaluate, and refine trading strategies using a combination of real-time data and user inputs. The
goal is to enable autonomous investment agents that can leverage emerging news, price trends, and
user preferences to propose strategies, backtest them, and adapt to market conditions. Ultimately, this will
power a web and iPhone app where users can contribute strategy ideas, review AI-generated strategies,
see backtest results, and monitor a live portfolio's performance.

## Key Objectives
1. **Multi-Source Data Integration:** Ingest market data (stock & crypto prices), news/sentiment, and
unconventional data (e.g. politicians’ stock trades) into a unified platform .
2. **AI-Driven Insights:** Utilize LLMs and analytics to interpret news and social sentiment (e.g. classify
headlines as bullish/bearish) and detect patterns beyond standard technical analysis .
3. **Autonomous Strategy Generation:** Employ specialized AI agents (roles) – e.g. a news analyst,
technical analyst, sentiment analyst, and a portfolio trader – to collaborate on strategy formulation. These agents mimic a real trading team: analyzing fundamentals, sentiment, technical indicators, and debating bullish vs bearish theses.
4. **Robust Backtesting & Evaluation:** Provide a backtesting engine to validate strategies against
historical data with detailed performance metrics (returns, Sharpe, drawdowns, etc.).
5. **User Preference Customization:** Incorporate user constraints (risk tolerance, asset preferences)
from a questionnaire into strategy selection and risk management.
6. **Safety & Risk Management:** Include guardrails (position limits, stop-loss thresholds, etc.) to protect
capital during volatile markets.
7. **Seamless UX Integration:** Design the system for easy integration with a web frontend and native
iOS app, enabling users to interact with the AI agents (input ideas, tweak strategies) and visualize
results in an intuitive interface.

## Scope & Constraints
1. **Asset Universe:** Focus on publicly listed equities and top 10 cryptocurrencies by market cap.
Exotic assets, derivatives, or low-liquidity tokens are out of scope to keep data reliable (per user
guidance to stay within mainstream stocks & top-10 crypto).
2. **Market Data Frequency:** Emphasize daily and hourly price data initially (1-day and 1-hour
intervals), with ability to extend to intraday (minute-level) if needed. This balances actionable
insight with simpler data handling for MVP.
3. **Geographical Scope:** Primarily U.S. markets (for stocks and political data) and major crypto
exchanges. International equities could be added later, but initially we use readily available US-
centric data (Yahoo Finance, etc.).
4. **User Preferences:** Only basic preferences are considered initially (e.g. risk level, sectors to avoid,
interest in crypto yes/no). Complex personalization (like tax implications or very detailed goals) is out
of scope for MVP.
5. **Performance vs. Readability:** The system is optimized for clarity and extensibility over ultra-low
latency. For example, backtests can run in seconds-to-minutes on historical data, which is
acceptable.
6. **Regulatory & Ethical Use:** The agent will not execute real trades initially – it will suggest and
simulate. Live trading integration is a future goal once the strategy logic is well-vetted.

## Key System Components
### Data Layer
1. **DataFetcher Module:** Centralized component to fetch all required data. It pulls stock price data (and crypto prices) via reliable APIs (using Yahoo Finance’s unofficial API for direct OHLCV data), and also retrieves alternative data:     
    - **Politician Trades:** Fetches recent stock trades by U.S. Congress members from Quiver Quantitative’s
API (House & Senate disclosures). This data is frequently discussed in the trading community as a signal, since a 2024 study found 20+ Congress members beat the market by a wide margin . The public can track these disclosures (via STOCK Act) through sites like Quiver Quant and others       
    - **Social/News Sentiment:** Provides hooks to ingest news headlines or Twitter data. Initially, we
simulate this or use a placeholder (e.g. sample tweets of notable trades) to demonstrate the pipeline
    - **Real-time news APIs** (or social media feeds) can be integrated later.

2. **Feature Engineering:** The data layer also computes common technical indicators on the price data
(SMA, EMA, RSI, Bollinger Bands, ATR, MACD, etc.) so that strategies can use these features .
All OHLCV data is standardized and enriched with these columns.

3. **Data Scope:** Initially, we will use end-of-day pricing for equities and daily crypto prices (which can be fetched via Yahoo or a crypto API). The DataFetcher is built to handle multiple tickers and aggregate into a coherent dataset for the strategy layer.

4. **Data Quality & Reliability:** The system uses direct API calls to avoid third-party library issues – for
example, it directly calls Yahoo’s chart API for price history, bypassing any SSL issues and returning
clean OHLCV data for analysis. If an API (like Quiver) requires keys, those are loaded from
environment variables. In absence of an API key or on request failure, the system can fallback to using sample or mock data with a warning (ensuring the pipeline can still run).

Development Note: For ease of getting started (user’s preference), we stick with straightforward solutions:
- Use requests to call REST endpoints (Yahoo Finance, Quiver) instead of introducing heavy SDKs. For
example, Yahoo data is fetched by constructing a URL with proper query parameters for dates and interval
- We recommend obtaining a free API key for QuiverQuant (to get live Congress trading data);
otherwise, the DataFetcher will safely return an empty DataFrame or use the hardcoded sample tweets to
illustrate politician trades
- Similarly, if news API integration is added, an API key (e.g. for NewsAPI or Finnhub) would be configured via environment variables.

### AI Agents & Strategy Layer
This layer is the “brain” of the system: a collection of specialized strategy modules and AI agents that
generate trading signals. It’s inspired by real hedge-fund teams and research on multi-agent trading frameworks :
1. News/Sentiment Analyst (LLM Agent): An agent focusing on unstructured data. It uses a financial NLP model (like FinBERT) to gauge sentiment from news or social media. For example, daily news headlines can be classified as bullish, bearish, or neutral. The SentimentLLMStrategy uses this model: it turns positive headlines into bullish signals and negative news into bearish signals automatically. This agent can be extended with larger LLMs (OpenAI GPT-4, etc.) to summarize news or parse financial reports – research shows LLMs are very effective at understanding text like news articles and social sentiment .
2. Technical Analyst: A collection of technical strategy classes that generate signals from price/indicator data. Examples include:
2.1. SMACrossover: a moving average crossover strategy (buy when short-term SMA crosses above long-
term SMA, etc.).
2.2. RSIReversion: a mean-reversion strategy using RSI (e.g. buy when RSI < 30 oversold, sell when RSI >
70 overbought).
2.3. MACDCross: momentum strategy based on MACD indicator crosses.
2.4. BollingerBounce: contrarian strategy using Bollinger Bands (buy near lower band, sell near upper
band). These are modular (each extends a base Strategy class) and output signals (+1 = buy, -1 = sell, 0 = hold) for each time step based on their logic. They can incorporate filters (like only trade certain symbols or conditions) for refined control.
2.5. Unusual Data Strategies (Politician & Social Trend Analyst): Strategies that leverage politician
trading data and social trends. For instance:
2.6. PoliticianFollowingStrategy: Follows trades of specified politicians. When a politician in focus buys
a stock, the strategy issues a buy signal (often with a short delay after the disclosure). If they sell,
it issues a sell signal. This effectively mimics portfolios of insiders in Congress (sometimes jokingly called the “Pelosi tracker” since some high-profile lawmakers’ trades beat the market). The strategy can filter by specific names (or “all” by default) and looks back a configurable number of days .
2.7. PelosiTrackingStrategy: A specialized version of the above focusing only on Nancy Pelosi’s trades,
given her trades’ notoriety. It treats any Pelosi buy as a strong bullish signal and any sell as bearish, on the premise that her disclosures often precede stock moves .
2.8. CongressMomentumStrategy: Rather than single trades, this looks for momentum or consensus among many politicians. If multiple politicians all bought the same stock within a short window, that triggers a bullish signal (and likewise for multiple sells). It’s effectively checking for clusters of political trades to identify “crowded” bets.
2.9. (Future) SocialMediaBuzzStrategy: (Planned) Could track social media sentiment, e.g. Twitter/Reddit
mentions of a stock (especially from known finance accounts) to gauge hype. For now, social
sentiment is only lightly represented via the sentiment agent and sample tweets.

3. Strategy Composer (Portfolio Manager Agent): This component acts as the orchestrator, combining signals from multiple strategies/agents. The StrategyComposer can take several strategies and either merge their signals or run them in parallel on different allocations:
3.1. **Voting & Weighted Strategies:** It supports majority voting (the most common signal among the group decides the action) or weighted averaging of signals. For example, you can assign 50% weight to a technical strategy and 50% to a sentiment strategy; the combined signal might only trigger if both agree or if one’s conviction is higher.
3.2. **Ensemble Definitions:** Compositions can be defined in config (YAML) so agents can be dynamically created. For instance, a config might define a “technical_ensemble” combining SMA, RSI, MACD with given weights. The composer reads this and auto-instantiates those strategies, ready to generate combined signals.
3.3. **Agent Debate (Future):** In future iterations, the composer could implement a more agent debate system. E.g., a “bull” agent and “bear” agent present arguments based on data, and a “arbiter” agent decides the final stance. This is inspired by multi-agent research and can make the system’s decisions more explainable (each agent provides rationale).

4. **Risk Management Agent:** A planned component that will monitor and enforce risk limits. This includes:
- Notional exposure limits (e.g., don’t invest more than X% of portfolio in one stock or sector).
- Stop-loss or drawdown controls (e.g., if portfolio drops more than 5%, reduce all positions).
- Leverage control (especially if margin or crypto futures come into play later).
This agent can act by dynamically adjusting signals (for example, if a strategy says “buy” but risk agent says exposure is too high, it could downgrade that signal to 0 or a smaller position). For MVP, basic checks will be implemented (like max position size per config), while more complex actions are a later addition.  (Ref: the README notes safety guardrails as in-progress).
Note: Each strategy class follows a simple interface ( generate_signals ) and can include pre-filters. The
base Strategy class allows attaching filters that pre-select which data points or symbols the strategy is
allowed to act on 32 33
. For example, a strategy could be configured to only trade stocks with market cap
above $10B and volume above 1M (using a StockFilter ) or to avoid trading around earnings dates
(using a TimeFilter ). This mechanism ensures the agents respect user-defined constraints (like “avoid
penny stocks” or “only trade within 9:30am-4pm market hours”).
### Backtest & Analytics Layer

1. **Backtest Engine:** A core component that simulates strategy performance on historical data. Given
one or a combination of strategies and a dataset (e.g. daily prices for 2020-2023 for S&P500 stocks),
it will step through time and execute trades as signals dictate.
It handles portfolio accounting: starting from an initial capital (configurable, e.g. \$100,000), it will
create positions when buy signals occur and close or short positions on sell signals. It accounts for
position sizing (e.g. fixed fraction of capital per trade or equal allocation) and optional transaction
costs (commission, slippage models).
It supports filters during backtest: e.g., using a LiquidityFilter to ignore signals on illiquid stocks or
applying a TimeFilter to skip trades on certain dates. This ties into the risk management by not
entering trades that violate constraints.
The engine can run either single-strategy backtests or combined strategy backtests (through the
composer). In combined mode, it can simulate rebalancing across multiple strategies or treat the
combined signal as a unified strategy.
2. **Performance Metrics:** After simulation, the backtest module computes a broad set of metrics: total return, annualized return, volatility, Sharpe ratio, Sortino ratio, max drawdown (and duration), value-at-risk (95% VaR), win rate, profit factor, and more. It also can compare against a benchmark (by default S&P 500 “SPY”) to compute alpha, beta, and information ratio. These metrics give a comprehensive view of how the strategy performed.

#### Results Storage
The backtest results (including trade logs and metrics) can be saved to disk or
database. For now, a simple approach is taken: results can be saved as JSON or pickle files for
analysis. This allows the front end to load past backtest results for display.

#### Visualization (Future)
While not in the backend scope, we anticipate producing equity curves and perhaps risk visualizations (drawdown charts, etc.) which the front-end can render. The backtest engine will make it easy to extract such time series (e.g. portfolio value over time) for plotting.

### User Interface Integration
Though the UI (web app and iPhone app) is outside the Python backend scope, the design of our system
facilitates easy integration:
- The agents and backtest can be exposed via a REST API (using a framework like FastAPI or Flask). For example, an endpoint /generate_strategy could trigger the AI agent to propose a strategy based on current news, and an endpoint /backtest could run a specified strategy and return the performance. 
- Real-time Monitoring: The backend can be extended to run a live trading simulation or connect to a broker API for actual trading. In MVP, we simply simulate “live” by running backtests on recent data periodically. The front-end could fetch updated results (e.g., “last week’s performance of your AI portfolio”). 
- User Inputs: The questionnaire results (user preferences) would be fed into the system to configure the agents: - Risk tolerance -> sets things like position size limits, leverage usage (a conservative user might only allow very small positions or enforce unanimous signals). 
- Asset preferences -> can inform the filters (e.g., if user doesn’t want crypto, the crypto-related strategies can be
turned off or filtered out; if user favors tech stocks, perhaps focus data and news on that sector). 
- Strategy style preferences -> could select which agent combinations to use (some users might prefer pure technical
strategies vs. those that consider news). 
- Collaboration Mode: The user should be able to see the agent’s reasoning. In future, using an LLM to generate a textual explanation of why a strategy is recommended (e.g., “The momentum strategy is suggesting buying AAPL because multiple politicians bought it last month and technical trends are positive”) would greatly improve trust. This is aligned with making the AI’s decisions transparent and explainable. For now, we can log key events (like “XYZ strategy generated a BUY for AAPL on 2025-11-01 because RSI=28 (oversold)”). 
- Multi-platform considerations: The backend will remain the single source of truth for strategies and data. The web and iPhone apps will mainly be views and input forms. We will ensure all heavy computations (AI inference, backtesting, data fetch) occur on the server side (or a cloud function) to keep the front-ends light.

### Technical Architecture
Combining the above, the system is organized into modular packages:

- **data/** – Data ingestion and preprocessing:
  - `fetch_data.py` – contains DataFetcher class (for Yahoo Finance data, QuiverQuant politician data, etc.) .
  - `features.py` – functions to add technical indicators (SMA, RSI, MACD, etc.) .
  - `constants.py` – any static mappings (e.g., Yahoo API interval codes, model names for NLP).
  - (Possibly a news.py in future for news scraping or API integration.)
- **strategies/** – Strategy definitions (each is an agent generating signals):
  - `base.py` – defines the Strategy abstract base class and common filtering utilities .
  - `technical/` (or directly in strategies) – classes for technical strategies like SMACrossover, RSIReversion , etc.
    - `sentiment_llm.py` – contains SentimentLLMStrategy that scores news headlines via utils.sentiment_engine and produces signals.
    - `politician_following.py` – contains PoliticianFollowingStrategy, PelosiTrackingStrategy, CongressMomentumStrategy (all leveraging politician trade data) 
    - Other strategies – e.g. BollingerBounce, ATRVolatilityFilter (treating ATR as a filter strategy), etc., each encapsulated in its class.
- **utils/** – Utility code, especially for NLP:
  - `sentiment_engine.py` – sets up the HuggingFace Transformers pipeline with FinBERT and provides score_sentiment(text) to classify text as bullish/bearish/neutral. (Future utils could include a news_fetcher or integration with OpenAI API if we add more complex text analysis.)
- **filters/** – Classes for filtering data or signals, used to enforce criteria:
  - Examples: StockFilter (by price, volume, market cap thresholds), TimeFilter (exclude certain
    dates or times), LiquidityFilter (ensure sufficient trading volume, etc.), CompositeFilter (combine multiple filters with AND/OR logic).
  - These filters are applied either at strategy level or globally in backtests.
- **composer/** – Strategy composer/orchestrator:
  - `strategy_composer.py` – defines StrategyComposer class and helpers to load strategy ensembles from config. It registers strategy classes, instantiates them as needed, and provides methods to combine signals (vote, average, etc.) and to retrieve specific configured combinations. This might also house higher-level agents logic (like coordinating a debate between strategies or deciding which strategies to activate based on market regime – e.g., use different ensembles if volatility is high vs. low).
- **backtest/** – Backtesting engine and performance analysis:
  - `engine.py` – main BacktestEngine class that runs simulations given strategies, data, and
    configurations (transaction cost settings, etc.).
  - `portfolio.py` – logic for maintaining portfolio state (positions, cash balance, P&L calculations).
  - `metrics.py` – functions to calculate performance metrics, and a PerformanceMetrics data class to hold results .
  - `results.py` – utilities to save/load backtest results (could be JSON serialization of PerformanceMetrics and maybe trade history).
  - Possibly `backtest_config.py` – pre-defined settings or parameter sets (e.g., “aggressive vs conservative” mode settings for position sizing, etc.).
- **config/** – Configuration files and loaders: YAML files for strategies ( strategies.yaml might list strategy combos and their parameters) ,
  for backtest settings ( backtest.yaml for different risk profiles, e.g. default vs conservative vs aggressive) , and filter settings.
  Python helpers like filter_config.py and backtest_config.py to load these YAMLs and provide to the system.
- **tests/** – Unit and integration tests ensuring each module works correctly. (Over 90 tests are already indicated as part of the repository, ensuring reliability). 

All these components interact as follows in a typical flow: 
    1. Data Preparation: Fetch historical data for selected symbols via DataFetcher . Augment data with technical features. 
    2. Agent Signal Generation: Each enabled strategy/agent processes the data: - Technical strategies use the price & indicator data (often
for each symbol individually). 
        - Sentiment strategy uses a separate news dataset (mapped by date or by event) to produce a sentiment signal series. - Politician strategies use the politician trade feed (which includes tickers and dates) to produce signal series for relevant tickers. 
    3. Signal Composition: The StrategyComposer collects signals. If running a single strategy, that is the signal. If multiple, it combines
them per chosen method (e.g., majority vote: needs at least 2 of 3 strategies to agree to take a trade). 
    4. Backtesting: The combined signal (or individual strategy signal) is fed into BacktestEngine along with price
data. The engine simulates entering/exiting positions according to signals and yields performance metrics
at the end. 
    5. Evaluation & Loop: The results inform adjustments. For example, if the backtest shows poor performance in high volatility periods, the agents might adjust (the system can automatically test different combinations or parameters – potentially using the AI to suggest optimizations). This iterative loop can be automated as part of the agent’s learning (future extension: a reinforcement learning loop or Bayesian optimization of strategy parameters). 
    6. User Feedback: The user can review the strategy’s performance and either accept it to run live (paper trading to start) or refine preferences (which triggers the agents to possibly generate a new strategy or tweak parameters).
    
## System Layout

| Layer | Responsibilities | Key Modules | Primary Outputs |
| --- | --- | --- | --- |
| Data Ingestion | Ingest market data, crypto prices, politician trades, and sentiment/news feeds into a unified platform. | data/fetch_data.py, data/constants.py, external APIs (Yahoo Finance, Quiver Quantitative) | Normalized OHLCV datasets, alternative data frames |
| Feature Engineering & NLP | Generate technical indicators and sentiment insights referenced by strategies. | data/features.py, utils/sentiment_engine.py | Indicator-enriched price tables, FinBERT sentiment scores |
| Strategy Agents | Produce trading signals from technical, sentiment, and politician-tracking logic. | strategies/*, filters/* | Per-strategy signals, filtered symbol universes |
| Strategy Composition & Risk | Combine agent signals and enforce guardrails before execution. | composer/strategy_composer.py, risk management agent, filter_config loaders | Blended signals, position and exposure limits |
| Backtesting & Analytics | Validate strategies, compute metrics, and persist logs for review. | backtest/engine.py, backtest/portfolio.py, backtest/metrics.py, backtest/results.py | Trade logs, performance statistics, benchmark comparisons |
| Interface & Delivery | Surface agent actions and results to web/iOS clients and collect user preferences. | REST API surface (FastAPI/Flask), config/, questionnaire inputs | API responses, UI-ready summaries, user-specific strategy constraints |

### Development Plan & Tools
To implement this system, we will follow best practices and leverage modern development tools. Below are
recommendations and considerations, aligning with the user’s guidance (no strong tech stack stance,
prioritize ease of start, and open to alternatives based on research):

- **Language & Environment:** Python 3.9+ is used (consistent with current repo and CI badges ).
  Python offers rich ecosystem for data science (pandas, numpy) and machine learning (huggingface
  transformers for NLP, etc.), making it well-suited for this project.
- **AI/ML Libraries:** We use Hugging Face Transformers for FinBERT (financial sentiment model) which runs locally. This requires installing the transformers package and a deep learning backend (PyTorch). The FinBERT model is loaded via the pipeline API. We suggest using PyTorch (torch) as it’s widely used and will be installed alongside transformers (if not, explicitly include it in requirements). Alternatively, for more advanced language tasks, OpenAI’s API could be used with the openai Python SDK – but since the user is okay with alternatives and FinBERT is a strong open model, we stick to FinBERT for sentiment. In future, if we want the agent to do more complex reasoning (like reading whole news articles or debates), we might integrate LangChain or similar frameworks to manage prompts, or fine-tune an open LLM for finance. For now, this complexity is beyond MVP (the approach is to keep it simple and “whatever is easiest to get started with”).
- **Data APIs:** We deliberately avoid heavy dependencies for data. The custom DataFetcher covers our needs with requests . We note that libraries like yfinance (Yahoo Finance API wrapper) or official SDKs (AlphaVantage’s alpha_vantage library, Finnhub’s client) could simplify some data access. The user allowed recommending best-practice alternatives: for instance, yfinance could replace direct Yahoo calls (yfinance handles retries, etc.). However, the direct approach is already implemented and known to work reliably, so we will continue with it. We will document how to obtain and set API keys for data that require it:
  - QUIVER_API_KEY for QuiverQuant (Congress trading data).
  - CAPITOL_TRADES_API_KEY if using CapitolTrades API (another source for Congress trades,
    currently not deeply integrated).
  - ALPHA_VANTAGE_API_KEY and FINNHUB_API_KEY – these are optional; if provided, they open
    up possibilities (e.g., using Alpha Vantage for crypto or FX data, or Finnhub for news and
    fundamentals). 
  In this MVP, we may not directly use them, but the code is structured to load them for potential use .
- **Testing Framework:** The project uses unittest (as seen by tests running with python -m
  unittest ) and likely pytest can be used as well. We’ll maintain a high coverage of unit tests for
  each agent and the backtest engine. This ensures that any new strategy or change doesn’t break
  existing functionality (important given the complexity).
- **Development Tools:** We recommend using Cursor or VS Code with GitHub Copilot / OpenAI Codex
  to accelerate coding (the user will develop in Cursor with Codex). The codebase will be structured
  clearly so that an AI coding assistant can follow the spec and implement accordingly. We also set up
  continuous integration (already present with GitHub Actions) to run tests and linting on each commit.
- **Code Quality:** Adhere to PEP8 style. Tools like Black (auto-formatter), flake8 (lint), and isort (import
  sorting) are configured in CI 49 50. A Makefile (see below) will include commands to easily format
  and lint the code. The CI also uses Bandit and Safety to catch security issues 51 52
  – we should
  regularly run these to ensure no vulnerable packages or sloppy code (especially since we deal with
  external data).
- **Extensibility:** Keep the design modular. Adding a new strategy agent should be as simple as writing
  a new class in the strategies module and registering it. The spec and config-driven approach allow
  swapping components (for example, one could try an alternative sentiment model or an alternative
  backtest engine without refactoring the whole system).
- **Performance Considerations:** While not high-frequency, we should be mindful of performance in
  backtests. Python/pandas can handle our use-case (a few years of daily data across perhaps tens of
  stocks is fine). If we scale to thousands of stocks or very long histories, we might need to optimize
  (using numpy vectorization or caching results of indicators). For now, clarity of algorithm is
  53 54
  preferred. We will use vectorized pandas operations for indicator calculations for speed .
  8
  •   
  •
- **Alternative Strategies & Research:** We remain open to integrating reinforcement learning or
  other AI-driven strategy discovery in the future (e.g., training an agent via deep RL to trade).
  However, initial focus is on heuristic and indicator-based strategies augmented with LLM for
  information analysis. This is both easier to validate and aligns with industry practices of combining
  3
  quantitative methods with qualitative insights .
- **Documentation & Examples:** We will maintain up-to-date documentation (this spec, a README for
  usage, and in-line docstrings). Additionally, example scripts will be provided (e.g., how to run a
  backtest on a sample strategy). The existing repository already includes usage examples (such as a
  complete workflow demo script) which we will refine to ensure they illustrate how a user or
  developer can invoke the various components step by step.
By following this specification, the development can proceed in a structured way. Each component can be
implemented and tested in isolation (for example, start by getting DataFetcher working with live APIs and
sample data; then implement a simple strategy and verify backtest outputs; then integrate the sentiment
model; and so on). The modular design also means coding can be parallelized (one person/agent working
on the backtest engine while another works on the NLP integration, etc.), with this spec ensuring everything
will fit together.
Finally, this spec serves as a guide for AI coding agents in the development environment – it provides the
blueprint so that an AI pair-programmer (like OpenAI Codex via Cursor) can understand the goals and
structure and assist in writing the actual code. Consistently referring to the spec during development will
help maintain alignment with the intended design and catch deviations early.
