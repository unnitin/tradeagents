const DEFAULT_BASE_URL = 'http://localhost:8000';
const API_BASE = (import.meta.env.VITE_API_BASE || DEFAULT_BASE_URL).replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export type PriceRow = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type FeatureRow = {
  date: string;
  [featureName: string]: string | number | null | undefined;
};

export type NewsRow = {
  symbol: string;
  published_at: string;
  headline: string;
  summary: string;
  url?: string | null;
};

export async function getCachedPrices(
  symbol: string,
  startDate: string,
  endDate: string,
  interval = '1d'
): Promise<PriceRow[]> {
  const params = new URLSearchParams({
    symbol,
    start_date: startDate,
    end_date: endDate,
    interval,
  });
  const data = await request<{ prices: PriceRow[] }>(`/cache/prices?${params.toString()}`);
  return data.prices;
}

export async function getCachedFeatures(
  symbol: string,
  startDate: string,
  endDate: string,
  interval = '1d',
  featureNames?: string[]
): Promise<FeatureRow[]> {
  const params = new URLSearchParams({
    symbol,
    start_date: startDate,
    end_date: endDate,
    interval,
  });
  (featureNames || []).forEach((name) => params.append('feature', name));
  const data = await request<{ features: FeatureRow[] }>(`/cache/features?${params.toString()}`);
  return data.features;
}

export async function getCachedNews(symbol: string, startDate: string, endDate: string): Promise<NewsRow[]> {
  const params = new URLSearchParams({
    symbol,
    start_date: startDate,
    end_date: endDate,
  });
  const data = await request<{ news: NewsRow[] }>(`/cache/news?${params.toString()}`);
  return data.news;
}

export { API_BASE };
