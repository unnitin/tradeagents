export function HeroSection() {
  return (
    <header className="hero">
      <nav className="nav">
        <div className="logo">
          <span className="logo-mark" aria-hidden>∿</span>
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
      <div className="hero-content">
        <p className="eyebrow">Never miss a signal—call the best plays in real time</p>
        <h1>Your AI-Powered Trading Strategy Partner</h1>
        <p>
          Cutting edge AI, human experts, and real-time signals in one canvas. Chat with collaborators,
          synthesize news and technical analysis, and launch backtests without leaving the workspace.
        </p>
        <div className="hero-actions">
          <button className="primary-btn">Create New Strategy</button>
          <button className="ghost-btn">Schedule a Review</button>
        </div>
      </div>
    </header>
  );
}
