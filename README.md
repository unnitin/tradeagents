# trade
Running trades using AI, GenAI

algo-trading/
│
├── data/
│   └── fetch_data.py         # Get and preprocess market data
│
├── strategies/
│   └── mean_reversion.py     # Example strategy implementation
│
├── backtest/
│   └── backtest_engine.py    # Simulate trading
│
├── execution/
│   └── broker_api.py         # Connect/send orders
│
├── risk/
│   └── risk_manager.py       # Enforce risk rules
│
├── config/
│   └── settings.yaml         # API keys, parameters, config
│
├── main.py                   # Entry point for trading bot
└── utils.py                  # Common helper functions
