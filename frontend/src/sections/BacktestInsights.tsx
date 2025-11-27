const backtests = [
  {
    name: 'Orion Momentum v5',
    cagr: '18.2%',
    maxDrawdown: '-6.4%',
    winRate: '58%',
    status: 'Ready to share',
  },
  {
    name: 'Aurora Mean Reversion',
    cagr: '11.4%',
    maxDrawdown: '-4.2%',
    winRate: '63%',
    status: 'Running...'
  },
];

const newsItems = [
  {
    title: 'Fed signals slower cuts; yields drift lower',
    time: '2h ago',
  },
  {
    title: 'TSMC highlights 2025 AI capacity commitments',
    time: '4h ago',
  },
  {
    title: 'House committee pushes new chip export guardrails',
    time: '6h ago',
  },
];

export function BacktestInsights() {
  return (
    <section className="backtest">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Performance transparency</p>
          <h2>Share backtest results with context</h2>
        </div>
        <button className="ghost-btn">Download PDF</button>
      </header>
      <div className="backtest-grid">
        <div className="backtest-cards">
          {backtests.map((run) => (
            <article key={run.name} className="backtest-card">
              <p className="eyebrow">{run.status}</p>
              <h3>{run.name}</h3>
              <dl>
                <div>
                  <dt>CAGR</dt>
                  <dd>{run.cagr}</dd>
                </div>
                <div>
                  <dt>Max DD</dt>
                  <dd>{run.maxDrawdown}</dd>
                </div>
                <div>
                  <dt>Win rate</dt>
                  <dd>{run.winRate}</dd>
                </div>
              </dl>
              <button className="primary-btn subtle">Send to client</button>
            </article>
          ))}
        </div>
        <div className="news-card">
          <p className="eyebrow">Linked news stream</p>
          <h3>Context your clients can trust</h3>
          <ul>
            {newsItems.map((item) => (
              <li key={item.title}>
                <p>{item.title}</p>
                <span>{item.time}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
