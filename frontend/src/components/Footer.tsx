export function Footer() {
  return (
    <footer className="footer">
      <p>© {new Date().getFullYear()} TradeAgent Studio</p>
      <div className="footer-links">
        <a href="#">Privacy</a>
        <a href="#">Security</a>
        <a href="#">Status</a>
      </div>
    </footer>
  );
}
