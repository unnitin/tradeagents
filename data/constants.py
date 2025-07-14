from dataclasses import dataclass

@dataclass(frozen=True)
class OHLCVResampleRules:
    open: str = 'first'
    high: str = 'max'
    low: str = 'min'
    close: str = 'last'
    volume: str = 'sum'

# Instance to use elsewhere
if __name__ == "__main__":
    # Example usage
    resample_rules = OHLCVResampleRules()
    print(resample_rules)