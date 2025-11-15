# Strategy & Backtest API Specification

_Reference for REST/JSON contracts that power strategy creation, orchestration, and backtesting._

## 1. Strategy Service

### 1.1 Entities

#### Strategy

```jsonc
{
  "id": "s_001",
  "user_id": "u_123",
  "name": "Trend + Positive News",
  "description": "Momentum plus news sentiment filter.",
  "current_version_id": "sv_003",
  "created_at": "2025-11-13T16:00:00Z",
  "updated_at": "2025-11-13T16:05:00Z"
}
```

#### StrategyVersion

```jsonc
{
  "id": "sv_003",
  "strategy_id": "s_001",
  "json_spec": { /* strategy DSL */ },
  "nl_summary": "Buys when 50d > 200d and sentiment is positive...",
  "origin": "user",            // "user" | "agent" | "mixed"
  "created_by": "u_123",       // user id or "agent_system"
  "created_at": "2025-11-13T16:05:00Z"
}
```

---

### 1.2 Endpoints

#### POST `/strategies`

Create a new strategy with an initial version.

**Request**

```json
{
  "user_id": "u_123",
  "name": "Trend + Positive News",
  "description": "Momentum plus news sentiment filter.",
  "json_spec": { /* strategy DSL */ },
  "nl_summary": "Buys when 50d > 200d and news sentiment is positive...",
  "origin": "user"
}
```

**Response – 201 Created**

```json
{
  "strategy": {
    "id": "s_001",
    "user_id": "u_123",
    "name": "Trend + Positive News",
    "description": "Momentum plus news sentiment filter.",
    "current_version_id": "sv_001",
    "created_at": "2025-11-13T16:00:00Z",
    "updated_at": "2025-11-13T16:00:00Z"
  },
  "version": {
    "id": "sv_001",
    "strategy_id": "s_001",
    "json_spec": { /* ... */ },
    "nl_summary": "Buys when 50d > 200d...",
    "origin": "user",
    "created_by": "u_123",
    "created_at": "2025-11-13T16:00:00Z"
  }
}
```

---

#### GET `/strategies`

List strategies for a user.

**Query params**

- `user_id` (required)
- Optional filters (e.g. pagination) can be added later.

**Example**

`GET /strategies?user_id=u_123`

**Response – 200 OK**

```json
{
  "items": [
    {
      "id": "s_001",
      "user_id": "u_123",
      "name": "Trend + Positive News",
      "description": "Momentum plus news sentiment filter.",
      "current_version_id": "sv_003",
      "origin_latest": "mixed",
      "created_at": "2025-11-13T16:00:00Z",
      "updated_at": "2025-11-13T16:05:00Z"
    }
  ]
}
```

---

#### GET `/strategies/{strategy_id}`

Get a strategy and its current version.

**Response – 200 OK**

```json
{
  "strategy": {
    "id": "s_001",
    "user_id": "u_123",
    "name": "Trend + Positive News",
    "description": "Momentum plus news sentiment filter.",
    "current_version_id": "sv_003",
    "created_at": "2025-11-13T16:00:00Z",
    "updated_at": "2025-11-13T16:05:00Z"
  },
  "current_version": {
    "id": "sv_003",
    "strategy_id": "s_001",
    "json_spec": { /* DSL */ },
    "nl_summary": "Buys when 50d > 200d and sentiment is positive...",
    "origin": "mixed",
    "created_by": "agent_system",
    "created_at": "2025-11-13T16:05:00Z"
  }
}
```

---

#### POST `/strategies/{strategy_id}/versions`

Create a new strategy version (typically after refinement).

**Request**

```json
{
  "json_spec": { /* updated DSL */ },
  "nl_summary": "Now includes a volatility cap and longer sentiment window.",
  "origin": "agent",
  "created_by": "agent_system"
}
```

**Response – 201 Created**

```json
{
  "version": {
    "id": "sv_004",
    "strategy_id": "s_001",
    "json_spec": { /* updated DSL */ },
    "nl_summary": "Now includes a volatility cap and longer sentiment window.",
    "origin": "agent",
    "created_by": "agent_system",
    "created_at": "2025-11-13T16:10:00Z"
  },
  "strategy": {
    "id": "s_001",
    "current_version_id": "sv_004",
    "updated_at": "2025-11-13T16:10:00Z"
  }
}
```

---

#### GET `/strategies/{strategy_id}/versions`

List all versions of a strategy.

**Response – 200 OK**

```json
{
  "items": [
    {
      "id": "sv_001",
      "origin": "user",
      "created_at": "2025-11-13T16:00:00Z"
    },
    {
      "id": "sv_002",
      "origin": "agent",
      "created_at": "2025-11-13T16:03:00Z"
    },
    {
      "id": "sv_003",
      "origin": "mixed",
      "created_at": "2025-11-13T16:05:00Z"
    }
  ]
}
```

---

#### GET `/strategy-versions/{version_id}`

Get a specific strategy version with full JSON spec.

**Response – 200 OK**

```json
{
  "id": "sv_003",
  "strategy_id": "s_001",
  "json_spec": { /* DSL */ },
  "nl_summary": "Buys when 50d > 200d and sentiment is positive...",
  "origin": "mixed",
  "created_by": "agent_system",
  "created_at": "2025-11-13T16:05:00Z"
}
```

---

#### POST `/strategies/validate`

Validate a strategy DSL without saving it.

**Request**

```json
{
  "json_spec": { /* DSL */ }
}
```

**Response – 200 OK (valid)**

```json
{
  "valid": true,
  "errors": []
}
```

**Response – 200 OK (invalid)**

```json
{
  "valid": false,
  "errors": [
    {
      "path": "entry.conditions[1].params.window",
      "message": "Must be >= 1"
    }
  ]
}
```

---

## 2. Backtest Orchestrator

### 2.1 Entities

#### Backtest

```jsonc
{
  "id": "bt_001",
  "user_id": "u_123",
  "strategy_version_id": "sv_004",
  "status": "completed",              // "queued" | "running" | "completed" | "failed"
  "config": {
    "universe_override": "SP500",
    "start_date": "2015-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000,
    "transaction_cost_bps": 5,
    "slippage_model": "basic"
  },
  "metrics_summary": {
    "total_return": 1.2,
    "cagr": 0.115,
    "max_drawdown": 0.25,
    "sharpe": 1.1
  },
  "created_at": "2025-11-13T16:01:00Z",
  "started_at": "2025-11-13T16:01:05Z",
  "completed_at": "2025-11-13T16:01:30Z"
}
```

#### BacktestResult

```jsonc
{
  "id": "bt_001",
  "equity_curve": [
    { "date": "2015-01-01", "equity": 100000 },
    { "date": "2015-01-02", "equity": 100350 }
  ],
  "drawdowns": [
    { "start": "2020-02-20", "end": "2020-04-01", "depth": 0.35 }
  ],
  "trades": [
    {
      "symbol": "AAPL",
      "side": "buy",
      "entry_date": "2018-01-10",
      "exit_date": "2018-02-15",
      "entry_price": 170.0,
      "exit_price": 185.0,
      "quantity": 100,
      "pnl": 1500.0,
      "return_pct": 0.088
    }
  ],
  "per_period_metrics": [
    { "period": "2015", "return": 0.10 },
    { "period": "2016", "return": 0.12 }
  ]
}
```

---

### 2.2 Endpoints

#### POST `/backtests`

Create a new backtest job.

**Request**

```json
{
  "user_id": "u_123",
  "strategy_version_id": "sv_004",
  "config": {
    "universe_override": "SP500",
    "start_date": "2015-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000,
    "transaction_cost_bps": 5,
    "slippage_model": "basic"
  },
  "tags": ["chat_session:conv_789"]
}
```

**Response – 202 Accepted**

```json
{
  "backtest": {
    "id": "bt_001",
    "user_id": "u_123",
    "strategy_version_id": "sv_004",
    "status": "queued",
    "config": {
      "universe_override": "SP500",
      "start_date": "2015-01-01",
      "end_date": "2024-12-31",
      "initial_capital": 100000,
      "transaction_cost_bps": 5,
      "slippage_model": "basic"
    },
    "created_at": "2025-11-13T16:01:00Z"
  }
}
```

---

#### GET `/backtests`

List backtests for a user.

**Query params**

- `user_id` (required)

**Example**

`GET /backtests?user_id=u_123`

**Response – 200 OK**

```json
{
  "items": [
    {
      "id": "bt_001",
      "user_id": "u_123",
      "strategy_version_id": "sv_004",
      "status": "completed",
      "created_at": "2025-11-13T16:01:00Z",
      "completed_at": "2025-11-13T16:01:30Z",
      "metrics_summary": {
        "total_return": 1.2,
        "cagr": 0.115,
        "max_drawdown": 0.25,
        "sharpe": 1.1
      }
    }
  ]
}
```

---

#### GET `/backtests/{backtest_id}`

Get a single backtest (status + summary metrics).

**Response – 200 OK**

```json
{
  "id": "bt_001",
  "user_id": "u_123",
  "strategy_version_id": "sv_004",
  "status": "completed",
  "config": {
    "universe_override": "SP500",
    "start_date": "2015-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000,
    "transaction_cost_bps": 5,
    "slippage_model": "basic"
  },
  "metrics_summary": {
    "total_return": 1.2,
    "cagr": 0.115,
    "max_drawdown": 0.25,
    "sharpe": 1.1
  },
  "created_at": "2025-11-13T16:01:00Z",
  "started_at": "2025-11-13T16:01:05Z",
  "completed_at": "2025-11-13T16:01:30Z"
}
```

---

#### GET `/backtests/{backtest_id}/results`

Get full backtest results.

**Response – 200 OK**

```json
{
  "id": "bt_001",
  "equity_curve": [ /* ... */ ],
  "drawdowns": [ /* ... */ ],
  "trades": [ /* ... */ ],
  "per_period_metrics": [ /* ... */ ]
}
```

---

## 3. Agent Tool APIs

Helper endpoints for LLM/agent orchestration (can be internal-only).

---

### 3.1 POST `/agent/strategies/from-text`

Create a strategy (and version) from a natural-language description.

**Request**

```json
{
  "user_id": "u_123",
  "name": "Trend + Positive News",
  "description": "Generated from user prompt",
  "natural_language_prompt": "Buy large-cap tech when the 50-day MA is above the 200-day and news has been positive for a week..."
}
```

**Typical server flow**

1. Call LLM → produce `json_spec` + `nl_summary`.
2. Validate via `/strategies/validate`.
3. Persist via `POST /strategies`.

**Response – 201 Created**

```json
{
  "strategy": { /* Strategy */ },
  "version": { /* StrategyVersion */ }
}
```

---

### 3.2 POST `/agent/strategies/{version_id}/refine`

Refine an existing strategy version via natural-language instructions.

**Request**

```json
{
  "user_id": "u_123",
  "instruction": "Reduce max drawdown, keep similar returns. Make it less sensitive to single bad headlines."
}
```

**Typical server flow**

1. Fetch `json_spec` for `version_id`.
2. Call LLM with current spec + instruction → new `json_spec` + updated `nl_summary`.
3. Validate.
4. Create new version via `POST /strategies/{strategy_id}/versions`.

**Response – 201 Created**

```json
{
  "old_version_id": "sv_004",
  "new_version": { /* StrategyVersion sv_005 */ }
}
```

---

### 3.3 POST `/agent/backtests`

Agent-triggered backtest (thin wrapper over `/backtests`).

**Request**

```json
{
  "user_id": "u_123",
  "strategy_version_id": "sv_005",
  "config": {
    "universe_override": "SP500",
    "start_date": "2015-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000,
    "transaction_cost_bps": 5,
    "slippage_model": "basic"
  },
  "conversation_id": "conv_789"
}
```

**Response – 202 Accepted**

```json
{
  "backtest": { /* same schema as POST /backtests */ }
}
```

---

### 3.4 POST `/agent/backtests/{backtest_id}/explain`

Generate a natural-language explanation of a backtest result.

**Request**

```json
{
  "user_id": "u_123",
  "detail_level": "summary",          // "summary" | "detailed"
  "focus": ["drawdowns", "regimes"]   // optional hints
}
```

**Typical server flow**

1. Fetch backtest metrics + sampled curves/trades.
2. Call LLM with those + strategy NL summary.
3. Return explanation + suggested changes.

**Response – 200 OK**

```json
{
  "explanation": "The strategy performed well from 2016–2019 but suffered a 35% drawdown in 2020 due to volatility spikes...",
  "suggested_changes": [
    "Add a volatility filter to reduce exposure during spikes.",
    "Lengthen the news sentiment window from 3 to 7 days."
  ]
}
```
