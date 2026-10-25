"use client";

import { ChangeEvent, useEffect, useState } from "react";
import {
  Bell, BriefcaseBusiness, ChevronDown, Database, Download, Globe2, LayoutDashboard,
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

const stockDirectory = [
  ["RELIANCE.NS", "Reliance Industries", "Energy"], ["TCS.NS", "Tata Consultancy Services", "Technology"],
  ["INFY.NS", "Infosys", "Technology"], ["HDFCBANK.NS", "HDFC Bank", "Financials"],
  ["ICICIBANK.NS", "ICICI Bank", "Financials"], ["SBIN.NS", "State Bank of India", "Financials"],
  ["ITC.NS", "ITC", "Consumer"], ["HINDUNILVR.NS", "Hindustan Unilever", "Consumer"],
  ["BHARTIARTL.NS", "Bharti Airtel", "Communication"], ["LT.NS", "Larsen & Toubro", "Industrials"],
  ["TATAMOTORS.NS", "Tata Motors", "Industrials"], ["MARUTI.NS", "Maruti Suzuki India", "Consumer"],
  ["AAPL", "Apple", "Technology"], ["MSFT", "Microsoft", "Technology"],
  ["GOOGL", "Alphabet", "Communication"], ["AMZN", "Amazon", "Consumer"],
  ["NVDA", "NVIDIA", "Technology"], ["TSLA", "Tesla", "Consumer"],
].map(([symbol, name, sector]) => ({ symbol, name, sector }));

async function searchLocalTop100(query: string): Promise<StockOption[]> {
  const response = await fetch("/equity_universe.csv");
  if (!response.ok) return [];
  const rows = (await response.text()).split(/\r?\n/).slice(1).filter(Boolean);
  const normalized = query.trim().toLowerCase();
  const showAll = normalized === "nse";
  return rows.map((line) => line.split(",")).map(([symbol, name]) => ({ symbol: `${symbol}.NS`, name, sector: "Other", exchange: "NSE" })).filter((stock) => showAll || `${stock.symbol} ${stock.name}`.toLowerCase().includes(normalized)).slice(0, 5000);
}

type Holding = typeof fallbackHoldings[number] & { quantity?: number; avg_buy_price?: number; buy_date?: string };
type PortfolioResponse = { holdings: Holding[]; summary: Record<string, any>; data_quality?: { status: string; available_count: number; unavailable_count: number; checked_at: string } };
type StockOption = { symbol: string; name: string; sector: string; exchange?: string };
type StockDetails = StockOption & { price?: number | null; change?: number; change_pct?: number; high?: number; low?: number; previous_close?: number; volume?: number; status: string };
type AuthUser = { id: string; email: string; display_name?: string | null };

function apiErrorMessage(body: any, fallback: string): string {
  if (typeof body?.detail === "string") return body.detail;
  if (Array.isArray(body?.detail)) return body.detail.map((item: any) => item?.msg || "Invalid input").join(", ");
  return fallback;
}

function uniqueStocks(stocks: StockOption[]): StockOption[] {
  return Array.from(new Map(stocks.map((stock) => [`${stock.symbol}|${stock.name}`, stock])).values());
}

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
  const [holdings, setHoldings] = useState<Holding[]>(fallbackHoldings);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [newHolding, setNewHolding] = useState({ symbol: "", name: "", sector: "Technology", quantity: "1", avg_buy_price: "100" });
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" ? `http://${window.location.hostname}:8000/api/portfolio` : "http://localhost:8000/api/portfolio");
  const [stockSearchQuery, setStockSearchQuery] = useState("");
  const [stockSuggestions, setStockSuggestions] = useState<StockOption[]>([]);
  const [stockSearchOpen, setStockSearchOpen] = useState(false);
  const [stockSearchField, setStockSearchField] = useState<"symbol" | "name" | null>(null);
  const [stockSearching, setStockSearching] = useState(false);
  const [stockDetails, setStockDetails] = useState<StockDetails | null>(null);
  const [stockDetailsLoading, setStockDetailsLoading] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authForm, setAuthForm] = useState({ email: "", password: "", display_name: "" });
  const [authError, setAuthError] = useState("");
  const [authNotice, setAuthNotice] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [emailVerificationSent, setEmailVerificationSent] = useState(false);
  const [verificationOtp, setVerificationOtp] = useState("");
  const [resetOtp, setResetOtp] = useState("");
  const [resetPassword, setResetPassword] = useState("");
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    if (!stockDetails) return;
    const timeout = window.setTimeout(() => setStockDetails(null), 5_000);
    return () => window.clearTimeout(timeout);
  }, [stockDetails]);

  useEffect(() => {
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/auth/me`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Not signed in")))
      .then((user) => setAuthUser(user))
      .catch(() => setAuthUser(null))
      .finally(() => setAuthChecked(true));
  }, [apiUrl]);

  useEffect(() => {
    if (!authUser) return;
    fetch(apiUrl, { credentials: "include" })
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
  }, [apiUrl, authUser]);

  useEffect(() => { if (portfolio?.holdings) setHoldings(portfolio.holdings); }, [portfolio]);

  useEffect(() => {
    if (!showAdd) { setStockSuggestions([]); return; }
    const query = stockSearchQuery.trim().toLowerCase();
    const searchTerm = query.length < 1 ? "nse" : stockSearchQuery;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setStockSearching(true);
      fetch(`${apiUrl.replace(/\/portfolio$/, "")}/stocks/search?q=${encodeURIComponent(searchTerm)}`, { signal: controller.signal })
        .then((response) => response.ok ? response.json() : Promise.reject(new Error("Search unavailable")))
        .then(async (data) => {
          const localMatches = stockDirectory.filter((stock) => `${stock.symbol} ${stock.name}`.toLowerCase().includes(query)).slice(0, 8);
          const localUniverse = await searchLocalTop100(searchTerm);
          setStockSuggestions(uniqueStocks(data.results?.length ? data.results : localUniverse.length ? localUniverse : localMatches));
        })
        .catch(async (error) => { if (error.name !== "AbortError") { const localUniverse = await searchLocalTop100(searchTerm); setStockSuggestions(uniqueStocks(localUniverse.length ? localUniverse : stockDirectory.filter((stock) => `${stock.symbol} ${stock.name}`.toLowerCase().includes(query)).slice(0, 8))); } })
        .finally(() => { if (!controller.signal.aborted) setStockSearching(false); });
    }, 180);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [apiUrl, showAdd, stockSearchQuery]);
  const summary = portfolio?.summary;
  const money = (value: number | null | undefined) => value == null ? "—" : `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  const exportCsv = () => {
    const rows = holdings.map((item) => [item.symbol, item.name, item.sector, item.quantity || 1, item.avg_buy_price || 0, item.buy_date || "", item.price, item.return, item.weight]);
    const csv = [["symbol", "name", "sector", "quantity", "avg_buy_price", "buy_date", "market_price", "return", "allocation"], ...rows].map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = "alphasage-portfolio.csv"; link.click(); URL.revokeObjectURL(url);
  };
  const importCsv = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; if (!file) return;
    file.text().then((text) => {
      const parsed = text.split(/\r?\n/).slice(1).filter(Boolean).map((line) => line.split(",").map((value) => value.replace(/^"|"$/g, ""))).filter((row) => row[0]).map((row) => ({ symbol: row[0], name: row[1] || row[0], sector: row[2] || "Unclassified", quantity: Number(row[3]) || 1, avg_buy_price: Number(row[4]) || 1, buy_date: row[5] || "", price: row[6] || "Unavailable", return: row[7] || "â€”", tone: row[7]?.startsWith("-") ? "negative" : "positive", weight: row[8] || "â€”" }));
      if (parsed.length) {
        setHoldings(parsed as Holding[]);
      fetch(`${apiUrl}/import`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ holdings: parsed.map(({ symbol, name, sector, quantity, avg_buy_price, buy_date }) => ({ symbol, name, sector, quantity, avg_buy_price, buy_date })) }) }).catch(() => undefined);
      }
    });
    event.target.value = "";
  };
  const addHolding = () => {
    if (!newHolding.symbol.trim() || !newHolding.name.trim()) return;
    const payload = { symbol: newHolding.symbol.trim().toUpperCase(), name: newHolding.name.trim(), sector: newHolding.sector, quantity: Number(newHolding.quantity), avg_buy_price: Number(newHolding.avg_buy_price), buy_date: new Date().toISOString().slice(0, 10) };
    if (!payload.quantity || !payload.avg_buy_price) return;
    fetch(`${apiUrl}/holdings`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }).then((response) => { if (!response.ok) throw new Error("Unable to save holding"); return response.json(); }).then((data) => { setPortfolio(data); setHoldings(data.holdings); setShowAdd(false); }).catch(() => setHoldings((current) => [...current, { ...payload, price: "Unavailable", return: "â€”", tone: "muted", weight: "â€”" }] as Holding[]));
    setNewHolding({ symbol: "", name: "", sector: "Technology", quantity: "1", avg_buy_price: "100" });
  };
  const selectStock = (value: string, field: "symbol" | "name") => {
    setStockSearchQuery(value);
    setStockSearchOpen(true);
    const search = value.trim().toLowerCase();
    const match = stockDirectory.find((stock) => stock[field].toLowerCase() === search);
    if (match) setNewHolding((current) => ({ ...current, symbol: match.symbol, name: match.name, sector: match.sector }));
    else setNewHolding((current) => ({ ...current, [field]: value }));
  };
  const chooseStock = (stock: StockOption) => {
    setNewHolding((current) => ({ ...current, symbol: stock.symbol, name: stock.name, sector: stock.sector || "Other" }));
    setStockDetailsLoading(true); setStockDetails(null);
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/stocks/details?symbol=${encodeURIComponent(stock.symbol)}`).then((response) => response.ok ? response.json() : Promise.reject(new Error("Details unavailable"))).then((data) => setStockDetails({ ...stock, ...data })).catch(() => setStockDetails({ ...stock, status: "Details unavailable" })).finally(() => setStockDetailsLoading(false));
    setStockSearchQuery(""); setStockSearchOpen(false);
  };
  const chooseCustomStock = () => {
    const value = stockSearchQuery.trim();
    if (!value) return;
    if (stockSearchField === "symbol") setNewHolding((current) => ({ ...current, symbol: value.toUpperCase(), name: current.name || value.toUpperCase(), sector: current.sector || "Other" }));
    else setNewHolding((current) => ({ ...current, name: value, symbol: current.symbol || value.toUpperCase(), sector: current.sector || "Other" }));
    setStockSearchOpen(false); setStockSearchQuery("");
  };
  const refreshPortfolio = () => { setRefreshing(true); window.location.reload(); };
  const removeHolding = (symbol: string) => {
    const encodedSymbol = encodeURIComponent(symbol);
    fetch(`${apiUrl}/holdings/${encodedSymbol}`, { method: "DELETE", credentials: "include" })
      .then((response) => response.ok ? response.json() : response.json().then((body) => Promise.reject(new Error(body.detail || "Unable to remove holding"))))
      .then((data) => { setPortfolio(data); setHoldings(data.holdings); })
      .catch((error) => window.alert(error.message || "Unable to remove holding"));
  };
  const submitAuth = () => {
    setAuthError("");
    if (authMode === "login" && (!authForm.email.trim() || !authForm.password)) {
      setAuthError("Enter login credentials");
      return;
    }
    const endpoint = authMode === "login" ? "/auth/login" : "/auth/register";
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}${endpoint}`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(authForm) })
      .then(async (response) => { const body = await response.json(); if (!response.ok) throw new Error(apiErrorMessage(body, "Authentication failed")); return body; })
      .then((user) => {
        if (authMode === "register") {
          setEmailVerificationSent(true);
          setAuthNotice("We sent a verification code to your email.");
        } else {
          setAuthUser(user);
          setShowAuth(false);
          setAuthForm({ email: "", password: "", display_name: "" });
        }
      })
      .catch((error) => setAuthError(error.message));
  };
  const verifyEmail = () => {
    setAuthError("");
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/auth/verify-email`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: authForm.email, otp: verificationOtp }) })
      .then(async (response) => { const body = await response.json(); if (!response.ok) throw new Error(body.detail || "Verification failed"); return body; })
      .then((user) => { setAuthUser(user); setEmailVerificationSent(false); setVerificationOtp(""); setAuthForm({ email: "", password: "", display_name: "" }); })
      .catch((error) => setAuthError(error.message));
  };
  const requestPasswordReset = (email: string) => {
    setAuthError("");
    setAuthNotice("");
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/auth/forgot-password`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) })
      .then(async (response) => { const body = await response.json(); if (!response.ok) throw new Error(body.detail || "Unable to send reset email"); return body; })
      .then((body) => setAuthNotice(body.message))
      .then(() => setOtpSent(true))
      .catch((error) => setAuthError(error.message));
  };
  const submitOtpReset = () => {
    setAuthError("");
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/auth/reset-password`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: authForm.email, otp: resetOtp, password: resetPassword }) })
      .then(async (response) => { const body = await response.json(); if (!response.ok) throw new Error(body.detail || "Invalid or expired OTP"); return body; })
      .then((body) => { setAuthNotice(body.message); setOtpSent(false); setResetOtp(""); setResetPassword(""); setAuthMode("login"); })
      .catch((error) => setAuthError(error.message));
  };
  const signOut = () => {
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/auth/logout`, { method: "POST", credentials: "include" })
      .finally(() => setAuthUser(null));
  };

  if (!authChecked || !authUser) {
    return <AuthGate mode={authMode} form={authForm} error={authError} notice={authNotice} otpSent={otpSent} emailVerificationSent={emailVerificationSent} otp={resetOtp} verificationOtp={verificationOtp} resetPassword={resetPassword} onOtpChange={setResetOtp} onVerificationOtpChange={setVerificationOtp} onResetPasswordChange={setResetPassword} onModeChange={(mode) => { setAuthMode(mode); setAuthError(""); setAuthNotice(""); setOtpSent(false); setEmailVerificationSent(false); }} onChange={setAuthForm} onSubmit={submitAuth} onForgot={requestPasswordReset} onOtpSubmit={submitOtpReset} onVerifyEmail={verifyEmail} onGoogle={() => { window.location.href = `${apiUrl.replace(/\/portfolio$/, "")}/auth/google/start`; }} />;
  }

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
          <span className="status-dot" /> {authUser ? authUser.display_name || authUser.email : "Guest workspace"}
          <p>{authUser ? "Your workspace is signed in and ready to sync." : "Sign in to sync your portfolio across devices."}</p>
          <button className="sign-in" onClick={() => { if (authUser) signOut(); else { setAuthMode("login"); setShowAuth(true); } }}>{authUser ? "Sign out" : "Sign in"} <ChevronDown size={14} /></button>
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
          <div className="header-actions"><button className="secondary" onClick={exportCsv}><Download size={16} /> Export CSV</button><label className="secondary file-button"><Upload size={16} /> Import CSV<input type="file" accept=".csv,text/csv" onChange={importCsv} /></label><button className="primary" onClick={() => setShowAdd(true)}><Plus size={17} /> Add holding</button></div>
        </div>

        <div className="disclaimer"><ShieldCheck size={16} /><span><strong>Research tool only.</strong> Market data may be delayed or incomplete. This is not financial advice.</span><button>Learn more</button></div>
        {portfolio?.data_quality && <div className={`data-status ${portfolio.data_quality.status}`}><span className="data-status-dot" /><strong>{portfolio.data_quality.status === "available" ? "Market data available" : portfolio.data_quality.status === "partial" ? "Some market data unavailable" : "Market data unavailable"}</strong><span>{portfolio.data_quality.available_count} of {holdings.length} prices available</span><time>{new Date(portfolio.data_quality.checked_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time></div>}

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

        <div className="section-heading"><div><div className="kicker">POSITIONS</div><h2>Holdings</h2></div><div className="section-actions"><button className="secondary compact" onClick={refreshPortfolio} disabled={refreshing}><LineChart size={15} /> {refreshing ? "Refreshing" : "Refresh prices"}</button><button className="secondary compact" onClick={() => setHoldings(fallbackHoldings)}>Try demo portfolio</button></div></div>

        <section className="holdings-card">
          <div className="table-toolbar"><div className="table-title">All positions <span>{holdings.length}</span></div><div className="table-tools"><button className="filter-button">All sectors <ChevronDown size={14} /></button><button className="icon-button"><Settings2 size={16} /></button></div></div>
          <div className="table-head"><span>Holding</span><span>Sector</span><span>Market price</span><span>Return</span><span>Allocation</span><span /></div>
          {holdings.map((holding, index) => <div className="holding-row" key={`${holding.symbol}-${holding.name}-${index}`}><div className="holding-name"><div className="ticker-icon">{holding.symbol.slice(0, 2)}</div><div><strong>{holding.name}</strong><small>{holding.symbol}</small></div></div><span className="muted">{holding.sector}</span><span className={holding.price === "Unavailable" ? "muted" : ""}>{holding.price}</span><span className={holding.tone}>{holding.return}</span><div className="allocation"><span>{holding.weight}</span><i><em style={{ width: holding.weight }} /></i></div><button className="row-menu" title={`Remove ${holding.name}`} aria-label={`Remove ${holding.name}`} onClick={() => removeHolding(holding.symbol)}>×</button></div>)}
        </section>
        {showAdd && <div className="modal-backdrop" onClick={() => { setShowAdd(false); setStockSearchOpen(false); }}><section className="add-modal" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><div className="kicker">PORTFOLIO ACTION</div><h2>Add holding</h2></div><button className="icon-button" onClick={() => setShowAdd(false)}>×</button></div><p className="modal-copy">Search live market instruments by typing a few letters. Select a result to fill the details automatically.</p><StockSearchField label="Symbol" value={newHolding.symbol} placeholder="Search symbol, e.g. AAPL" onChange={(value) => selectStock(value, "symbol")} onFocus={() => { setStockSearchField("symbol"); setStockSearchQuery(newHolding.symbol); setStockSearchOpen(true); }} open={stockSearchOpen && stockSearchField === "symbol"} suggestions={stockSuggestions} searching={stockSearching} onSelect={chooseStock} onCustom={chooseCustomStock} /><StockSearchField label="Company name" value={newHolding.name} placeholder="Search company name" onChange={(value) => selectStock(value, "name")} onFocus={() => { setStockSearchField("name"); setStockSearchQuery(newHolding.name); setStockSearchOpen(true); }} open={stockSearchOpen && stockSearchField === "name"} suggestions={stockSuggestions} searching={stockSearching} onSelect={chooseStock} onCustom={chooseCustomStock} /><div className="form-row"><label>Quantity<input type="number" min="0.01" step="0.01" value={newHolding.quantity} onChange={(event) => setNewHolding({ ...newHolding, quantity: event.target.value })} /></label><label>Average buy price<input type="number" min="0.01" step="0.01" value={newHolding.avg_buy_price} onChange={(event) => setNewHolding({ ...newHolding, avg_buy_price: event.target.value })} /></label></div><label>Sector<select value={newHolding.sector} onChange={(event) => setNewHolding({ ...newHolding, sector: event.target.value })}><option>Technology</option><option>Financials</option><option>Energy</option><option>Healthcare</option><option>Industrials</option><option>Consumer</option><option>Unclassified</option></select></label><div className="modal-actions"><button className="secondary" onClick={() => setShowAdd(false)}>Cancel</button><button className="primary" onClick={addHolding}>Add to portfolio</button></div></section></div>}
        {showAuth && <div className="modal-backdrop" onClick={() => setShowAuth(false)}><section className="add-modal auth-modal" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><div className="kicker">ALPHASAGE ACCOUNT</div><h2>{authMode === "login" ? "Welcome back" : "Create your account"}</h2></div><button className="icon-button" onClick={() => setShowAuth(false)}>×</button></div><p className="modal-copy">{authMode === "login" ? "Sign in to sync your portfolio and watchlists across devices." : "Create a secure workspace for your investment research."}</p>{authMode === "register" && <label>Display name<input value={authForm.display_name} onChange={(event) => setAuthForm({ ...authForm, display_name: event.target.value })} placeholder="Your name" /></label>}<label>Email<input type="email" value={authForm.email} onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })} placeholder="you@example.com" /></label><label>Password<input type="password" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} placeholder="At least 8 characters" /></label>{authError && <p className="auth-error">{authError}</p>}<div className="modal-actions"><button className="secondary" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "Create account" : "Sign in instead"}</button><button className="primary" onClick={submitAuth}>{authMode === "login" ? "Sign in" : "Create account"}</button></div></section></div>}
        </> : <WorkspacePage active={active} />}
      </section>
      {stockDetails && <StockPreview details={stockDetails} loading={stockDetailsLoading} />}
    </main>
  );
}

function AuthGate({ mode, form, error, notice, otpSent, emailVerificationSent, otp, verificationOtp, resetPassword, onOtpChange, onVerificationOtpChange, onResetPasswordChange, onModeChange, onChange, onSubmit, onForgot, onOtpSubmit, onVerifyEmail, onGoogle }: { mode: "login" | "register"; form: { email: string; password: string; display_name: string }; error: string; notice: string; otpSent: boolean; emailVerificationSent: boolean; otp: string; verificationOtp: string; resetPassword: string; onOtpChange: (value: string) => void; onVerificationOtpChange: (value: string) => void; onResetPasswordChange: (value: string) => void; onModeChange: (mode: "login" | "register") => void; onChange: (form: { email: string; password: string; display_name: string }) => void; onSubmit: () => void; onForgot: (email: string) => void; onOtpSubmit: () => void; onVerifyEmail: () => void; onGoogle: () => void }) {
  return <main className="auth-gate"><div className="auth-gate-glow" /><section className="auth-gate-card"><div className="brand auth-brand"><div className="brand-mark"><Sparkles size={18} /></div><div><strong>AlphaSage</strong><span>INVESTMENT INTELLIGENCE</span></div></div><div className="kicker">PRIVATE RESEARCH WORKSPACE</div><h1>{emailVerificationSent ? "Verify your email" : otpSent ? "Reset your password" : mode === "login" ? "Welcome back" : "Create your account"}</h1><p className="auth-gate-copy">{emailVerificationSent ? "Enter the 6-digit code sent to your email before continuing." : otpSent ? "Enter the 6-digit code sent to your email, then choose a new password." : mode === "login" ? "Sign in to access your portfolio, market research, and investment intelligence." : "Create a secure workspace to manage your portfolio and research across devices."}</p>{emailVerificationSent ? <><label>Verification code<input inputMode="numeric" maxLength={6} value={verificationOtp} onChange={(event) => onVerificationOtpChange(event.target.value)} placeholder="000000" /></label><button className="primary auth-submit" onClick={onVerifyEmail}>Verify email</button></> : otpSent ? <><label>One-time code<input inputMode="numeric" maxLength={6} value={otp} onChange={(event) => onOtpChange(event.target.value)} placeholder="000000" /></label><label>New password<input type="password" minLength={8} value={resetPassword} onChange={(event) => onResetPasswordChange(event.target.value)} placeholder="At least 8 characters" /></label><button className="primary auth-submit" onClick={onOtpSubmit}>Update password</button></> : <>{mode === "register" && <label>Display name<input value={form.display_name} onChange={(event) => onChange({ ...form, display_name: event.target.value })} placeholder="Your name" /></label>}<label>Email<input type="email" value={form.email} onChange={(event) => onChange({ ...form, email: event.target.value })} placeholder="you@example.com" /></label><label>Password<input type="password" value={form.password} onChange={(event) => onChange({ ...form, password: event.target.value })} placeholder="At least 8 characters" /></label><button className="primary auth-submit" onClick={onSubmit}>{mode === "login" ? "Sign in" : "Create secure account"}</button><button className="google-auth-button" onClick={onGoogle}>Continue with Google</button>{mode === "login" && <button className="forgot-link" onClick={() => onForgot(form.email)}>Forgot password?</button>}<button className="auth-switch" onClick={() => onModeChange(mode === "login" ? "register" : "login")}>{mode === "login" ? "New to AlphaSage? Create an account" : "Already have an account? Sign in"}</button></>}{error && <p className="auth-error">{error}</p>}{notice && <p className="auth-notice">{notice}</p>}<small className="auth-footnote">Your workspace is protected with secure session-based authentication.</small></section></main>;
}

function Metric({ label, value, detail, tone = "" }: { label: string; value: string; detail: string; tone?: string }) {
  return <article className="metric-card"><span>{label}</span><strong className={tone}>{value}</strong><small>{detail}</small></article>;
}
function Insight({ label, value, detail, tone = "" }: { label: string; value: string; detail: string; tone?: string }) {
  return <article className="insight-card"><span>{label}</span><strong className={tone}>{value}</strong><small className={tone}>{detail}</small></article>;
}

function StockPreview({ details, loading }: { details: StockDetails | null; loading: boolean }) {
  if (!details) return null;
  return <aside className="stock-preview"><div className="preview-heading"><div><span className="kicker">SELECTED INSTRUMENT</span><strong>{details.name}</strong><small>{details.symbol} · {details.exchange}</small></div><span className="preview-status">{loading ? "Loading" : details.status}</span></div><div className="preview-price">{details.price == null ? "Price unavailable" : `₹${details.price.toLocaleString("en-IN")}`} {details.change_pct != null && <small className={details.change_pct < 0 ? "negative" : "positive"}>{details.change_pct >= 0 ? "+" : ""}{details.change_pct.toFixed(2)}%</small>}</div><div className="preview-meta"><span>Sector<strong>{details.sector}</strong></span><span>Day high<strong>{details.high == null ? "—" : details.high}</strong></span><span>Day low<strong>{details.low == null ? "—" : details.low}</strong></span><span>Previous close<strong>{details.previous_close == null ? "—" : details.previous_close}</strong></span></div></aside>;
}

function StockSearchField({ label, value, placeholder, onChange, onFocus, open, suggestions, searching, onSelect, onCustom }: { label: string; value: string; placeholder: string; onChange: (value: string) => void; onFocus: () => void; open: boolean; suggestions: StockOption[]; searching: boolean; onSelect: (stock: StockOption) => void; onCustom: () => void }) {
  return <label className="stock-search-field">{label}<div className="stock-search-control"><Search size={15} /><input value={value} onChange={(event) => onChange(event.target.value)} onFocus={onFocus} placeholder={placeholder} />{searching && <span className="search-spinner" />}</div>{open && searching && <div className="stock-results search-status">Searching live instruments…</div>}{open && !searching && suggestions.length > 0 && <div className="stock-results">{suggestions.map((stock) => <button type="button" className="stock-result" key={`${stock.symbol}-${stock.name}`} onMouseDown={(event) => event.preventDefault()} onClick={() => onSelect(stock)}><span><strong>{stock.symbol}</strong><small>{stock.name}</small></span><em>{stock.exchange || stock.sector}</em></button>)}</div>}{open && !searching && value.length > 1 && suggestions.length === 0 && <div className="stock-results"><div className="empty-results">No live result yet</div><button type="button" className="stock-custom-result" onMouseDown={(event) => event.preventDefault()} onClick={onCustom}><strong>Use “{value}” as a custom instrument</strong><small>You can add any valid market symbol and update its details later.</small></button></div>}</label>;
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

