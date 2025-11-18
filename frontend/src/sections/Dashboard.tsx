import { useMemo, useState } from 'react';

type SeriesPoint = { date: string; price: number; indicator: number };
type NewsEvent = { date: string; label: string };

type Strategy = {
  name: string;
  date: string;
  priceSeries: SeriesPoint[];
  newsEvents: NewsEvent[];
  returnPct: number;
  maxDrawdownPct: number;
  sharpe: number;
};

const strategies: Strategy[] = [
  {
    name: 'Orion Momentum',
    date: '2024-03-15',
    priceSeries: [
      { date: '2024-01-02', price: 100, indicator: 98 },
      { date: '2024-01-08', price: 104, indicator: 101 },
      { date: '2024-01-15', price: 109, indicator: 105 },
      { date: '2024-01-22', price: 115, indicator: 110 },
      { date: '2024-01-29', price: 112, indicator: 111 },
      { date: '2024-02-05', price: 118, indicator: 114 },
      { date: '2024-02-12', price: 124, indicator: 120 },
      { date: '2024-02-19', price: 129, indicator: 124 },
      { date: '2024-02-26', price: 133, indicator: 126 },
      { date: '2024-03-04', price: 138, indicator: 130 },
    ],
    newsEvents: [
      { date: '2024-01-22', label: 'Earnings beat' },
      { date: '2024-02-12', label: 'AI partnership' },
    ],
    returnPct: 28.4,
    maxDrawdownPct: -6.1,
    sharpe: 1.9,
  },
  {
    name: 'Helios Signal Blend',
    date: '2024-02-10',
    priceSeries: [
      { date: '2024-01-02', price: 95, indicator: 96 },
      { date: '2024-01-08', price: 96, indicator: 97 },
      { date: '2024-01-15', price: 98, indicator: 98 },
      { date: '2024-01-22', price: 102, indicator: 101 },
      { date: '2024-01-29', price: 105, indicator: 103 },
      { date: '2024-02-05', price: 108, indicator: 105 },
      { date: '2024-02-12', price: 110, indicator: 108 },
      { date: '2024-02-19', price: 113, indicator: 110 },
      { date: '2024-02-26', price: 115, indicator: 111 },
      { date: '2024-03-04', price: 117, indicator: 113 },
    ],
    newsEvents: [
      { date: '2024-01-29', label: 'Regulation update' },
      { date: '2024-02-26', label: 'Sector rotation' },
    ],
    returnPct: 23.1,
    maxDrawdownPct: -4.8,
    sharpe: 1.6,
  },
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
  const indicators = series.map((p) => p.indicator);
  const allValues = [...prices, ...indicators];
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
      <path d={toPath(indicators)} className="indicator-line" />
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
      </header>

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
        <StrategyTable />
      </div>
    </section>
  );
}

type SortKey = 'name' | 'date';

function StrategyTable() {
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [ascending, setAscending] = useState<boolean>(true);

  const rows = useMemo(() => {
    const sorted = [...strategies];
    sorted.sort((a, b) => {
      if (sortKey === 'name') {
        return ascending ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
      }
      return ascending ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date);
    });
    return sorted;
  }, [sortKey, ascending]);

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
      {rows.map((row) => (
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
