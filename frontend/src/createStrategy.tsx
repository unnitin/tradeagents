import React, { useMemo, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

type Ticker = { symbol: string; name: string; price: number; change: number };
type ChatEntry = { author: string; message: string; timestamp: string };
type CandlePoint = {
  date: string;
  price: number;
  sma: number;
  ema: number;
  bbUpper: number;
  bbLower: number;
};

const tickers: Ticker[] = [
  { symbol: 'AAPL', name: 'Apple', price: 191.22, change: 0.8 },
  { symbol: 'NVDA', name: 'NVIDIA', price: 872.11, change: -1.2 },
  { symbol: 'MSFT', name: 'Microsoft', price: 416.87, change: 0.4 },
];

const chatLog: ChatEntry[] = [
  { author: 'Client', message: 'Focus on AI infra names; keep drawdown under 8%.', timestamp: '09:10' },
  { author: 'Strategy Agent', message: 'Screening NVDA/MSFT/SMCI; testing EMA+vol breakout and news sentiment.', timestamp: '09:12' },
  { author: 'Risk Agent', message: 'Sharpe 1.7; max DD 6.2% on 3m backtest. Ready to review weights.', timestamp: '09:14' },
];

const featureFeed = [
  { label: 'EMA(10) > SMA(20)', detail: 'Momentum bias flagged on NVDA, MSFT' },
  { label: 'Volatility cooling', detail: '30d realized vol trending down for NVDA' },
  { label: 'Relative strength', detail: 'NVDA outperforming SOXX by 2.1% over 2w' },
];

const newsFeed = [
  { title: 'NVDA announces new inference chips', time: '08:55', impact: 'Positive sentiment 0.64' },
  { title: 'MSFT AI partnership update', time: '08:48', impact: 'Neutral to positive' },
  { title: 'SMCI supply-chain headline', time: '08:30', impact: 'Watch for follow-up' },
];

const priceSeries: CandlePoint[] = [
  { date: '2024-02-01', price: 118, sma: 117, ema: 116, bbUpper: 122, bbLower: 112 },
  { date: '2024-02-05', price: 121, sma: 118, ema: 117, bbUpper: 125, bbLower: 113 },
  { date: '2024-02-09', price: 124, sma: 120, ema: 119, bbUpper: 128, bbLower: 114 },
  { date: '2024-02-13', price: 123, sma: 121, ema: 120, bbUpper: 129, bbLower: 115 },
  { date: '2024-02-17', price: 127, sma: 122, ema: 122, bbUpper: 132, bbLower: 116 },
  { date: '2024-02-21', price: 131, sma: 124, ema: 124, bbUpper: 136, bbLower: 118 },
  { date: '2024-02-25', price: 129, sma: 125, ema: 125, bbUpper: 135, bbLower: 119 },
  { date: '2024-02-29', price: 134, sma: 127, ema: 127, bbUpper: 139, bbLower: 121 },
];

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function PriceChart({ series }: { series: CandlePoint[] }) {
  const [showSMA, setShowSMA] = useState(true);
  const [showEMA, setShowEMA] = useState(true);
  const [showBands, setShowBands] = useState(true);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const width = 900;
  const height = 260;
  const padding = 30;

  const values = series.flatMap((p) => [p.price, p.sma, p.ema, p.bbUpper, p.bbLower]);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);

  const scaleX = (index: number) => {
    if (series.length === 1) return width / 2;
    return padding + (index / (series.length - 1)) * (width - padding * 2);
  };
  const scaleY = (value: number) => {
    if (maxVal === minVal) return height / 2;
    return height - padding - ((value - minVal) / (maxVal - minVal)) * (height - padding * 2);
  };

  const toPath = (valuesArr: number[]) =>
    valuesArr
      .map((v, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(i).toFixed(2)} ${scaleY(v).toFixed(2)}`)
      .join(' ');

  const pricePath = useMemo(() => toPath(series.map((p) => p.price)), [series]);
  const smaPath = useMemo(() => toPath(series.map((p) => p.sma)), [series]);
  const emaPath = useMemo(() => toPath(series.map((p) => p.ema)), [series]);
  const upperPath = useMemo(() => toPath(series.map((p) => p.bbUpper)), [series]);
  const lowerPath = useMemo(() => toPath(series.map((p) => p.bbLower)), [series]);

  const bandAreaPath = useMemo(() => {
    if (!showBands) return '';
    const upperPoints = series.map((p, i) => `L ${scaleX(i).toFixed(2)} ${scaleY(p.bbUpper).toFixed(2)}`);
    const lowerPoints = [...series]
      .reverse()
      .map((p, i) => `L ${scaleX(series.length - 1 - i).toFixed(2)} ${scaleY(p.bbLower).toFixed(2)}`);
    const start = `M ${scaleX(0).toFixed(2)} ${scaleY(series[0].bbUpper).toFixed(2)}`;
    return `${start} ${upperPoints.slice(1).join(' ')} ${lowerPoints.join(' ')} Z`;
  }, [series, showBands]);

  const handleMove = (evt: React.MouseEvent<SVGSVGElement>) => {
    const rect = (evt.currentTarget as SVGSVGElement).getBoundingClientRect();
    const x = evt.clientX - rect.left - padding;
    const step = (width - padding * 2) / Math.max(series.length - 1, 1);
    const idx = clamp(Math.round(x / step), 0, series.length - 1);
    setHoverIndex(idx);
  };

  const hovered = hoverIndex !== null ? series[hoverIndex] : null;

  return (
    <div className="chart-card">
      <div className="card-header chart-toolbar">
        <div>
          <p className="eyebrow">Live signals</p>
          <h3>Price with SMA, EMA, and Bollinger Bands</h3>
        </div>
        <div className="legend toggle-group">
          <label className="legend-item price">
            <input type="checkbox" checked readOnly />
            Price
          </label>
          <label className="legend-item sma">
            <input type="checkbox" checked={showSMA} onChange={(e) => setShowSMA(e.target.checked)} />
            SMA
          </label>
          <label className="legend-item ema">
            <input type="checkbox" checked={showEMA} onChange={(e) => setShowEMA(e.target.checked)} />
            EMA
          </label>
          <label className="legend-item band">
            <input type="checkbox" checked={showBands} onChange={(e) => setShowBands(e.target.checked)} />
            Bollinger
          </label>
        </div>
      </div>
      <div className="chart-frame" onMouseLeave={() => setHoverIndex(null)}>
        <svg
          className="strategy-chart wide"
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          onMouseMove={handleMove}
        >
          {showBands && <path d={bandAreaPath} className="band-fill" />}
          {showBands && <path d={upperPath} className="band-line" />}
          {showBands && <path d={lowerPath} className="band-line" />}
          <path d={pricePath} className="price-line" />
          {showSMA && <path d={smaPath} className="sma-line" />}
          {showEMA && <path d={emaPath} className="ema-line" />}
          {series.map((pt, idx) => (
            <circle key={pt.date} cx={scaleX(idx)} cy={scaleY(pt.price)} r={3} className="price-dot" />
          ))}
          {hovered && (
            <>
              <line
                x1={scaleX(hoverIndex as number)}
                x2={scaleX(hoverIndex as number)}
                y1={padding}
                y2={height - padding}
                className="hover-line"
              />
              <circle cx={scaleX(hoverIndex as number)} cy={scaleY(hovered.price)} r={4} className="hover-dot" />
            </>
          )}
        </svg>
        {hovered && (
          <div className="chart-tooltip">
            <div className="tooltip-header">
              <strong>{hovered.price.toFixed(2)}</strong>
              <span>{hovered.date}</span>
            </div>
            <div className="tooltip-grid">
              {showSMA && (
                <div>
                  <span className="tooltip-label">SMA</span>
                  <span>{hovered.sma.toFixed(2)}</span>
                </div>
              )}
              {showEMA && (
                <div>
                  <span className="tooltip-label">EMA</span>
                  <span>{hovered.ema.toFixed(2)}</span>
                </div>
              )}
              {showBands && (
                <>
                  <div>
                    <span className="tooltip-label">Upper</span>
                    <span>{hovered.bbUpper.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="tooltip-label">Lower</span>
                    <span>{hovered.bbLower.toFixed(2)}</span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PriceTracker() {
  return (
    <div className="tracker">
      <div className="tracker-header">
        <div>
          <p className="eyebrow">Live price tracker</p>
          <h2>Watchlist & signals</h2>
        </div>
        <div className="ticker-actions">
          <input className="text-input" placeholder="Add ticker (e.g., AMZN)" aria-label="Add ticker" />
          <button className="ghost-btn small">Track</button>
        </div>
      </div>
      <div className="ticker-list">
        {tickers.map((t) => (
          <label key={t.symbol} className="ticker-chip">
            <input type="checkbox" defaultChecked aria-label={`Track ${t.symbol}`} />
            <div>
              <div className="chip-row">
                <span className="ticker-symbol">{t.symbol}</span>
                <span className="ticker-name">{t.name}</span>
              </div>
              <div className="chip-row">
                <span className="ticker-price">${t.price.toFixed(2)}</span>
                <span className={t.change >= 0 ? 'ticker-change up' : 'ticker-change down'}>
                  {t.change >= 0 ? '+' : ''}
                  {t.change.toFixed(1)}%
                </span>
              </div>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
}

function ChatPane() {
  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div>
          <p className="eyebrow">Strategy chat</p>
          <h3>Collaborate with agents & stakeholders</h3>
        </div>
        <button className="ghost-btn small">Export thread</button>
      </div>
      <div className="chat-log">
        {chatLog.map((entry) => (
          <div key={entry.timestamp + entry.message} className="chat-bubble">
            <span className="author">{entry.author}</span>
            <p>{entry.message}</p>
            <span className="timestamp">{entry.timestamp}</span>
          </div>
        ))}
      </div>
      <div className="chat-input">
        <input placeholder="Ask agents to adjust weights, run backtests, or fetch news" />
        <button className="primary-btn">Send</button>
      </div>
    </div>
  );
}

function FeedPane() {
  return (
    <div className="feed-grid">
      <article className="feed-card">
        <div className="feed-header">
          <p className="eyebrow">Data</p>
          <h3>Signals & features</h3>
        </div>
        <ul className="feed-list">
          {featureFeed.map((item) => (
            <li key={item.label}>
              <strong>{item.label}</strong>
              <span>{item.detail}</span>
            </li>
          ))}
        </ul>
      </article>
      <article className="feed-card">
        <div className="feed-header">
          <p className="eyebrow">News</p>
          <h3>Recent headlines</h3>
        </div>
        <ul className="feed-list">
          {newsFeed.map((item) => (
            <li key={item.title}>
              <strong>{item.title}</strong>
              <span>
                {item.time} · {item.impact}
              </span>
            </li>
          ))}
        </ul>
      </article>
    </div>
  );
}

function CreateStrategyLayout() {
  return (
    <div className="app-shell create-page">
      <header className="hero">
        <nav className="nav">
          <div className="logo" aria-label="TradeAgent Studio">
            <span className="logo-mark" aria-hidden>
              ∿
            </span>
            TradeAgent Studio
          </div>
          <div className="nav-links">
            {[
              { label: 'Home', href: '/' },
              { label: 'Dashboard', href: '/dashboard.html' },
              { label: 'Create Strategy', href: '/create-strategy.html' },
              { label: 'Backtest', href: '#' },
              { label: 'Manage Risk', href: '#' },
              { label: 'Notifications', href: '#' },
            ].map((item) => (
              <a key={item.label} href={item.href} className="nav-link">
                {item.label}
              </a>
            ))}
          </div>
          <button className="ghost-btn">Sign In</button>
        </nav>
        <div className="hero-content narrow">
          <p className="eyebrow">Design a strategy collaboratively</p>
          <h1>Create a strategy with live signals, data, and chat</h1>
          <p>
            Track tickers, discuss with agents, and review live signals and headlines—all in one workspace.
          </p>
        </div>
      </header>

      <div className="create-content">
        <PriceTracker />
        <PriceChart series={priceSeries} />
        <div className="pane-grid">
          <ChatPane />
          <FeedPane />
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <CreateStrategyLayout />
  </React.StrictMode>
);
