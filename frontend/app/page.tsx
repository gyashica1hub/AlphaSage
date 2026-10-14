"use client";

import { useState } from "react";
import {
  Bell, Bot, BriefcaseBusiness, ChevronDown, Database, Download, Globe2, LayoutDashboard,
  LineChart, Newspaper, Plus, Search, Settings, Settings2, ShieldCheck, Sparkles,
  Upload, WalletCards, Watch
} from "lucide-react";

const holdings = [
  { symbol: "RELIANCE.NS", name: "Reliance Industries", sector: "Energy", price: "₹1,174.60", return: "-51.06%", tone: "negative", weight: "28.4%" },
  { symbol: "TCS.NS", name: "Tata Consultancy Services", sector: "Technology", price: "₹2,304.90", return: "-34.15%", tone: "negative", weight: "22.1%" },
  { symbol: "INFY.NS", name: "Infosys", sector: "Technology", price: "₹1,088.00", return: "-24.97%", tone: "negative", weight: "19.8%" },
  { symbol: "HDFCBANK.NS", name: "HDFC Bank", sector: "Financials", price: "₹1,542.20", return: "-5.58%", tone: "negative", weight: "17.3%" },
  { symbol: "TATAMOTORS.NS", name: "Tata Motors", sector: "Industrials", price: "Unavailable", return: "—", tone: "muted", weight: "12.4%" }
];

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
          <div className="breadcrumbs"><span>Markets</span><b>/</b><strong>Portfolio</strong></div>
          <div className="top-actions"><button className="icon-button"><Bell size={17} /></button><button className="avatar">G</button></div>
        </header>

        <div className="page-header">
          <div><div className="kicker">PERSONAL WORKSPACE</div><h1>Portfolio</h1><p>Track holdings, understand exposure, and make better-informed decisions.</p></div>
          <div className="header-actions"><button className="secondary"><Download size={16} /> Export CSV</button><button className="secondary"><Upload size={16} /> Import CSV</button><button className="primary"><Plus size={17} /> Add holding</button></div>
        </div>

        <div className="disclaimer"><ShieldCheck size={16} /><span><strong>Research tool only.</strong> Market data may be delayed or incomplete. This is not financial advice.</span><button>Learn more</button></div>

        <section className="metric-grid">
          <Metric label="Total value" value="₹45,276" detail="Updated just now" />
          <Metric label="Total gain / loss" value="₹-47,774" detail="Since inception" tone="negative" />
          <Metric label="Portfolio return" value="-51.34%" detail="Time-weighted return" tone="negative" />
          <Metric label="Est. annual dividends" value="—" detail="Awaiting corporate-action data" tone="muted" />
        </section>

        <section className="metric-grid intelligence">
          <Insight label="Best performer" value="Infosys" detail="-24.97%" />
          <Insight label="Worst performer" value="Reliance Industries" detail="-51.06%" tone="negative" />
          <Insight label="Diversification score" value="67/100" detail="Moderately diversified" />
          <Insight label="Risk score" value="31/100" detail="Moderate concentration risk" />
        </section>

        <div className="section-heading"><div><div className="kicker">POSITIONS</div><h2>Holdings</h2></div><button className="secondary compact"><LineChart size={15} /> Refresh prices</button></div>

        <section className="holdings-card">
          <div className="table-toolbar"><div className="table-title">All positions <span>{holdings.length}</span></div><div className="table-tools"><button className="filter-button">All sectors <ChevronDown size={14} /></button><button className="icon-button"><Settings2 size={16} /></button></div></div>
          <div className="table-head"><span>Holding</span><span>Sector</span><span>Market price</span><span>Return</span><span>Allocation</span><span /></div>
          {holdings.map((holding) => <div className="holding-row" key={holding.symbol}><div className="holding-name"><div className="ticker-icon">{holding.symbol.slice(0, 2)}</div><div><strong>{holding.name}</strong><small>{holding.symbol}</small></div></div><span className="muted">{holding.sector}</span><span className={holding.price === "Unavailable" ? "muted" : ""}>{holding.price}</span><span className={holding.tone}>{holding.return}</span><div className="allocation"><span>{holding.weight}</span><i><em style={{ width: holding.weight }} /></i></div><button className="row-menu">•••</button></div>)}
        </section>
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

