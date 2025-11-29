import { useCallback, useEffect, useState } from 'react';
import { getCachedFeatures, getCachedNews, getCachedPrices } from '../api/client';

export type SeriesPoint = { date: string; price: number; indicator: number | null };
export type NewsEvent = { date: string; label: string; url?: string | null };

export type StrategyRecord = {
  name: string;
  symbol: string;
  date: string;
  priceSeries: SeriesPoint[];
  newsEvents: NewsEvent[];
  returnPct: number;
  maxDrawdownPct: number;
  sharpe: number;
};

export type StrategyConfig = {
  symbol: string;
  name: string;
};

export type UseStrategiesResult = {
  strategies: StrategyRecord[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
};

const INDICATOR_NAME = 'sma_5';

function formatDateISO(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function computeReturn(prices: number[]): number {
  if (prices.length < 2) return 0;
  const first = prices[0];
  const last = prices[prices.length - 1];
  return ((last - first) / first) * 100;
}

function computeMaxDrawdown(prices: number[]): number {
  if (prices.length === 0) return 0;
  let peak = prices[0];
  let maxDrawdown = 0;
  for (const price of prices) {
    if (price > peak) {
      peak = price;
    }
    const drawdown = (price - peak) / peak;
    if (drawdown < maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }
  return maxDrawdown * 100;
}

function computeSharpe(prices: number[]): number {
  if (prices.length < 2) {
    return 0;
  }
  const returns: number[] = [];
  for (let i = 1; i < prices.length; i += 1) {
    returns.push(prices[i] / prices[i - 1] - 1);
  }
  if (returns.length < 2) {
    return 0;
  }
  const mean = returns.reduce((acc, val) => acc + val, 0) / returns.length;
  const variance =
    returns.reduce((acc, val) => acc + (val - mean) ** 2, 0) / (returns.length - 1 || 1);
  const stdDev = Math.sqrt(variance);
  if (stdDev === 0) return 0;
  const sharpe = (mean / stdDev) * Math.sqrt(252);
  return sharpe;
}

async function buildStrategyRecord(
  config: StrategyConfig,
  startDate: string,
  endDate: string
): Promise<StrategyRecord> {
  const [prices, features, news] = await Promise.all([
    getCachedPrices(config.symbol, startDate, endDate),
    getCachedFeatures(config.symbol, startDate, endDate, '1d', [INDICATOR_NAME]),
    getCachedNews(config.symbol, startDate, endDate),
  ]);

  const featureMap = new Map(
    features
      .filter((row) => typeof row[INDICATOR_NAME] === 'number')
      .map((row) => [row.date.slice(0, 10), Number(row[INDICATOR_NAME])])
  );

  const priceSeries: SeriesPoint[] = prices.map((row) => {
    const date = row.date.slice(0, 10);
    return { date, price: row.close, indicator: featureMap.get(date) ?? null };
  });

  const priceValues = priceSeries.map((point) => point.price);

  const newsEvents: NewsEvent[] = news.map((article) => ({
    date: article.published_at.slice(0, 10),
    label: article.headline,
    url: article.url ?? undefined,
  }));

  return {
    name: config.name,
    symbol: config.symbol,
    date: endDate,
    priceSeries,
    newsEvents,
    returnPct: computeReturn(priceValues),
    maxDrawdownPct: computeMaxDrawdown(priceValues),
    sharpe: computeSharpe(priceValues),
  };
}

export function useStrategiesData(
  configs: StrategyConfig[],
  opts: { lookbackDays?: number } = {}
): UseStrategiesResult {
  const lookbackDays = opts.lookbackDays ?? 60;
  const [strategies, setStrategies] = useState<StrategyRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  const refresh = useCallback(() => {
    setVersion((prev) => prev + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      setLoading(true);
      setError(null);
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - lookbackDays);
      const startDate = formatDateISO(start);
      const endDate = formatDateISO(end);
      try {
        const results = await Promise.all(
          configs.map((cfg) => buildStrategyRecord(cfg, startDate, endDate))
        );
        if (!cancelled) {
          setStrategies(results);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load market data');
          setStrategies([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();
    return () => {
      cancelled = true;
    };
  }, [configs, lookbackDays, version]);

  return { strategies, loading, error, refresh };
}
