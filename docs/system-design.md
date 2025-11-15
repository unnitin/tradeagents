
---

## System Design

_High-level blueprint covering services, flows, and data contracts for the Trade platform._

The architecture explicitly supports:

* Modular indicators/checks (A)
* Dual-origin, NL+JSON strategies (B)
* Backtests from UI or agent (C)
* Chat-centric iteration (D)

### 1.1 Core Services Overview

We can still start the MVP with a **modular monolith**, but in terms of clear modules:

1. **User & Auth Service**
2. **Strategy Service**
3. **Indicator & Feature Service** (modular checks)
4. **Backtest Orchestrator & Engine**
5. **Market Data Service**
6. **News & NLP Service**
7. **Agent/LLM Orchestrator**
8. **Conversation Service** (strategy-focused chat)

---

### 1.2 Indicator & Feature Service (Flow A)

**Responsibility:** Provide a **modular registry of indicators & checks**.

* **Indicator Registry**

  * Metadata for each indicator/check:

    * Name, description, inputs (symbol, window, etc.), output type.
    * Category: technical, news-based, risk, portfolio, etc.
  * Versioning so we can evolve computations over time.

* **Indicator Engine**

  * Standard interface:
    `compute(indicator_name, params, symbol/universe, date_range)`
  * Internally, each indicator is a plugin/module:

    * Can be implemented in Python/Numpy.
  * Supports both:

    * On-the-fly calculation.
    * Precomputed indicator storage.

* **Why this matters for MVP**

  * When we add a new “check”, we:

    * Implement a module conforming to the interface.
    * Register its metadata.
    * The UI and agents discover it from the registry (no bespoke wiring each time).

---

### 1.3 Strategy Service (Flow B)

**Responsibility:** Store strategy specs (JSON) and their **NL summaries & origin**.

* **Data model (conceptually)**

  * `strategies`

    * `id`
    * `user_id`
    * `current_version_id`
  * `strategy_versions`

    * `id`
    * `strategy_id`
    * `json_spec` (canonical DSL)
    * `nl_summary` (agent-generated or user-supplied)
    * `origin` (`user`, `agent`, `mixed`)
    * `created_at`

* **APIs**

  * `POST /strategies` – create (agent or user)
  * `POST /strategies/{id}/versions` – new version (agent-edited or user-edited)
  * `GET /strategies/{id}` – latest version + NL summary
  * `GET /strategies/{id}/versions` – history

* **Tight integration with Agent**

  * Agent calls Strategy Service to:

    * Create strategies derived from chat.
    * Save modified versions after NL refinements.

---

### 2.4 Backtest Orchestrator & Engine (Flow C)

**Responsibility:** Accept backtest requests from UI or Agent and run them.

* **Orchestrator (API level)**

  * `POST /backtests`

    * Inputs: `strategy_version_id`, universe, dates, capital, fees.
    * Called by:

      * UI when user clicks “Run backtest”.
      * Agent Orchestrator when chat triggers a backtest.
  * `GET /backtests/{id}` – status + meta.
  * `GET /backtests/{id}/results` – performance data.

* **Worker / Engine**

  * Consumes jobs from `backtest_jobs` queue.
  * For each job:

    * Fetch `json_spec` from Strategy Service.
    * Use Indicator & Feature Service + Data Services to get required inputs.
    * Run simulation.
    * Stores results (summary stats + time series + trades).
    * Publishes an event `backtest.completed`.

* **Integration with Agent & Conversation**

  * When a backtest completes, Orchestrator:

    * Notifies Agent / Conversation service so the agent can **proactively summarize** results in chat.

---

### 1.5 Market Data & News Services

* **Market Data Service**

  * Price/volume data.
  * Exposed via API to:

    * Frontend charts.
    * Backtest Engine.
    * Indicator Engine.

* **News & NLP Service**

  * Ingests news.
  * Runs NLP (sentiment, tags).
  * Provides ticker/time-filtered news & features:

    * `GET /news?ticker=AAPL&start=...&end=...`
    * `GET /news_features?ticker=AAPL&date=...`

* **Indicator/Feature Service** will likely **wrap** this to produce higher-level features like “3-day sentiment average”, “event shock score”, etc.

---

### 1.6 Agent / LLM Orchestrator (Flows B, C, D)

This is now **central** instead of auxiliary.

**Key “tools” / capabilities:**

1. **Strategy Author**

   * Input: natural language idea.
   * Output:

     * `json_spec` (validated against DSL schema).
     * `nl_summary`.
   * Calls Strategy Service to persist.

2. **Strategy Editor**

   * Input: existing JSON + user instructions (“make it less volatile”).
   * Output:

     * New `json_spec` + updated `nl_summary`.
   * Persists as new strategy version.

3. **Backtest Explainer**

   * Input: backtest results (metrics, curves, maybe sampled trades).
   * Output: explanation in natural language.
   * Suggests modifications:

     * As NL + JSON diff.

4. **Backtest Launcher**

   * Tool to call `POST /backtests` directly from chat.

**Implementation pattern**

* Backend exposes a small set of “tools” to the LLM:

  * `create_strategy`, `update_strategy`, `run_backtest`, `get_backtest_summary`, etc.
* LLM uses function calling / structured output to orchestrate.

---

### 1.7 Conversation Service (Flow D)

**Responsibility:** Glue strategies, backtests, and agent reasoning into a single conversational context.

* **Data model**

  * `conversations`

    * `id`
    * `user_id`
    * optional `strategy_id`
  * `messages`

    * `id`
    * `conversation_id`
    * `sender` (user/agent/system)
    * `content` (text + metadata)
    * optional `backtest_id` references

* **Behavior**

  * When a user chat references “this strategy” or “the last backtest”, the Conversation Service:

    * Maintains the mapping to the actual IDs.
  * When `backtest.completed` event fires:

    * Conversation for that strategy/backtest can be updated:

      * Agent posts a summary message.

* **Why separate this out (conceptually)**

  * Clear separation between:

    * The **model** that generates text & strategy JSON.
    * The **timeline** of interactions, backtests, and changes.

---

### 1.8 Putting It All Together (End-to-End Example)

**Example: full loop with your updated flows**

1. **Explore (A)**

   * User opens AAPL.
   * UI calls Indicator Service for SMA, RSI, and a “NewsTrend” check.
   * User sees modular checks & gets a feel for the behavior.

2. **Create Idea (B)**

   * User: “Build a strategy that buys AAPL when short-term trend is up and news is positive for a week.”
   * Agent:

     * Calls Strategy Author tool → JSON spec + NL summary.
     * Stores in Strategy Service.
   * UI shows strategy summary: “Trend + Positive News Strategy”.

3. **Run Backtest (C)**

   * User: “Backtest this on SP500 2015–2024 with 100k capital.”
   * Agent:

     * Calls Backtest Orchestrator to create job.
     * Tells user: “Starting backtest…”
   * Engine runs, stores results, emits `backtest.completed`.

4. **Explain & Iterate (D)**

   * Agent receives completion event and:

     * Fetches results.
     * Posts: “The strategy returned 12% CAGR with 25% max drawdown. It struggled in 2020 crashes.”
   * User: “Reduce drawdown even if we lose some return.”
   * Agent:

     * Modifies JSON spec (e.g., adds tighter stop-loss, risk cap).
     * Saves new version via Strategy Editor.
     * Suggests: “Shall I backtest this version?” → user says yes.
   * Loop continues.
