from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class OHLCVResampleRules:
    open: str = 'first'
    high: str = 'max'
    low: str = 'min'
    close: str = 'last'
    volume: str = 'sum'

# Yahoo Finance API interval mapping
YAHOO_FINANCE_INTERVALS: Dict[str, str] = {
    '1d': '1d',
    '1h': '1h', 
    '5m': '5m',
    '1m': '1m'
}

# Instance to use elsewhere
if __name__ == "__main__":
    # Example usage
    resample_rules = OHLCVResampleRules()
    print(resample_rules)