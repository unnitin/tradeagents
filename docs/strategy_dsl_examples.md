
# Strategy DSL Specification & Common Use‑Case Examples

_Quick primer on the JSON DSL structure with representative templates for frequent strategy motifs._

This document defines the **Agentic Strategy DSL** (expressed as JSON) and demonstrates how it handles the most common trader strategy patterns (technical, news‑driven, hybrid, portfolio/risk, filters).

---

# 1. DSL Structure

```jsonc
{
  "schema_version": "1.0",
  "timeframe": "1d",

  "universe": {
    "type": "preset",
    "value": "SP500"
  },

  "entry": {
    "logic": "and",
    "conditions": []
  },

  "exit": {
    "logic": "or",
    "conditions": []
  },

  "position_sizing": {
    "mode": "fixed_fraction",
    "fraction": 0.1,
    "max_positions": 10
  },

  "risk": {
    "max_gross_exposure": 1.0,
    "max_single_position_pct": 0.15,
    "stop_loss": {
      "type": "trailing_pct",
      "value": 0.2
    },
    "take_profit": {
      "type": "pct",
      "value": 0.4
    }
  },

  "execution": {
    "order_type": "market",
    "time_in_force": "day",
    "rebalance": "daily_close"
  }
}
```

---

# 2. Condition Types

## 2.1 `indicator_compare`

```jsonc
{
  "type": "indicator_compare",
  "left": {
    "source": "indicator",
    "indicator": "RSI",
    "params": { "window": 14 },
    "field": "value"
  },
  "operator": "<",
  "right": { "source": "constant", "value": 30 }
}
```

---

## 2.2 `indicator_cross`

```jsonc
{
  "type": "indicator_cross",
  "fast": { "indicator": "SMA", "params": { "window": 50 } },
  "slow": { "indicator": "SMA", "params": { "window": 200 } },
  "direction": "up"
}
```

---

## 2.3 `news_feature`

```jsonc
{
  "type": "news_feature",
  "feature": "sentiment_mean",
  "lookback_days": 7,
  "operator": ">",
  "value": 0.2
}
```

---

## 2.4 `composite`

```jsonc
{
  "type": "composite",
  "logic": "and",
  "conditions": [
    { /* condition A */ },
    { /* condition B */ }
  ]
}
```

---

# 3. DSL Examples for Top Trader Use‑Cases

Below are real strategies encoded in the DSL.

---

## 3.1 SMA Crossover (Trend Follow)

```jsonc
{
  "entry": {
    "logic": "and",
    "conditions": [{
      "type": "indicator_cross",
      "fast": { "indicator": "SMA", "params": { "window": 50 }},
      "slow": { "indicator": "SMA", "params": { "window": 200 }},
      "direction": "up"
    }]
  },
  "exit": {
    "logic": "and",
    "conditions": [{
      "type": "indicator_cross",
      "fast": { "indicator": "SMA", "params": { "window": 50 }},
      "slow": { "indicator": "SMA", "params": { "window": 200 }},
      "direction": "down"
    }]
  }
}
```

---

## 3.2 RSI Mean Reversion

```jsonc
{
  "entry": {
    "logic": "and",
    "conditions": [{
      "type": "indicator_compare",
      "left": { "source": "indicator", "indicator": "RSI", "params": { "window": 14 }, "field": "value" },
      "operator": "<",
      "right": { "source": "constant", "value": 30 }
    }]
  },
  "exit": {
    "logic": "and",
    "conditions": [{
      "type": "indicator_compare",
      "left": { "source": "indicator", "indicator": "RSI", "params": { "window": 14 }, "field": "value" },
      "operator": ">",
      "right": { "source": "constant", "value": 50 }
    }]
  }
}
```

---

## 3.3 Breakout + Volume Confirmation

```jsonc
{
  "entry": {
    "logic": "and",
    "conditions": [
      {
        "type": "indicator_compare",
        "left": { "source": "indicator", "indicator": "PRICE", "params": { "field": "close" }, "field": "value" },
        "operator": ">",
        "right": { "source": "indicator", "indicator": "HIGH_N", "params": { "window": 20 }, "field": "value" }
      },
      {
        "type": "indicator_compare",
        "left": { "source": "indicator", "indicator": "VOLUME", "params": {}, "field": "value" },
        "operator": ">",
        "right": { "source": "indicator", "indicator": "AVG_VOLUME", "params": { "window": 20, "multiplier": 1.5 }, "field": "value" }
      }
    ]
  },
  "exit": {
    "logic": "and",
    "conditions": [{
      "type": "indicator_compare",
      "left": { "source": "indicator", "indicator": "PRICE", "params": { "field": "close" }, "field": "value" },
      "operator": "<",
      "right": { "source": "indicator", "indicator": "LOW_N", "params": { "window": 20 }, "field": "value" }
    }]
  }
}
```

---

## 3.4 Trend + News Sentiment Filter

```jsonc
{
  "entry": {
    "logic": "and",
    "conditions": [
      {
        "type": "indicator_compare",
        "left": { "source": "indicator", "indicator": "SMA", "params": { "window": 50 }, "field": "value" },
        "operator": ">",
        "right": { "source": "indicator", "indicator": "SMA", "params": { "window": 200 }, "field": "value" }
      },
      {
        "type": "news_feature",
        "feature": "sentiment_mean",
        "lookback_days": 7,
        "operator": ">",
        "value": 0.2
      }
    ]
  },
  "exit": {
    "logic": "or",
    "conditions": [
      {
        "type": "indicator_compare",
        "left": { "source": "indicator", "indicator": "RSI", "params": { "window": 14 }, "field": "value" },
        "operator": ">",
        "right": { "source": "constant", "value": 70 }
      },
      {
        "type": "news_feature",
        "feature": "sentiment_mean",
        "lookback_days": 3,
        "operator": "<",
        "value": 0
      }
    ]
  }
}
```

---

## 3.5 Earnings Drift

```jsonc
{
  "entry": {
    "logic": "and",
    "conditions": [
      { "type": "news_feature", "feature": "sentiment_mean", "lookback_days": 2, "operator": ">", "value": 0.5 },
      { "type": "news_feature", "feature": "count_positive", "lookback_days": 2, "operator": ">=", "value": 1 }
    ]
  },
  "exit": {
    "logic": "and",
    "conditions": [{
      "type": "indicator_compare",
      "left": { "source": "indicator", "indicator": "SMA", "params": { "window": 20 }, "field": "value" },
      "operator": "<",
      "right": { "source": "indicator", "indicator": "SMA", "params": { "window": 50 }, "field": "value" }
    }]
  }
}
```

---

## 3.6 Volatility Filter

```jsonc
{
  "entry": {
    "logic": "and",
    "conditions": [
      {"type": "indicator_compare", "left": {"source": "indicator","indicator": "ATR","params": {"window": 14},"field": "value"}, "operator": "<", "right": {"source": "constant","value": 0.05}}
    ]
  }
}
```

---

## 3.7 Risk-Limited Portfolio Controls

```jsonc
{
  "position_sizing": {
    "mode": "fixed_fraction",
    "fraction": 0.1,
    "max_positions": 10
  },
  "risk": {
    "max_gross_exposure": 1.5,
    "max_single_position_pct": 0.15
  }
}
```

---

## 3.8 News Shock Avoidance

```jsonc
{
  "exit": {
    "logic": "or",
    "conditions": [{
      "type": "news_feature",
      "feature": "count_negative",
      "lookback_days": 2,
      "operator": ">=",
      "value": 3
    }]
  }
}
```

---

## 3.9 Universe Filter (Sector / Theme)

```jsonc
{
  "universe": {
    "type": "filter",
    "value": "sector == 'Technology' AND market_cap > 10e9"
  }
}
```

---

## 3.10 Momentum + Pullback (Composite)

```jsonc
{
  "entry": {
    "logic": "and",
    "conditions": [{
      "type": "composite",
      "logic": "and",
      "conditions": [
        {
          "type": "indicator_compare",
          "left": {"source": "indicator","indicator": "SMA","params": {"window": 50},"field": "value"},
          "operator": ">",
          "right": {"source": "indicator","indicator": "SMA","params": {"window": 200},"field": "value"}
        },
        {
          "type": "indicator_compare",
          "left": {"source": "indicator","indicator": "RSI","params": {"window": 14},"field": "value"},
          "operator": "<",
          "right": {"source": "constant","value": 40}
        }
      ]
    }]
  }
}
```

---

## 3.11 Equal-Weight Factor Strategy

```jsonc
{
  "position_sizing": {
    "mode": "equal_weight",
    "max_positions": 50
  },
  "entry": {
    "logic": "and",
    "conditions": [
      {"type": "indicator_compare","left": {"source": "indicator","indicator": "MOMENTUM_12M","field": "value"}, "operator": ">", "right": {"source": "constant","value": 0}},
      {"type": "indicator_compare","left": {"source": "indicator","indicator": "QUALITY_SCORE","field": "value"}, "operator": ">", "right": {"source": "constant","value": 60}}
    ]
  }
}
```

---

## 3.12 News‑Only Sentiment Strategy

```jsonc
{
  "entry": {
    "logic": "and",
    "conditions": [
      {"type": "news_feature","feature": "sentiment_mean","lookback_days": 3,"operator": ">","value": 0.4},
      {"type": "news_feature","feature": "count_negative","lookback_days": 3,"operator": "==","value": 0}
    ]
  },
  "exit": {
    "logic": "or",
    "conditions": [
      {"type": "news_feature","feature": "sentiment_mean","lookback_days": 3,"operator": "<=","value": 0}
    ]
  }
}
```

---

# 4. Coverage Summary

The DSL supports:
- Trend strategies  
- Mean-reversion  
- Breakout & volume confirmation  
- Hybrid news + technical  
- Earnings/event-based  
- Volatility filters  
- Portfolio sizing & risk  
- Universe filters  
- Composite nested logic  

Suitable for MVP + beyond.
