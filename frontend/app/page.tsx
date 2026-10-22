"use client";

import { useEffect, useState } from "react";
import {
  Bell, Bot, BriefcaseBusiness, ChevronDown, Database, Download, Globe2, LayoutDashboard,
  LineChart, Newspaper, Plus, Search, Settings, Settings2, ShieldCheck, Sparkles,
  Upload, WalletCards, Watch
} from "lucide-react";

const fallbackHoldings = [
  { symbol: "RELIANCE.NS", name: "Reliance Industries", sector: "Energy", price: "₹1,174.60", return: "-51.06%", tone: "negative", weight: "28.4%" },
  { symbol: "TCS.NS", name: "Tata Consultancy Services", sector: "Technology", price: "₹2,304.90", return: "-34.15%", tone: "negative", weight: "22.1%" },
  { symbol: "INFY.NS", name: "Infosys", sector: "Technology", price: "₹1,088.00", return: "-24.97%", tone: "negative", weight: "19.8%" },
  { symbol: "HDFCBANK.NS", name: "HDFC Bank", sector: "Financials", price: "₹1,542.20", return: "-5.58%", tone: "negative", weight: "17.3%" },
  { symbol: "TATAMOTORS.NS", name: "Tata Motors", sector: "Industrials", price: "Unavailable", return: "—", tone: "muted", weight: "12.4%" }
];

type Holding = typeof fallbackHoldings[number];
type PortfolioResponse = { holdings: Holding[]; summary: Record<string, any> };

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard, group: "Platform" },
  { label: "Scanner", icon: Search, group: "Platform" },
  { label: "Global markets", icon: Globe2, group: "Markets" },
  { label: "Portfolio", icon: BriefcaseBusiness, group: "Markets", active: true },
  { label: "Watchlists", icon: Watch, group: "Markets" },
  { label: "News intelligence", icon: Newspaper, group: "Markets" },
  { label: "Blog", icon: Newspaper, group: "Markets" },
  { label: "Pricing", icon: WalletCards, group: "Account" },
  { label: "Data coverage", icon: Database, group: "Account" },
  { label: "Settings", icon: Settings, group: "Account" }
];

export default function Home() {
  const [active, setActive] = useState("Portfolio");
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/portfolio")
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("API unavailable")))
      .then((data) => {
        const total = data.summary.total_value || 0;
        setPortfolio({
          ...data,
          holdings: data.holdings.map((item: any) => ({
            ...item,
            price: item.current_price == null ? "Unavailable" : `₹${item.current_price.toLocaleString("en-IN")}`,
            return: item.pnl_pct == null ? "—" : `${item.pnl_pct.toFixed(2)}%`,
            tone: item.pnl_pct == null ? "muted" : item.pnl_pct < 0 ? "negative" : "positive",
            weight: item.current_value && total ? `${((item.current_value / total) * 100).toFixed(1)}%` : "—",
          }))
        });
      })
      .catch(() => setPortfolio(null))
      .finally(() => setLoading(false));
  }, []);

  const holdings = portfolio?.holdings || fallbackHoldings;
  const summary = portfolio?.summary;
  const money = (value: number | null | undefined) => value == null ? "—" : `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Sparkles size={18} /></div>
          <div><strong>AlphaSage</strong><span>INVESTMENT INTELLIGENCE</span></div>
        </div>

        <div className="sidebar-label">Platform</div>
        {navigation.map(({ label, icon: Icon, group, active: defaultActive }) => (
          <div key={label}>
            {(group === "Markets" && label === "Global markets") ||
            (group === "Account" && label === "Pricing") ? <div className="sidebar-label group-gap">{group}</div> : null}
            <button className={active === label || (defaultActive && active === "Portfolio") ? "nav-item active" : "nav-item"} onClick={() => setActive(label)}>
              <Icon size={17} /><span>{label}</span>
              {label === "AI research" && <span className="new-badge">NEW</span>}
            </button>
          </div>
        ))}

        <div className="sidebar-spacer" />
        <div className="early-access">
          <div className="eyebrow"><Sparkles size={14} /> EARLY ACCESS</div>
          <strong>Research with an edge.</strong>
          <p>Unlock cited AI analysis, portfolio risk signals, and market intelligence.</p>
          <button>Join the waitlist <ChevronDown size={14} /></button>
        </div>
        <div className="guest-card">
          <span className="status-dot" /> Guest workspace
          <p>Sign in to sync your portfolio across devices.</p>
          <button className="sign-in">Sign in <ChevronDown size={14} /></button>
        </div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div className="breadcrumbs"><span>{active === "Portfolio" ? "Markets" : "Workspace"}</span><b>/</b><strong>{active}</strong></div>
          <div className="top-actions"><button className="icon-button"><Bell size={17} /></button><button className="avatar">G</button></div>
        </header>

        {active === "Portfolio" ? <>
        <div className="page-header">
          <div><div className="kicker">PERSONAL WORKSPACE</div><h1>Portfolio</h1><p>Track holdings, understand exposure, and make better-informed decisions.</p></div>
          <div className="header-actions"><button className="secondary"><Download size={16} /> Export CSV</button><button className="secondary"><Upload size={16} /> Import CSV</button><button className="primary"><Plus size={17} /> Add holding</button></div>
        </div>

        <div className="disclaimer"><ShieldCheck size={16} /><span><strong>Research tool only.</strong> Market data may be delayed or incomplete. This is not financial advice.</span><button>Learn more</button></div>

        <section className="insight-hero">
          <div className="insight-copy"><div className="eyebrow"><Sparkles size={14} /> ALPHASAGE INTELLIGENCE</div><h2>Your portfolio, interpreted.</h2><p>Get a clear view of exposure, performance, and the signals that matter before you make your next decision.</p><button className="hero-action">Open AI research <LineChart size={15} /></button></div>
          <div className="pulse-panel"><div className="pulse-label">MARKET PULSE <span className="live-indicator" /> LIVE</div><div className="pulse-value">Markets are mixed</div><div className="pulse-bars"><i /><i /><i /><i /><i /><i /><i /></div><small>Based on your watchlist and portfolio exposure</small></div>
          <div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" />
        </section>

        <section className="metric-grid">
          <Metric label="Total value" value={money(summary?.total_value)} detail={loading ? "Loading market data" : "Updated from AlphaSage API"} />
          <Metric label="Total gain / loss" value={money(summary?.total_pnl)} detail="Since inception" tone="negative" />
          <Metric label="Portfolio return" value={summary?.return_pct == null ? "—" : `${summary.return_pct.toFixed(2)}%`} detail="Time-weighted return" tone="negative" />
          <Metric label="Est. annual dividends" value="—" detail="Awaiting corporate-action data" tone="muted" />
        </section>

        <section className="metric-grid intelligence">
          <Insight label="Best performer" value={summary?.best_performer?.name || "Infosys"} detail={summary?.best_performer?.pnl_pct == null ? "—" : `${summary.best_performer.pnl_pct.toFixed(2)}%`} />
          <Insight label="Worst performer" value={summary?.worst_performer?.name || "Reliance Industries"} detail={summary?.worst_performer?.pnl_pct == null ? "—" : `${summary.worst_performer.pnl_pct.toFixed(2)}%`} tone="negative" />
          <Insight label="Diversification score" value={summary?.diversification_score == null ? "—" : `${summary.diversification_score}/100`} detail="Calculated from current exposure" />
          <Insight label="Risk score" value={summary?.risk_score == null ? "—" : `${summary.risk_score}/100`} detail="Lower concentration is better" />
        </section>

        <div className="section-heading"><div><div className="kicker">POSITIONS</div><h2>Holdings</h2></div><button className="secondary compact"><LineChart size={15} /> Refresh prices</button></div>

        <section className="holdings-card">
          <div className="table-toolbar"><div className="table-title">All positions <span>{holdings.length}</span></div><div className="table-tools"><button className="filter-button">All sectors <ChevronDown size={14} /></button><button className="icon-button"><Settings2 size={16} /></button></div></div>
          <div className="table-head"><span>Holding</span><span>Sector</span><span>Market price</span><span>Return</span><span>Allocation</span><span /></div>
          {holdings.map((holding) => <div className="holding-row" key={holding.symbol}><div className="holding-name"><div className="ticker-icon">{holding.symbol.slice(0, 2)}</div><div><strong>{holding.name}</strong><small>{holding.symbol}</small></div></div><span className="muted">{holding.sector}</span><span className={holding.price === "Unavailable" ? "muted" : ""}>{holding.price}</span><span className={holding.tone}>{holding.return}</span><div className="allocation"><span>{holding.weight}</span><i><em style={{ width: holding.weight }} /></i></div><button className="row-menu">•••</button></div>)}
        </section>
        </> : <WorkspacePage active={active} />}
      </section>
    </main>
  );
}

function Metric({ label, value, detail, tone = "" }: { label: string; value: string; detail: string; tone?: string }) {
  return <article className="metric-card"><span>{label}</span><strong className={tone}>{value}</strong><small>{detail}</small></article>;
}
function Insight({ label, value, detail, tone = "" }: { label: string; value: string; detail: string; tone?: string }) {
  return <article className="insight-card"><span>{label}</span><strong className={tone}>{value}</strong><small className={tone}>{detail}</small></article>;
}

function WorkspacePage({ active }: { active: string }) {
  const copy: Record<string, { kicker: string; title: string; subtitle: string; action: string; items: [string, string, string][] }> = {
    Dashboard: { kicker: "MARKET OVERVIEW", title: "Good morning, investor.", subtitle: "A focused view of your portfolio, watchlist, and the market signals worth your attention.", action: "Customize dashboard", items: [["Portfolio pulse", "Your workspace is ready", "Connect holdings to unlock live insights."], ["Market breadth", "Mixed session", "Track indices, sectors, and global markets."], ["AI research", "Ask AlphaSage", "Get cited answers about companies and markets."]] },
    Scanner: { kicker: "DISCOVERY WORKSPACE", title: "Find your next signal.", subtitle: "Screen the market using momentum, valuation, quality, and risk factors.", action: "Create a screen", items: [["Momentum", "Coming soon", "Discover stocks showing relative strength."], ["Quality", "Coming soon", "Filter companies by durable fundamentals."], ["Risk", "Coming soon", "Identify volatility and drawdown patterns."]] },
    "Global markets": { kicker: "MARKET INTELLIGENCE", title: "Global markets.", subtitle: "See how major indices, currencies, commodities, and sectors are moving together.", action: "Explore markets", items: [["Equities", "Live coverage", "US, India, Europe, and Asia-Pacific indices."], ["Commodities", "Live coverage", "Energy, metals, and agricultural markets."], ["Macro calendar", "Coming soon", "Stay ahead of important economic releases."]] },
    Watchlists: { kicker: "PERSONAL WORKSPACE", title: "Watchlists.", subtitle: "Keep the companies and themes you care about one click away.", action: "Create watchlist", items: [["My watchlist", "0 symbols", "Add stocks to start tracking their signals."], ["Themes", "Coming soon", "Group companies by the ideas shaping markets."], ["Price alerts", "Coming soon", "Get notified when a level matters."]] },
    "News intelligence": { kicker: "RESEARCH FEED", title: "News intelligence.", subtitle: "Cut through the noise with market-moving headlines and source-aware summaries.", action: "Refresh feed", items: [["Market briefing", "AI-curated", "A concise overview of the day’s important stories."], ["Company news", "Source-aware", "Follow news for the companies in your workspace."], ["Sentiment", "Coming soon", "Understand tone, momentum, and narrative shifts."]] },
    Blog: { kicker: "ALPHASAGE INSIGHTS", title: "Research, explained.", subtitle: "Practical market education, product updates, and transparent investing workflows.", action: "Browse insights", items: [["Market notes", "Coming soon", "Clear explanations for complex market moves."], ["Product updates", "Coming soon", "See what is new across AlphaSage."], ["Learning center", "Coming soon", "Build better research habits over time."]] },
    Pricing: { kicker: "ALPHASAGE PLANS", title: "Research that scales with you.", subtitle: "Start with a focused workspace and unlock deeper intelligence as your needs grow.", action: "Join early access", items: [["Essential", "Free workspace", "Portfolio tracking and market discovery."], ["Pro", "Coming soon", "Cited AI research, alerts, and advanced analytics."], ["Teams", "Coming soon", "Shared research workflows for modern investors."]] },
    "Data coverage": { kicker: "DATA TRANSPARENCY", title: "Know your data.", subtitle: "Understand coverage, freshness, and the sources behind every AlphaSage insight.", action: "View coverage", items: [["Market prices", "Provider connected", "Prices may be delayed or unavailable for some symbols."], ["Fundamentals", "Expanding", "Company metrics will be added with source timestamps."], ["News sources", "Expanding", "Source-linked headlines and reports are on the roadmap."]] },
    Settings: { kicker: "WORKSPACE SETTINGS", title: "Make AlphaSage yours.", subtitle: "Manage your profile, notifications, data connections, and research preferences.", action: "Open preferences", items: [["Profile", "Guest workspace", "Sign in to sync your preferences across devices."], ["Notifications", "Not configured", "Choose how alerts and research updates reach you."], ["Data connections", "Local mode", "Connect supported brokers and data providers."]] }
  };
  const view = copy[active] || copy.Dashboard;
  return <>
    <div className="page-header"><div><div className="kicker">{view.kicker}</div><h1>{view.title}</h1><p>{view.subtitle}</p></div><button className="primary"><Plus size={17} /> {view.action}</button></div>
    <div className="disclaimer"><ShieldCheck size={16} /><span><strong>AlphaSage workspace.</strong> Features are being connected progressively with source-aware market data.</span></div>
    <section className="workspace-hero"><div><div className="eyebrow"><Sparkles size={14} /> BUILT FOR BETTER RESEARCH</div><h2>Clarity before conviction.</h2><p>AlphaSage brings your market context, portfolio signals, and research workflow into one calm workspace.</p></div><div className="workspace-ring"><Sparkles size={22} /><span>AI<br />READY</span></div></section>
    <section className="workspace-grid">{view.items.map(([label, value, detail]) => <article className="workspace-card" key={label}><div className="card-icon"><LineChart size={16} /></div><span>{label}</span><strong>{value}</strong><p>{detail}</p><button className="text-action">Explore <ChevronDown size={14} /></button></article>)}</section>
  </>;
}

