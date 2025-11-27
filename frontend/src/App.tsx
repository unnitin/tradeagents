import { HeroSection } from './sections/HeroSection';
import { StrategyWorkspace } from './sections/StrategyWorkspace';
import { DataHighlights } from './sections/DataHighlights';
import { BacktestInsights } from './sections/BacktestInsights';
import { Footer } from './components/Footer';

function App() {
  return (
    <div className="app-shell">
      <HeroSection />
      <StrategyWorkspace />
      <DataHighlights />
      <BacktestInsights />
      <Footer />
    </div>
  );
}

export default App;
