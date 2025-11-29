import { useMemo, useState } from 'react';
import type { StrategyRecord, SeriesPoint, NewsEvent, StrategyConfig } from '../hooks/useStrategiesData';
import { useStrategiesData } from '../hooks/useStrategiesData';

const STRATEGY_CONFIGS: StrategyConfig[] = [
  { symbol: 'AAPL', name: 'AAPL Momentum' },
  { symbol: 'MSFT', name: 'MSFT Signal Blend' },
  { symbol: 'NVDA', name: 'NVDA Growth Pulse' },
];

type ChartProps = {
  series: SeriesPoint[];
  news: NewsEvent[];
};

function StrategyChart({ series, news }: ChartProps) {
  const width = 620;
  const height = 220;
  const padding = 20;

  const prices = series.map((p) => p.price);
  const indicators = series.map((p) => (p.indicator ?? p.price));
  const hasIndicator = series.some((p) => p.indicator !== null);
  const allValues = [...prices, ...(hasIndicator ? indicators : prices)];
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);

  const scaleX = (index: number) => {
    if (series.length === 1) return width / 2;
    return padding + (index / (series.length - 1)) * (width - padding * 2);
  };
  const scaleY = (value: number) => {
    if (max === min) return height / 2;
    return height - padding - ((value - min) / (max - min)) * (height - padding * 2);
  };

  const toPath = (values: number[]) =>
    values
      .map((v, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(i).toFixed(2)} ${scaleY(v).toFixed(2)}`)
      .join(' ');

  const dateToIndex = (d: string) => series.findIndex((p) => p.date === d);

  return (
    <svg className="strategy-chart" viewBox={`0 0 ${width} ${height}`} role="img">
      <path d={toPath(prices)} className="price-line" />
      {hasIndicator && <path d={toPath(indicators)} className="indicator-line" />}
      {series.map((point, idx) => (
        <circle
          key={point.date}
          cx={scaleX(idx)}
          cy={scaleY(point.price)}
          r={3}
          className="price-dot"
        />
      ))}
      {news.map((item) => {
        const idx = dateToIndex(item.date);
        if (idx === -1) return null;
        const x = scaleX(idx);
        return (
          <g key={item.label}>
            <line x1={x} x2={x} y1={padding} y2={height - padding} className="news-line" />
            <circle cx={x} cy={padding + 6} r={5} className="news-marker" />
            <text x={x + 8} y={padding + 10} className="news-label">
              {item.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function Dashboard() {
  const { strategies, loading, error, refresh } = useStrategiesData(STRATEGY_CONFIGS);

  return (
    <section className="dashboard" id="dashboard">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h2>Performance snapshots</h2>
          <p className="subhead">
            Charts blend price, technical signals, and key news markers—plus quick stats on return and risk.
          </p>
        </div>
        <div className="dashboard-actions">
          <button type="button" className="ghost-btn" onClick={refresh}>
            Refresh data
          </button>
        </div>
      </header>

      {loading && <p className="eyebrow">Loading market data…</p>}
      {error && (
        <div
          style={{
            marginTop: '1rem',
            padding: '1rem',
            borderRadius: '16px',
            background: '#fff0f0',
            border: '1px solid #ffb4b4',
          }}
        >
          <p style={{ marginBottom: '0.5rem' }}>Unable to load strategy data: {error}</p>
          <button type="button" className="ghost-btn" onClick={refresh}>
            Retry
          </button>
        </div>
      )}

      {strategies.length > 0 && (
        <>
          <div className="strategy-grid">
            {strategies.slice(0, 2).map((strategy) => (
              <article key={strategy.name} className="strategy-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">{strategy.date}</p>
                    <h3>{strategy.name}</h3>
                  </div>
                  <div className="metrics-inline">
                    <div>
                      <span className="metric-label">Return</span>
                      <span className="metric-value">{strategy.returnPct.toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="metric-label">Max DD</span>
                      <span className="metric-value">{strategy.maxDrawdownPct.toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="metric-label">Sharpe</span>
                      <span className="metric-value">{strategy.sharpe.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
                <StrategyChart series={strategy.priceSeries} news={strategy.newsEvents} />
              </article>
            ))}
          </div>

          <div className="strategy-table-card">
            <div className="table-header-row">
              <div className="table-title">
                <p className="eyebrow">Strategies</p>
                <h3>All runs</h3>
              </div>
              <small>Sort by name or date to scan recent runs.</small>
            </div>
            <StrategyTable rows={strategies} />
          </div>
        </>
      )}
    </section>
  );
}

type SortKey = 'name' | 'date';

function StrategyTable({ rows }: { rows: StrategyRecord[] }) {
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [ascending, setAscending] = useState<boolean>(true);

  const sortedRows = useMemo(() => {
    const sorted = [...rows];
    sorted.sort((a, b) => {
      if (sortKey === 'name') {
        return ascending ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
      }
      return ascending ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date);
    });
    return sorted;
  }, [rows, sortKey, ascending]);

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) {
      setAscending(!ascending);
    } else {
      setSortKey(key);
      setAscending(true);
    }
  };

  return (
    <div className="strategy-table">
      <div className="table-row table-header">
        <div role="button" tabIndex={0} onClick={() => toggleSort('name')} onKeyDown={() => toggleSort('name')}>
          Name {sortKey === 'name' ? (ascending ? '↑' : '↓') : ''}
        </div>
        <div role="button" tabIndex={0} onClick={() => toggleSort('date')} onKeyDown={() => toggleSort('date')}>
          Date {sortKey === 'date' ? (ascending ? '↑' : '↓') : ''}
        </div>
        <div>Return</div>
        <div>Max drawdown</div>
        <div>Sharpe</div>
      </div>
      {sortedRows.map((row) => (
        <div className="table-row" key={row.name}>
          <div>{row.name}</div>
          <div>{row.date}</div>
          <div>{row.returnPct.toFixed(1)}%</div>
          <div>{row.maxDrawdownPct.toFixed(1)}%</div>
          <div>{row.sharpe.toFixed(1)}</div>
        </div>
      ))}
    </div>
  );
}
