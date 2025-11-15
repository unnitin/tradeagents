
## Core User Flows

_Step-by-step narratives showing how users and agents traverse the core product surfaces._

### Flow A – Explore Data & Indicators (Modular Checks)

**Goal:** Let user (and agents) explore price + news + indicators with a **modular, extensible indicator/check system**.

1. User selects a ticker, sector or universe.
2. UI shows:

   * Price chart + core indicators (SMA, EMA, RSI, MACD, etc.).
   * News timeline with sentiment & tags.
   * “Checks” panel: e.g. *“Trend up,” “High volatility,” “Negative news sentiment”*.
3. Under the hood, each “check” or indicator is a **module**:

   * Implemented as a function/feature with a common interface.
   * The “indicator registry” knows what’s available and how to compute it.
4. As we grow, we can add:

   * New technical indicators.
   * New news-derived features.
   * New portfolio/risk checks.
     …without breaking the rest of the system.

> A is explicitly **modular indicators/checks** that are easy to extend.

---

### Flow B – Create & Store Strategies (NL-first, JSON Canonical)

**Goal:** Strategy ideas can come from **user or agent**, are **stored as JSON**, and always have a **plain-language explanation**.

1. User enters a strategy idea in **natural language**
   e.g. “Buy large-cap tech when 50d > 200d and recent news is positive, sell when momentum fades.”

2. The **agent parses & proposes a strategy**:

   * Converts the NL description into a **JSON strategy spec** (our DSL).
   * Generates a **simple natural-language explanation** of that JSON:

     * “This strategy buys large-cap tech stocks when the short-term trend is up and news sentiment has been positive in the last 7 days. It sells when momentum weakens.”

3. User can also ask the **agent to come up with ideas**:

   * “Suggest a mean reversion strategy using RSI and news shocks.”
   * Agent proposes a JSON strategy + plain-language summary.
   * User can tweak it in chat (“make it less aggressive”) and the agent adjusts the JSON.

4. In the backend, each strategy has:

   * `json_spec` – canonical machine-readable definition.
   * `nl_summary` – human-friendly explanation.
   * `origin` – `user`, `agent`, or `mixed`.
   * Versioning – each change creates a new version with both JSON & NL summary.

> B emphasizes: **NL as the interface**, **JSON as the truth**, and **both user and agent as first-class idea generators**.

---

### Flow C – Backtests (User or Model Initiated)

**Goal:** Both user and agent can trigger backtests.

1. From the UI:

   * User selects a strategy and sets:

     * Universe, date range, capital, fees, etc.
   * Clicks **“Run backtest”**.

2. From chat (agent-initiated):

   * User: “Run this strategy on SP500 from 2018–2024 with 1% fees.”
   * Agent calls backtest API on behalf of the user.
   * Or: Agent itself suggests:
     “Let me test this on large-cap vs small-cap to compare” and initiates two backtests.

3. System:

   * Creates backtest job(s).
   * Shows status in:

     * Backtests list.
     * Chat (agent: “Backtest is running…” → “Backtest finished, here are the highlights.”).

> C now supports **two entry points**: UI clicks and **agent-driven experiments**.

---

### Flow D – Chat-driven Analysis & Iteration

**Goal:** Chat with agents is **central**, not a side feature.

1. After a backtest finishes, user opens **chat for that strategy/backtest**.

2. Agent:

   * Explains performance in simple language:

     * “The strategy did well from 2016–2019 but struggled during COVID due to abrupt news shocks.”
   * Highlights metrics and failure modes:

     * “Max drawdown 35% in March 2020.”

3. User can **iterate via chat**:

   * “Reduce drawdown, keep similar returns.”
   * “Make the strategy less sensitive to single bad news events.”
   * Agent **modifies the JSON spec**, explains what changed in NL (“I added a filter to ignore isolated negative articles unless sentiment stays negative for 3 days”), saves a new version.
   * Optionally **auto-runs** a new backtest or asks permission.

4. Over time, the chat becomes the **primary design surface**:

   * Strategy design, modification, and backtesting all flow through conversation.

> D is now the glue: **analysis + iteration + execution** all via agents in chat.
