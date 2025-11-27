import React from 'react';
import ReactDOM from 'react-dom/client';
import { Dashboard } from './sections/Dashboard';
import { Footer } from './components/Footer';
import './styles.css';

function DashboardPage() {
  return (
    <div className="app-shell">
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
      </header>
      <Dashboard />
      <Footer />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <DashboardPage />
  </React.StrictMode>
);
