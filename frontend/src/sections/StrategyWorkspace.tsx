import { MessageCircle, PlayCircle, Sparkles, Workflow } from 'lucide-react';
import { clsx } from 'clsx';

const pipelineSteps = [
  {
    title: 'Ideate with Client',
    description: 'Summarize objectives, risk tolerance, and assets via chat threads.',
    icon: MessageCircle,
  },
  {
    title: 'Enrich Data',
    description: 'Pull fundamentals, news, and engineered features from the backend.',
    icon: Sparkles,
  },
  {
    title: 'Configure Strategies',
    description: 'Set agent roles, signals, execution rules, and guardrails.',
    icon: Workflow,
  },
  {
    title: 'Backtest & Share',
    description: 'Trigger multi-agent simulations and review outcomes with the client.',
    icon: PlayCircle,
  },
];

const chatLog = [
  {
    author: 'Client',
    message: 'Can we tilt toward AI infrastructure names and monitor earnings news?'
  },
  {
    author: 'News Agent',
    message: 'Flagged NVDA, AMD, and SMCI with positive coverage sentiment > 0.62 over the past 7 days.'
  },
  {
    author: 'Strategy Agent',
    message: 'Updated weights and reran EMA+vol breakout. Backtest ready with 18% annualized return.'
  }
];

export function StrategyWorkspace() {
  return (
    <section className="workspace">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Collaborative canvas</p>
          <h2>Coordinate agents, insights, and expertise</h2>
        </div>
        <button className="primary-btn subtle">Invite collaborators</button>
      </header>
      <div className="workspace-grid">
        <div className="pipeline">
          {pipelineSteps.map((step, index) => (
            <article key={step.title} className="pipeline-step">
              <div className={clsx('step-index', { active: index === 2 })}>{index + 1}</div>
              <div className="step-icon">
                <step.icon size={20} />
              </div>
              <div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
            </article>
          ))}
        </div>
        <div className="chat-panel">
          <div className="chat-header">
            <div>
              <p className="eyebrow">Strategy chat</p>
              <h3>Orion Momentum x News Sweep</h3>
            </div>
            <button className="ghost-btn small">Export thread</button>
          </div>
          <div className="chat-log">
            {chatLog.map((entry) => (
              <div key={entry.message} className="chat-bubble">
                <span className="author">{entry.author}</span>
                <p>{entry.message}</p>
              </div>
            ))}
          </div>
          <div className="chat-input">
            <input placeholder="Ask agents to run a backtest, fetch news, or summarize sentiment" />
            <button className="primary-btn">Send</button>
          </div>
        </div>
      </div>
    </section>
  );
}
