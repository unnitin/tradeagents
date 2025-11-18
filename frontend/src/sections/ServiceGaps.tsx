const gaps = [
  {
    title: 'Strategy + backtest orchestration',
    detail:
      'The backend currently exposes market data, feature creation, cache reads, and refresh jobs only. No endpoints exist for saving strategies, defining agents, or triggering/ranking backtests.',
  },
  {
    title: 'Chat + collaboration history',
    detail:
      'Conversation threads between clients and agents are purely front-end concepts today. Persistence, search, and notification plumbing must be built.',
  },
  {
    title: 'Auth & workspace scoping',
    detail:
      'Flask service has no authentication, authorization, or tenant scoping. Before shipping to clients we need token-based auth and RBAC across strategies/data.',
  },
  {
    title: 'Agent middleware',
    detail:
      'The system diagram assumes agent + middleware services to run automations. Those layers are not yet implemented; hooks should call placeholder APIs until defined.',
  },
];

export function ServiceGaps() {
  return (
    <section className="service-gaps">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Implementation notes</p>
          <h2>Backend scope gaps to address</h2>
        </div>
      </header>
      <div className="gaps-grid">
        {gaps.map((gap) => (
          <article key={gap.title} className="gap-card">
            <h3>{gap.title}</h3>
            <p>{gap.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
