const metrics = [
  {
    label: 'Signals online',
    value: '42',
    detail: 'Feature sets enriched in the last 24h',
  },
  {
    label: 'News pulses',
    value: '128',
    detail: 'Curated articles linked to tracked tickers',
  },
  {
    label: 'Pending backtests',
    value: '3',
    detail: 'Queued scenarios awaiting execution agent',
  },
];

const featureRows = [
  { ticker: 'NVDA', momentum: '+1.8σ', sentiment: '0.62', news: 'Earnings beat + AI GPU backlog' },
  { ticker: 'MSFT', momentum: '+0.7σ', sentiment: '0.55', news: 'Copilot integrations expanding' },
  { ticker: 'SMCI', momentum: '+2.2σ', sentiment: '0.71', news: 'Orders spike on hyperscaler demand' },
];

export function DataHighlights() {
  return (
    <section className="data-highlights">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Live market context</p>
          <h2>Blend engineered features, news signals, and trades</h2>
        </div>
        <button className="ghost-btn">View data catalog</button>
      </header>
      <div className="metrics">
        {metrics.map((metric) => (
          <article key={metric.label} className="metric-card">
            <p className="eyebrow">{metric.label}</p>
            <p className="metric-value">{metric.value}</p>
            <p>{metric.detail}</p>
          </article>
        ))}
      </div>
      <div className="feature-table">
        <div className="table-header">
          <span>Ticker</span>
          <span>Momentum (z)</span>
          <span>Sentiment</span>
          <span>Latest insight</span>
        </div>
        {featureRows.map((row) => (
          <div key={row.ticker} className="table-row">
            <span>{row.ticker}</span>
            <span>{row.momentum}</span>
            <span>{row.sentiment}</span>
            <span>{row.news}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
