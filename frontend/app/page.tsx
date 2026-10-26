"use client";

import { ChangeEvent, MouseEvent as ReactMouseEvent, PointerEvent, useEffect, useState } from "react";
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
type Transaction = { id: string; symbol: string; side: "BUY" | "SELL"; quantity: number; price: number; executed_at: string };
type Watchlist = { id: string; name: string };
type WatchlistItem = { id: string; symbol: string; created_at: string };
type MarketInstrument = { name: string; symbol: string; region: string; price?: number | null; change?: number; change_pct?: number | null; status: string };
type StockOption = { symbol: string; name: string; sector: string; exchange?: string };
type StockHistoryPoint = { date: string; open?: number; high?: number; low?: number; close: number };
type StockDetails = StockOption & { price?: number | null; change?: number; change_pct?: number; high?: number; low?: number; previous_close?: number; volume?: number; status: string; provider?: string | null; data_status?: "fresh" | "unavailable"; fetched_at?: string; history_quality?: { points: number; invalid_points: number; duplicate_dates: number; status: string }; corporate_actions?: { date: string; type: string; value: number }[]; purchase_price?: number | null; history?: StockHistoryPoint[]; intraday_history?: StockHistoryPoint[]; benchmark?: StockHistoryPoint[]; benchmark_symbol?: string; stock_return_pct?: number | null; benchmark_return_pct?: number | null; indicators?: { sma_20?: number | null; ema_20?: number | null; rsi_14?: number | null }; forecast?: { status: string; method?: string; forecast?: number; lower_bound?: number; upper_bound?: number }; forecast_validation?: { status: string; test_points?: number; directional_accuracy?: number; strategy_return_pct?: number; buy_hold_return_pct?: number }; fundamentals?: { market_cap?: number | null; pe_ratio?: number | null; dividend_yield?: number | null; week52_high?: number | null; week52_low?: number | null } };
type AuthUser = { id: string; email: string; display_name?: string | null };
type AlertRule = { id: string; symbol: string; rule: string; threshold: number; cooldown_minutes: number; last_triggered_at?: string | null; active: boolean };
type AlertDelivery = { id: string; symbol?: string; channel: string; status: string; message: string; error?: string | null; created_at: string };
type RiskMetric = { symbol: string; status: string; observations?: number; volatility?: number; max_drawdown?: number; downside_deviation?: number };

function apiErrorMessage(body: any, fallback: string): string {
  if (typeof body?.detail === "string") return body.detail;
  if (Array.isArray(body?.detail)) return body.detail.map((item: any) => item?.msg || "Invalid input").join(", ");
  return fallback;
}

function uniqueStocks(stocks: StockOption[]): StockOption[] {
  return Array.from(new Map(stocks.map((stock) => [`${stock.symbol}|${stock.name}`, stock])).values());
}

function formatMarketPointDate(value: string): string {
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (dateOnly) {
    const [, year, month, day] = dateOnly;
    return new Date(Number(year), Number(month) - 1, Number(day)).toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
  }
  return new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard, group: "Platform" },
  { label: "Scanner", icon: Search, group: "Platform" },
  { label: "Global markets", icon: Globe2, group: "Markets" },
  { label: "Portfolio", icon: BriefcaseBusiness, group: "Markets", active: true },
  { label: "Watchlists", icon: Watch, group: "Markets" },
  { label: "Alerts", icon: Bell, group: "Markets" },
  { label: "News intelligence", icon: Newspaper, group: "Markets" },
  { label: "Blog", icon: Newspaper, group: "Markets" },
  { label: "Pricing", icon: WalletCards, group: "Account" },
  { label: "Data coverage", icon: Database, group: "Account" },
  { label: "Settings", icon: Settings, group: "Account" }
];

export default function Home() {
  const [active, setActive] = useState("Portfolio");
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [transactionForm, setTransactionForm] = useState({ symbol: "", side: "BUY" as "BUY" | "SELL", quantity: "1", price: "100", executed_at: new Date().toISOString().slice(0, 10) });
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItem[]>([]);
  const [watchlistQuotes, setWatchlistQuotes] = useState<Record<string, StockDetails>>({});
  const [watchlistRefreshing, setWatchlistRefreshing] = useState(false);
  const [marketInstruments, setMarketInstruments] = useState<MarketInstrument[]>([]);
  const [marketsLoading, setMarketsLoading] = useState(false);
  const [marketRefreshKey, setMarketRefreshKey] = useState(0);
  const [selectedMarket, setSelectedMarket] = useState<StockDetails | null>(null);
  const [selectedMarketLoading, setSelectedMarketLoading] = useState(false);
  const [watchlistSymbol, setWatchlistSymbol] = useState("");
  const [watchlistName, setWatchlistName] = useState("My watchlist");
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
  const [stockDetailsPinned, setStockDetailsPinned] = useState(false);
  const [stockDetailsExpanded, setStockDetailsExpanded] = useState(false);
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
  const [pageRestored, setPageRestored] = useState(false);
  const [alerts, setAlerts] = useState<AlertRule[]>([]);
  const [alertForm, setAlertForm] = useState({ symbol: "RELIANCE.NS", rule: "price_above", threshold: "1000", cooldown_minutes: "60" });
  const [alertMessage, setAlertMessage] = useState("");
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [bellOpen, setBellOpen] = useState(false);
  const [deliveries, setDeliveries] = useState<AlertDelivery[]>([]);
  const [deliveriesLoading, setDeliveriesLoading] = useState(false);
  const [browserNotifications, setBrowserNotifications] = useState(false);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetric[]>([]);
  const [riskMetricsLoading, setRiskMetricsLoading] = useState(false);

  useEffect(() => {
    if (!stockDetails || stockDetailsPinned) return;
    const timeout = window.setTimeout(() => setStockDetails(null), 5_000);
    return () => window.clearTimeout(timeout);
  }, [stockDetails, stockDetailsPinned]);

  useEffect(() => {
    if (!stockSearchOpen) return;
    const closeOnOutsideClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest(".stock-search-field")) {
        setStockSearchOpen(false);
        setStockSearchField(null);
      }
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, [stockSearchOpen]);

  useEffect(() => {
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/auth/me`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Not signed in")))
      .then((user) => setAuthUser(user))
      .catch(() => setAuthUser(null))
      .finally(() => setAuthChecked(true));
  }, [apiUrl]);

  useEffect(() => {
    if (!authUser) {
      setPageRestored(false);
      return;
    }
    const savedPage = window.localStorage.getItem(`alphasage_active_page_${authUser.id}`);
    setActive(savedPage && navigation.some((item) => item.label === savedPage) ? savedPage : "Portfolio");
    setPageRestored(true);
  }, [authUser]);

  useEffect(() => {
    if (authUser) window.localStorage.setItem(`alphasage_active_page_${authUser.id}`, active);
  }, [active, authUser]);

  useEffect(() => {
    if (!authUser || active !== "Alerts") return;
    setAlertsLoading(true);
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/alerts`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Unable to load alerts")))
      .then((data: AlertRule[]) => setAlerts(data))
      .catch(() => setAlerts([]))
      .finally(() => setAlertsLoading(false));
  }, [active, apiUrl, authUser]);

  const createAlert = () => {
    setAlertMessage("");
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/alerts`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ symbol: alertForm.symbol.trim().toUpperCase(), rule: alertForm.rule, threshold: Number(alertForm.threshold), cooldown_minutes: Number(alertForm.cooldown_minutes) }) })
      .then((response) => response.ok ? response.json() : response.json().then((body) => Promise.reject(new Error(body.detail || "Unable to create alert"))))
      .then((created: AlertRule) => { setAlerts((current) => [created, ...current]); setAlertMessage("Alert created successfully."); })
      .catch((error) => setAlertMessage(error.message));
  };

  const evaluateAlerts = () => {
    setAlertMessage("Checking current market prices…");
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/alerts/evaluate`, { method: "POST", credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Unable to evaluate alerts")))
      .then((data) => { const triggered = data.results?.filter((result: { status: string }) => result.status === "sent" || result.status === "evaluated") || []; if (browserNotifications && triggered.length && "Notification" in window && Notification.permission === "granted") new Notification("AlphaSage alert", { body: triggered[0].message }); setAlertMessage(`${data.results?.length || 0} alert condition(s) evaluated. Check your email if a rule was triggered.`); })
      .catch((error) => setAlertMessage(error.message));
  };

  const enableBrowserNotifications = () => {
    if (!("Notification" in window)) { setAlertMessage("Browser notifications are not supported here."); return; }
    Notification.requestPermission().then((permission) => { setBrowserNotifications(permission === "granted"); setAlertMessage(permission === "granted" ? "Browser notifications enabled." : "Browser notifications were not enabled."); });
  };

  const removeAlert = (id: string) => {
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/alerts/${encodeURIComponent(id)}`, { method: "DELETE", credentials: "include" })
      .then((response) => response.ok ? setAlerts((current) => current.filter((alert) => alert.id !== id)) : Promise.reject(new Error("Unable to remove alert")))
      .catch((error) => setAlertMessage(error.message));
  };

  const fetchDeliveries = () => {
    setDeliveriesLoading(true);
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/alerts/deliveries`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Unable to load notifications")))
      .then((data: AlertDelivery[]) => setDeliveries(data))
      .catch(() => setDeliveries([]))
      .finally(() => setDeliveriesLoading(false));
  };

  const loadDeliveries = () => {
    setBellOpen((open) => !open);
    if (!bellOpen) fetchDeliveries();
  };

  useEffect(() => {
    if (!authUser) return;
    fetchDeliveries();
    const timer = window.setInterval(fetchDeliveries, 30000);
    return () => window.clearInterval(timer);
  }, [authUser]);

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

  useEffect(() => {
    if (!authUser || active !== "Portfolio") return;
    const baseUrl = apiUrl.replace(/\/portfolio$/, "");
    setRiskMetricsLoading(true);
    fetch(`${baseUrl}/portfolio/risk`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Risk data unavailable")))
      .then((data) => setRiskMetrics(data.metrics || []))
      .catch(() => setRiskMetrics([]))
      .finally(() => setRiskMetricsLoading(false));
  }, [active, apiUrl, authUser]);

  useEffect(() => {
    if (!watchlistItems.length) { setWatchlistQuotes({}); return; }
    const baseUrl = apiUrl.replace(/\/portfolio$/, "");
    Promise.all(watchlistItems.map((item) => fetch(`${baseUrl}/stocks/details?symbol=${encodeURIComponent(item.symbol)}`).then((response) => response.ok ? response.json() : Promise.reject(new Error("Quote unavailable"))).then((quote) => ({ ...quote, symbol: item.symbol } as StockDetails)).catch(() => ({ symbol: item.symbol, name: item.symbol, sector: "Other", status: "Price unavailable" }))))
      .then((quotes) => setWatchlistQuotes(Object.fromEntries(quotes.map((quote) => [quote.symbol, quote]))));
  }, [apiUrl, watchlistItems]);

  useEffect(() => {
    if (!authUser) return;
    const baseUrl = apiUrl.replace(/\/portfolio$/, "");
    fetch(`${baseUrl}/watchlists`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Unable to load watchlists")))
      .then((data: Watchlist[]) => { setWatchlists(data); if (data[0]) return fetch(`${baseUrl}/watchlists/${data[0].id}/items`, { credentials: "include" }).then((response) => response.json()); return []; })
      .then((items: WatchlistItem[]) => setWatchlistItems(items))
      .catch(() => { setWatchlists([]); setWatchlistItems([]); });
  }, [apiUrl, authUser]);

  useEffect(() => {
    if (!authUser) return;
    fetch(`${apiUrl}/transactions`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Unable to load transactions")))
      .then((data) => setTransactions(data))
      .catch(() => setTransactions([]));
  }, [apiUrl, authUser]);

  useEffect(() => { if (portfolio?.holdings) setHoldings(portfolio.holdings); }, [portfolio]);

  useEffect(() => {
    if (!showAdd && active !== "Watchlists" && stockSearchField !== "symbol") { setStockSuggestions([]); return; }
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
  }, [active, apiUrl, showAdd, stockSearchField, stockSearchQuery]);
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
    setStockDetailsPinned(false); setStockDetailsExpanded(false); setStockDetailsLoading(true); setStockDetails(null);
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/stocks/dashboard?symbol=${encodeURIComponent(stock.symbol)}`).then((response) => response.ok ? response.json() : Promise.reject(new Error("Details unavailable"))).then((data) => setStockDetails({ ...stock, ...data, purchase_price: Number(newHolding.avg_buy_price) || null })).catch(() => setStockDetails({ ...stock, status: "Details unavailable", purchase_price: Number(newHolding.avg_buy_price) || null })).finally(() => setStockDetailsLoading(false));
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
  const addTransaction = () => {
    const payload = { symbol: transactionForm.symbol.trim().toUpperCase(), side: transactionForm.side, quantity: Number(transactionForm.quantity), price: Number(transactionForm.price), executed_at: new Date(`${transactionForm.executed_at}T00:00:00`).toISOString() };
    if (!payload.symbol || payload.quantity <= 0 || payload.price < 0) return;
    fetch(`${apiUrl}/transactions`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      .then((response) => response.ok ? response.json() : response.json().then((body) => Promise.reject(new Error(apiErrorMessage(body, "Unable to add transaction")))))
      .then(() => fetch(`${apiUrl}/transactions`, { credentials: "include" }))
      .then((response) => response.json())
      .then((data) => { setTransactions(data); window.location.reload(); });
  };
  const removeTransaction = (id: string) => {
    fetch(`${apiUrl}/transactions/${id}`, { method: "DELETE", credentials: "include" })
      .then((response) => response.ok ? setTransactions((current) => current.filter((item) => item.id !== id)) : Promise.reject(new Error("Unable to remove transaction")));
  };
  const createWatchlist = () => {
    const name = watchlistName.trim();
    if (!name) return;
    const baseUrl = apiUrl.replace(/\/portfolio$/, "");
    fetch(`${baseUrl}/watchlists`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) })
      .then((response) => response.json()).then((watchlist) => { setWatchlists((current) => [...current, watchlist]); setWatchlistName(""); });
  };
  const addWatchlistSymbol = () => {
    const symbol = watchlistSymbol.trim().toUpperCase();
    const watchlist = watchlists[0];
    if (!symbol || !watchlist) return;
    const baseUrl = apiUrl.replace(/\/portfolio$/, "");
    fetch(`${baseUrl}/watchlists/${watchlist.id}/items`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ symbol }) })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Symbol already exists")))
      .then((item) => { setWatchlistItems((current) => [...current, { ...item, created_at: new Date().toISOString() }]); setWatchlistSymbol(""); });
  };
  const chooseWatchlistStock = (stock: StockOption) => {
    setWatchlistSymbol(stock.symbol);
    setStockSearchQuery("");
    setStockSearchOpen(false);
  };
  const viewWatchlistStock = (symbol: string, name: string) => {
    setStockDetailsPinned(true);
    setStockDetailsExpanded(false);
    setStockDetailsLoading(true);
    const purchased = holdings.find((holding) => holding.symbol === symbol)?.avg_buy_price;
    setStockDetails({ symbol, name, sector: "Other", status: "Loading", purchase_price: purchased ?? null });
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/stocks/dashboard?symbol=${encodeURIComponent(symbol)}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Details unavailable")))
      .then((data) => setStockDetails({ symbol, name: data.name || name, sector: data.sector || "Other", purchase_price: purchased ?? null, ...data }))
      .catch(() => setStockDetails({ symbol, name, sector: "Other", status: "Details unavailable", purchase_price: purchased ?? null }))
      .finally(() => setStockDetailsLoading(false));
  };
  const chooseTransactionStock = (stock: StockOption) => {
    setTransactionForm((current) => ({ ...current, symbol: stock.symbol }));
    setStockSearchQuery("");
    setStockSearchOpen(false);
  };
  const removeWatchlistSymbol = (symbol: string) => {
    const watchlist = watchlists[0];
    if (!watchlist) return;
    const baseUrl = apiUrl.replace(/\/portfolio$/, "");
    fetch(`${baseUrl}/watchlists/${watchlist.id}/items/${encodeURIComponent(symbol)}`, { method: "DELETE", credentials: "include" }).then(() => setWatchlistItems((current) => current.filter((item) => item.symbol !== symbol)));
  };
  const refreshWatchlistQuotes = () => {
    setWatchlistRefreshing(true);
    const baseUrl = apiUrl.replace(/\/portfolio$/, "");
    Promise.all(watchlistItems.map((item) => fetch(`${baseUrl}/stocks/refresh?symbol=${encodeURIComponent(item.symbol)}`, { method: "POST" }).then((response) => response.ok ? response.json() : Promise.reject(new Error("Quote unavailable"))).then((quote) => ({ ...quote, symbol: item.symbol } as StockDetails)).catch(() => ({ symbol: item.symbol, name: item.symbol, sector: "Other", status: "Price unavailable" }))))
      .then((quotes) => setWatchlistQuotes(Object.fromEntries(quotes.map((quote) => [quote.symbol, quote]))))
      .finally(() => setWatchlistRefreshing(false));
  };
  useEffect(() => {
    if (active !== "Global markets") return;
    setMarketsLoading(true);
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/market-overview`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Market overview unavailable")))
      .then((data) => setMarketInstruments(data))
      .catch(() => setMarketInstruments([]))
      .finally(() => setMarketsLoading(false));
  }, [active, apiUrl, marketRefreshKey]);
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

  const openMarketDetails = (instrument: MarketInstrument) => {
    setSelectedMarketLoading(true);
    setSelectedMarket({ symbol: instrument.symbol, name: instrument.name, sector: instrument.region, status: "Loading" });
    fetch(`${apiUrl.replace(/\/portfolio$/, "")}/stocks/dashboard?symbol=${encodeURIComponent(instrument.symbol)}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Market details unavailable")))
      .then((data) => setSelectedMarket({ symbol: instrument.symbol, ...data, name: instrument.name, sector: instrument.region }))
      .catch(() => setSelectedMarket({ symbol: instrument.symbol, name: instrument.name, sector: instrument.region, status: "Details unavailable" }))
      .finally(() => setSelectedMarketLoading(false));
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

  if (!authChecked || (authUser && !pageRestored)) {
    return <LoadingScreen />;
  }

  if (!authUser) {
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
          <div className="top-actions"><div className="notification-wrap"><button className={`icon-button${bellOpen ? " active" : ""}`} onClick={loadDeliveries} aria-label="Open notifications"><Bell size={17} /></button>{bellOpen && <div className="notification-popover"><div className="notification-header"><strong>Notifications</strong><small>Alert activity</small></div>{deliveriesLoading ? <div className="notification-empty">Loading notifications…</div> : deliveries.length === 0 ? <div className="notification-empty">No alert activity yet.</div> : <div className="notification-list">{deliveries.slice(0, 8).map((delivery) => <div className="notification-item" key={delivery.id}><span className={`notification-status ${delivery.status}`} /> <div><strong>{delivery.message}</strong><small>{delivery.status} · {new Date(delivery.created_at).toLocaleString()}</small></div></div>)}</div>}<button className="notification-link" onClick={() => { setBellOpen(false); setActive("Alerts"); }}>Open Alerts</button></div>}</div><button className="avatar">G</button></div>
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

        <section className="activity-section risk-metrics-section"><div className="section-heading activity-heading"><div><div className="kicker">HISTORICAL RISK</div><h2>Risk by holding</h2></div><span>{riskMetricsLoading ? "Loading…" : "6 month history"}</span></div>{riskMetrics.length === 0 ? <div className="activity-empty">Historical risk metrics will appear when price history is available.</div> : <div className="risk-metrics-grid">{riskMetrics.map((metric) => <article className="risk-metric-card" key={metric.symbol}><strong>{metric.symbol}</strong>{metric.status === "ok" ? <><span>Volatility <b>{((metric.volatility || 0) * 100).toFixed(1)}%</b></span><span>Max drawdown <b className="negative">-{((metric.max_drawdown || 0) * 100).toFixed(1)}%</b></span><span>Downside deviation <b>{((metric.downside_deviation || 0) * 100).toFixed(1)}%</b></span></> : <small>Price history unavailable</small>}</article>)}</div>}</section>

        <div className="section-heading"><div><div className="kicker">POSITIONS</div><h2>Holdings</h2></div><div className="section-actions"><button className="secondary compact" onClick={refreshPortfolio} disabled={refreshing}><LineChart size={15} /> {refreshing ? "Refreshing" : "Refresh prices"}</button><button className="secondary compact" onClick={() => setHoldings(fallbackHoldings)}>Try demo portfolio</button></div></div>

        <section className="holdings-card">
          <div className="table-toolbar"><div className="table-title">All positions <span>{holdings.length}</span></div><div className="table-tools"><button className="filter-button">All sectors <ChevronDown size={14} /></button><button className="icon-button"><Settings2 size={16} /></button></div></div>
          <div className="table-head"><span>Holding</span><span>Sector</span><span>Market price</span><span>Return</span><span>Allocation</span><span /></div>
          {holdings.map((holding, index) => <div className="holding-row" key={`${holding.symbol}-${holding.name}-${index}`}><div className="holding-name"><div className="ticker-icon">{holding.symbol.slice(0, 2)}</div><div><strong>{holding.name}</strong><small>{holding.symbol}</small></div></div><span className="muted">{holding.sector}</span><span className={holding.price === "Unavailable" ? "muted" : ""}>{holding.price}</span><span className={holding.tone}>{holding.return}</span><div className="allocation"><span>{holding.weight}</span><i><em style={{ width: holding.weight }} /></i></div><button className="row-menu" title={`Remove ${holding.name}`} aria-label={`Remove ${holding.name}`} onClick={() => removeHolding(holding.symbol)}>×</button></div>)}
        </section>
        <section className="activity-section"><div className="section-heading activity-heading"><div><div className="kicker">PORTFOLIO ACTIVITY</div><h2>Transaction history</h2></div></div><div className="transaction-form"><StockSearchField label="" value={transactionForm.symbol} placeholder="Search symbol or company" onChange={(value) => { setTransactionForm({ ...transactionForm, symbol: value }); setStockSearchQuery(value); setStockSearchField("symbol"); setStockSearchOpen(true); }} onFocus={() => { setStockSearchField("symbol"); setStockSearchQuery(transactionForm.symbol); setStockSearchOpen(true); }} open={stockSearchOpen && stockSearchField === "symbol" && !showAdd} suggestions={stockSuggestions} searching={stockSearching} onSelect={chooseTransactionStock} onCustom={() => { setTransactionForm({ ...transactionForm, symbol: stockSearchQuery.toUpperCase() }); setStockSearchOpen(false); }} /><select aria-label="Transaction side" value={transactionForm.side} onChange={(event) => setTransactionForm({ ...transactionForm, side: event.target.value as "BUY" | "SELL" })}><option value="BUY">Buy</option><option value="SELL">Sell</option></select><input aria-label="Transaction quantity" type="number" min="0.01" step="0.01" placeholder="Quantity" value={transactionForm.quantity} onChange={(event) => setTransactionForm({ ...transactionForm, quantity: event.target.value })} /><input aria-label="Transaction price" type="number" min="0" step="0.01" placeholder="Price" value={transactionForm.price} onChange={(event) => setTransactionForm({ ...transactionForm, price: event.target.value })} /><input aria-label="Transaction date" type="date" value={transactionForm.executed_at} onChange={(event) => setTransactionForm({ ...transactionForm, executed_at: event.target.value })} /><button className="primary compact" onClick={addTransaction}>Add transaction</button></div>{transactions.length === 0 ? <div className="activity-empty">No transactions recorded yet. Add your first buy or sell activity above.</div> : <div className="transactions-list">{transactions.map((transaction) => <div className="transaction-row" key={transaction.id}><div><strong>{transaction.symbol}</strong><small>{new Date(transaction.executed_at).toLocaleDateString()}</small></div><span className={transaction.side === "BUY" ? "transaction-buy" : "transaction-sell"}>{transaction.side}</span><span>{transaction.quantity} shares</span><span>₹{transaction.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</span><button className="row-menu" aria-label={`Remove ${transaction.symbol} transaction`} onClick={() => removeTransaction(transaction.id)}>×</button></div>)}</div>}</section>
        <section className="activity-section watchlist-section"><div className="section-heading activity-heading"><div><div className="kicker">MARKET TRACKING</div><h2>Watchlists</h2></div></div>{watchlists.length === 0 ? <div className="watchlist-create"><input placeholder="Watchlist name" value={watchlistName} onChange={(event) => setWatchlistName(event.target.value)} /><button className="primary compact" onClick={createWatchlist}>Create watchlist</button></div> : <><div className="watchlist-add"><input placeholder="Add symbol e.g. INFY.NS" value={watchlistSymbol} onChange={(event) => setWatchlistSymbol(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") addWatchlistSymbol(); }} /><button className="primary compact" onClick={addWatchlistSymbol}>Add symbol</button></div><div className="watchlist-items">{watchlistItems.length === 0 ? <div className="activity-empty">Your watchlist is empty. Add a symbol to start tracking it.</div> : watchlistItems.map((item) => { const quote = watchlistQuotes[item.symbol]; return <div className="watchlist-item" key={item.id}><div><strong>{item.symbol}</strong><small>{quote?.name || "Loading quote…"}</small></div><div className="watchlist-quote"><strong>{quote?.price == null ? "—" : `₹${quote.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`}</strong><small className={quote?.change_pct != null && quote.change_pct < 0 ? "negative" : "positive"}>{quote?.change_pct == null ? quote?.status || "Loading" : `${quote.change_pct >= 0 ? "+" : ""}${quote.change_pct.toFixed(2)}%`}</small></div><button className="row-menu" aria-label={`Remove ${item.symbol} from watchlist`} onClick={() => removeWatchlistSymbol(item.symbol)}>×</button></div>; })}</div></>}</section>
        {showAdd && <div className="modal-backdrop" onClick={() => { setShowAdd(false); setStockSearchOpen(false); }}><section className="add-modal" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><div className="kicker">PORTFOLIO ACTION</div><h2>Add holding</h2></div><button className="icon-button" onClick={() => setShowAdd(false)}>×</button></div><p className="modal-copy">Search live market instruments by typing a few letters. Select a result to fill the details automatically.</p><StockSearchField label="Symbol" value={newHolding.symbol} placeholder="Search symbol, e.g. AAPL" onChange={(value) => selectStock(value, "symbol")} onFocus={() => { setStockSearchField("symbol"); setStockSearchQuery(newHolding.symbol); setStockSearchOpen(true); }} open={stockSearchOpen && stockSearchField === "symbol"} suggestions={stockSuggestions} searching={stockSearching} onSelect={chooseStock} onCustom={chooseCustomStock} /><StockSearchField label="Company name" value={newHolding.name} placeholder="Search company name" onChange={(value) => selectStock(value, "name")} onFocus={() => { setStockSearchField("name"); setStockSearchQuery(newHolding.name); setStockSearchOpen(true); }} open={stockSearchOpen && stockSearchField === "name"} suggestions={stockSuggestions} searching={stockSearching} onSelect={chooseStock} onCustom={chooseCustomStock} /><div className="form-row"><label>Quantity<input type="number" min="0.01" step="0.01" value={newHolding.quantity} onChange={(event) => setNewHolding({ ...newHolding, quantity: event.target.value })} /></label><label>Average buy price<input type="number" min="0.01" step="0.01" value={newHolding.avg_buy_price} onChange={(event) => setNewHolding({ ...newHolding, avg_buy_price: event.target.value })} /></label></div><label>Sector<select value={newHolding.sector} onChange={(event) => setNewHolding({ ...newHolding, sector: event.target.value })}><option>Technology</option><option>Financials</option><option>Energy</option><option>Healthcare</option><option>Industrials</option><option>Consumer</option><option>Unclassified</option></select></label><div className="modal-actions"><button className="secondary" onClick={() => setShowAdd(false)}>Cancel</button><button className="primary" onClick={addHolding}>Add to portfolio</button></div></section></div>}
        {showAuth && <div className="modal-backdrop" onClick={() => setShowAuth(false)}><section className="add-modal auth-modal" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><div className="kicker">ALPHASAGE ACCOUNT</div><h2>{authMode === "login" ? "Welcome back" : "Create your account"}</h2></div><button className="icon-button" onClick={() => setShowAuth(false)}>×</button></div><p className="modal-copy">{authMode === "login" ? "Sign in to sync your portfolio and watchlists across devices." : "Create a secure workspace for your investment research."}</p>{authMode === "register" && <label>Display name<input value={authForm.display_name} onChange={(event) => setAuthForm({ ...authForm, display_name: event.target.value })} placeholder="Your name" /></label>}<label>Email<input type="email" value={authForm.email} onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })} placeholder="you@example.com" /></label><label>Password<input type="password" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} placeholder="At least 8 characters" /></label>{authError && <p className="auth-error">{authError}</p>}<div className="modal-actions"><button className="secondary" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "Create account" : "Sign in instead"}</button><button className="primary" onClick={submitAuth}>{authMode === "login" ? "Sign in" : "Create account"}</button></div></section></div>}
        </> : active === "Watchlists" ? <WatchlistsPage watchlists={watchlists} items={watchlistItems} quotes={watchlistQuotes} symbol={watchlistSymbol} suggestions={stockSuggestions} searching={stockSearching} searchOpen={stockSearchOpen && stockSearchField === "symbol"} refreshing={watchlistRefreshing} onSymbolChange={(value) => { setWatchlistSymbol(value); setStockSearchQuery(value); setStockSearchField("symbol"); setStockSearchOpen(true); }} onSearchFocus={() => { setStockSearchField("symbol"); setStockSearchQuery(watchlistSymbol); setStockSearchOpen(true); }} onSelect={chooseWatchlistStock} onCreate={createWatchlist} onAdd={addWatchlistSymbol} onRemove={removeWatchlistSymbol} onViewStock={viewWatchlistStock} onRefresh={refreshWatchlistQuotes} /> : active === "Alerts" ? <AlertsPage alerts={alerts} form={alertForm} message={alertMessage} loading={alertsLoading} browserNotifications={browserNotifications} onEnableNotifications={enableBrowserNotifications} onChange={setAlertForm} onCreate={createAlert} onEvaluate={evaluateAlerts} onRemove={removeAlert} /> : active === "Global markets" ? <MarketOverviewPage instruments={marketInstruments} loading={marketsLoading} selected={selectedMarket} selectedLoading={selectedMarketLoading} onSelect={openMarketDetails} onBack={() => setSelectedMarket(null)} onRefresh={() => setMarketRefreshKey((value) => value + 1)} /> : <WorkspacePage active={active} />}
      </section>
      {stockDetails && <ReadableStockDashboardV2 details={stockDetails} loading={stockDetailsLoading} expanded={stockDetailsExpanded} onExpand={() => setStockDetailsExpanded((value) => !value)} onClose={() => { setStockDetails(null); setStockDetailsPinned(false); setStockDetailsExpanded(false); }} />}
    </main>
  );
}

function LoadingScreen() {
  return <main className="loading-screen" aria-live="polite"><div className="loading-spinner" /><p>Loading your workspace…</p></main>;
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

function ReadableStockDashboard({ details, loading, expanded, onExpand, onClose }: { details: StockDetails; loading: boolean; expanded: boolean; onExpand: () => void; onClose: () => void }) {
  useEffect(() => {
    const tone = details.price != null && details.purchase_price != null && details.price >= details.purchase_price ? "profit" : "loss";
    document.documentElement.dataset.purchaseTone = tone;
    return () => { delete document.documentElement.dataset.purchaseTone; };
  }, [details.price, details.purchase_price]);
  const history = details.history || [];
  const values = history.map((point) => point.close);
  const chartMin = values.length ? Math.min(...values, ...(details.purchase_price ? [details.purchase_price] : [])) : details.purchase_price || 0;
  const chartMax = values.length ? Math.max(...values, ...(details.purchase_price ? [details.purchase_price] : [])) : details.purchase_price || 1;
  const chartRange = Math.max(chartMax - chartMin, 1);
  const yFor = (value: number) => 72 - ((value - chartMin) / chartRange) * 64;
  const points = history.map((point, index) => `${(index / Math.max(history.length - 1, 1)) * 320},${yFor(point.close)}`).join(" ");
  const purchaseY = details.purchase_price == null ? null : yFor(details.purchase_price);
  return <aside className={`stock-preview${expanded ? " expanded" : ""}`}><div className="preview-heading"><div><span className="kicker">SELECTED INSTRUMENT</span><strong>{details.name}</strong><small>{details.symbol} · {details.exchange}</small></div><div className="preview-heading-actions"><span className="preview-status">{loading ? "Loading" : details.status}</span><button className="preview-expand" onClick={onExpand}>{expanded ? "Collapse" : "Expand"}</button><button className="preview-close" onClick={onClose} aria-label="Close stock details">×</button></div></div><div className="preview-price">{details.price == null ? "Price unavailable" : `₹${details.price.toLocaleString("en-IN")}`} {details.change_pct != null && <small className={details.change_pct < 0 ? "negative" : "positive"}>{details.change_pct >= 0 ? "+" : ""}{details.change_pct.toFixed(2)}%</small>}</div>{history.length > 1 && <div className="stock-chart readable-chart"><svg viewBox="0 0 320 80" role="img" aria-label={`${details.name} six month price chart`}><line x1="0" x2="320" y1="8" y2="8" className="chart-grid-line" /><line x1="0" x2="320" y1="40" y2="40" className="chart-grid-line" /><line x1="0" x2="320" y1="72" y2="72" className="chart-grid-line" />{purchaseY != null && <line x1="0" x2="320" y1={purchaseY} y2={purchaseY} className="purchase-price-line" />}<polyline points={points} fill="none" stroke="var(--green)" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg><div><span>6M price trend {details.purchase_price != null && <em className="purchase-legend">Purchase ₹{details.purchase_price.toLocaleString("en-IN")}</em>}</span><span>{details.stock_return_pct == null ? "—" : `${details.stock_return_pct >= 0 ? "+" : ""}${details.stock_return_pct.toFixed(2)}%`}</span></div></div>}<div className="preview-meta"><span>Sector<strong>{details.sector}</strong></span><span>Day high<strong>{details.high == null ? "—" : details.high}</strong></span><span>Day low<strong>{details.low == null ? "—" : details.low}</strong></span><span>Previous close<strong>{details.previous_close == null ? "—" : details.previous_close}</strong></span></div><div className="preview-fundamentals"><span><small>Market cap</small><strong>{details.fundamentals?.market_cap ? `₹${(details.fundamentals.market_cap / 10000000).toFixed(1)} Cr` : "—"}</strong></span><span><small>P/E ratio</small><strong>{details.fundamentals?.pe_ratio?.toFixed(2) || "—"}</strong></span><span><small>52W range</small><strong>{details.fundamentals?.week52_low && details.fundamentals?.week52_high ? `${details.fundamentals.week52_low} – ${details.fundamentals.week52_high}` : "—"}</strong></span><span><small>vs {details.benchmark_symbol || "benchmark"}</small><strong>{details.benchmark_return_pct == null ? "—" : `${details.benchmark_return_pct >= 0 ? "+" : ""}${details.benchmark_return_pct.toFixed(2)}%`}</strong></span></div></aside>;
}

function StockCandleChart({ details }: { details: StockDetails }) {
  const [range, setRange] = useState<"1M" | "3M" | "6M">("6M");
  const [selection, setSelection] = useState<{ start: number; end: number } | null>(null);
  const [drag, setDrag] = useState<{ start: number; current: number } | null>(null);
  const allHistory = details.history || [];
  const rangeSize = range === "1M" ? 22 : range === "3M" ? 66 : 90;
  const baseHistory = allHistory.slice(-rangeSize);
  const history = selection ? baseHistory.slice(selection.start, selection.end + 1) : baseHistory;
  const prices = history.flatMap((point) => [point.high ?? point.close, point.low ?? point.close]);
  if (details.purchase_price != null) prices.push(details.purchase_price);
  const min = prices.length ? Math.min(...prices) : 0;
  const max = prices.length ? Math.max(...prices) : 1;
  const chartRange = Math.max(max - min, 1);
  const yFor = (value: number) => 72 - ((value - min) / chartRange) * 64;
  const xFor = (index: number) => 12 + (index / Math.max(history.length - 1, 1)) * 296;
  const bodyWidth = Math.max(2, Math.min(7, 260 / Math.max(history.length, 1)));
  const purchaseY = details.purchase_price == null ? null : yFor(details.purchase_price);
  const chartX = (event: PointerEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    return Math.max(12, Math.min(308, ((event.clientX - bounds.left) / bounds.width) * 320));
  };
  const indexForX = (x: number) => Math.round(((x - 12) / 296) * Math.max(baseHistory.length - 1, 1));
  const finishSelection = (event: PointerEvent<SVGSVGElement>) => {
    if (!drag) return;
    const endX = chartX(event);
    if (Math.abs(endX - drag.start) > 8) {
      const first = Math.max(0, Math.min(indexForX(drag.start), indexForX(endX)));
      const last = Math.min(baseHistory.length - 1, Math.max(indexForX(drag.start), indexForX(endX)));
      if (last > first) setSelection({ start: first, end: last });
    }
    setDrag(null);
  };
  const selectionLeft = drag ? Math.min(drag.start, drag.current) : null;
  const selectionWidth = drag ? Math.abs(drag.current - drag.start) : 0;

  return <div className="stock-chart readable-chart"><div className="chart-toolbar"><span>Price history <small>Drag across the chart to zoom</small></span><div className="chart-range-controls" role="group" aria-label="Chart time range">{(["1M", "3M", "6M"] as const).map((option) => <button type="button" key={option} className={range === option ? "active" : ""} onClick={() => { setRange(option); setSelection(null); }}>{option}</button>)}{selection && <button type="button" onClick={() => setSelection(null)}>Reset</button>}</div></div><svg viewBox="0 0 320 80" role="img" aria-label={`${details.name} ${range} candlestick price chart`} onPointerDown={(event) => { event.currentTarget.setPointerCapture(event.pointerId); setDrag({ start: chartX(event), current: chartX(event) }); }} onPointerMove={(event) => { if (drag) setDrag({ ...drag, current: chartX(event) }); }} onPointerUp={finishSelection} onPointerCancel={() => setDrag(null)}>
    <line x1="0" x2="320" y1="8" y2="8" className="chart-grid-line" />
    <line x1="0" x2="320" y1="40" y2="40" className="chart-grid-line" />
    <line x1="0" x2="320" y1="72" y2="72" className="chart-grid-line" />
    {purchaseY != null && <line x1="0" x2="320" y1={purchaseY} y2={purchaseY} className="purchase-price-line" />}
    {selectionLeft != null && <rect x={selectionLeft} y="0" width={selectionWidth} height="80" className="chart-selection" />}
    {history.map((point) => {
      const open = point.open ?? point.close;
      const close = point.close;
      const high = point.high ?? Math.max(open, close);
      const low = point.low ?? Math.min(open, close);
      const up = close >= open;
      const x = xFor(history.indexOf(point));
      const bodyY = Math.min(yFor(open), yFor(close));
      const bodyHeight = Math.max(1.5, Math.abs(yFor(open) - yFor(close)));
      return <g key={point.date}><line x1={x} x2={x} y1={yFor(high)} y2={yFor(low)} className={up ? "candle-wick-up" : "candle-wick-down"} /><rect x={x - bodyWidth / 2} y={bodyY} width={bodyWidth} height={bodyHeight} className={up ? "candle-up" : "candle-down"} /></g>;
    })}
  </svg><div><span>{range} candlestick trend {details.purchase_price != null && <em className="purchase-legend">Purchase ₹{details.purchase_price.toLocaleString("en-IN")}</em>}</span><span>{details.stock_return_pct == null ? "—" : `${details.stock_return_pct >= 0 ? "+" : ""}${details.stock_return_pct.toFixed(2)}%`}</span></div></div>;
}

function ReadableStockDashboardV2({ details, loading, expanded, onExpand, onClose }: { details: StockDetails; loading: boolean; expanded: boolean; onExpand: () => void; onClose: () => void }) {
  useEffect(() => {
    const tone = details.price != null && details.purchase_price != null && details.price >= details.purchase_price ? "profit" : "loss";
    document.documentElement.dataset.purchaseTone = tone;
    return () => { delete document.documentElement.dataset.purchaseTone; };
  }, [details.price, details.purchase_price]);
  const forecast = details.forecast;
  return <aside className={`stock-preview${expanded ? " expanded" : ""}`}><div className="preview-heading"><div><span className="kicker">SELECTED INSTRUMENT</span><strong>{details.name}</strong><small>{details.symbol} · {details.exchange}</small></div><div className="preview-heading-actions"><span className="preview-status">{loading ? "Loading" : details.status}</span><button className="preview-expand" onClick={onExpand}>{expanded ? "Collapse" : "Expand"}</button><button className="preview-close" onClick={onClose} aria-label="Close stock details">×</button></div></div><div className="preview-price">{details.price == null ? "Price unavailable" : `₹${details.price.toLocaleString("en-IN")}`} {details.change_pct != null && <small className={details.change_pct < 0 ? "negative" : "positive"}>{details.change_pct >= 0 ? "+" : ""}{details.change_pct.toFixed(2)}%</small>}</div>{(details.history || []).length > 1 && <StockCandleChart details={details} />}<div className="preview-meta"><span>Sector<strong>{details.sector}</strong></span><span>Day high<strong>{details.high == null ? "—" : details.high}</strong></span><span>Day low<strong>{details.low == null ? "—" : details.low}</strong></span><span>Previous close<strong>{details.previous_close == null ? "—" : details.previous_close}</strong></span></div><div className="indicator-summary"><span><small>SMA 20</small><strong>{details.indicators?.sma_20 ?? "—"}</strong></span><span><small>EMA 20</small><strong>{details.indicators?.ema_20 ?? "—"}</strong></span><span><small>RSI 14</small><strong>{details.indicators?.rsi_14 ?? "—"}</strong></span></div><div className="forecast-summary"><div><small>Baseline forecast</small><strong>{forecast?.forecast == null ? "Unavailable" : `₹${forecast.forecast.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`}</strong></div><span>{forecast?.lower_bound == null || forecast?.upper_bound == null ? "Needs more history" : `Expected range ₹${forecast.lower_bound.toFixed(2)} – ₹${forecast.upper_bound.toFixed(2)}`}</span><em>Moving-average benchmark · not investment advice</em></div><div className="preview-fundamentals"><span><small>Market cap</small><strong>{details.fundamentals?.market_cap ? `₹${(details.fundamentals.market_cap / 10000000).toFixed(1)} Cr` : "—"}</strong></span><span><small>P/E ratio</small><strong>{details.fundamentals?.pe_ratio?.toFixed(2) || "—"}</strong></span><span><small>52W range</small><strong>{details.fundamentals?.week52_low && details.fundamentals?.week52_high ? `${details.fundamentals.week52_low} – ${details.fundamentals.week52_high}` : "—"}</strong></span><span><small>vs {details.benchmark_symbol || "benchmark"}</small><strong>{details.benchmark_return_pct == null ? "—" : `${details.benchmark_return_pct >= 0 ? "+" : ""}${details.benchmark_return_pct.toFixed(2)}%`}</strong></span></div></aside>;
}

function StockDashboardPreview({ details, loading, expanded, onExpand, onClose }: { details: StockDetails; loading: boolean; expanded: boolean; onExpand: () => void; onClose: () => void }) {
  const history = details.history || [];
  const values = history.map((point) => point.close);
  const chartMin = values.length ? Math.min(...values, ...(details.purchase_price ? [details.purchase_price] : [])) : details.purchase_price || 0;
  const chartMax = values.length ? Math.max(...values, ...(details.purchase_price ? [details.purchase_price] : [])) : details.purchase_price || 1;
  const chartRange = Math.max(chartMax - chartMin, 1);
  const points = history.map((point, index) => `${(index / Math.max(history.length - 1, 1)) * 320},${72 - ((point.close - chartMin) / chartRange) * 64}`).join(" ");
  const indicator = details.indicators;
  return <aside className={`stock-preview${expanded ? " expanded" : ""}`}><div className="preview-heading"><div><span className="kicker">SELECTED INSTRUMENT</span><strong>{details.name}</strong><small>{details.symbol} · {details.exchange}</small></div><div className="preview-heading-actions"><span className="preview-status">{loading ? "Loading" : details.status}</span><button className="preview-expand" onClick={onExpand} aria-label={expanded ? "Collapse stock details" : "Expand stock details"}>{expanded ? "Collapse" : "Expand"}</button><button className="preview-close" onClick={onClose} aria-label="Close stock details">×</button></div></div><div className="preview-price">{details.price == null ? "Price unavailable" : `₹${details.price.toLocaleString("en-IN")}`} {details.change_pct != null && <small className={details.change_pct < 0 ? "negative" : "positive"}>{details.change_pct >= 0 ? "+" : ""}{details.change_pct.toFixed(2)}%</small>}</div>{history.length > 1 && <div className="stock-chart"><svg viewBox="0 0 320 80" role="img" aria-label={`${details.name} six month price chart`}><polyline points={points} fill="none" stroke="var(--green)" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg><div><span>6M price trend</span><span>{details.stock_return_pct == null ? "—" : `${details.stock_return_pct >= 0 ? "+" : ""}${details.stock_return_pct.toFixed(2)}%`}</span></div></div>}<div className="preview-meta"><span>Sector<strong>{details.sector}</strong></span><span>Day high<strong>{details.high == null ? "—" : details.high}</strong></span><span>Day low<strong>{details.low == null ? "—" : details.low}</strong></span><span>Previous close<strong>{details.previous_close == null ? "—" : details.previous_close}</strong></span></div><div className="indicator-summary"><span><small>SMA 20</small><strong>{indicator?.sma_20 ?? "—"}</strong></span><span><small>EMA 20</small><strong>{indicator?.ema_20 ?? "—"}</strong></span><span><small>RSI 14</small><strong>{indicator?.rsi_14 ?? "—"}</strong></span></div><div className="preview-fundamentals"><span><small>Market cap</small><strong>{details.fundamentals?.market_cap ? `₹${(details.fundamentals.market_cap / 10000000).toFixed(1)} Cr` : "—"}</strong></span><span><small>P/E ratio</small><strong>{details.fundamentals?.pe_ratio?.toFixed(2) || "—"}</strong></span><span><small>52W range</small><strong>{details.fundamentals?.week52_low && details.fundamentals?.week52_high ? `${details.fundamentals.week52_low} – ${details.fundamentals.week52_high}` : "—"}</strong></span><span><small>vs {details.benchmark_symbol || "benchmark"}</small><strong>{details.benchmark_return_pct == null ? "—" : `${details.benchmark_return_pct >= 0 ? "+" : ""}${details.benchmark_return_pct.toFixed(2)}%`}</strong></span></div></aside>;
}

function StockSearchField({ label, value, placeholder, onChange, onFocus, open, suggestions, searching, onSelect, onCustom }: { label: string; value: string; placeholder: string; onChange: (value: string) => void; onFocus: () => void; open: boolean; suggestions: StockOption[]; searching: boolean; onSelect: (stock: StockOption) => void; onCustom: () => void }) {
  return <label className="stock-search-field">{label}<div className="stock-search-control"><Search size={15} /><input value={value} onChange={(event) => onChange(event.target.value)} onFocus={onFocus} placeholder={placeholder} />{searching && <span className="search-spinner" />}</div>{open && searching && <div className="stock-results search-status">Searching live instruments…</div>}{open && !searching && suggestions.length > 0 && <div className="stock-results">{suggestions.map((stock) => <button type="button" className="stock-result" key={`${stock.symbol}-${stock.name}`} onMouseDown={(event) => event.preventDefault()} onClick={() => onSelect(stock)}><span><strong>{stock.symbol}</strong><small>{stock.name}</small></span><em>{stock.exchange || stock.sector}</em></button>)}</div>}{open && !searching && value.length > 1 && suggestions.length === 0 && <div className="stock-results"><div className="empty-results">No live result yet</div><button type="button" className="stock-custom-result" onMouseDown={(event) => event.preventDefault()} onClick={onCustom}><strong>Use “{value}” as a custom instrument</strong><small>You can add any valid market symbol and update its details later.</small></button></div>}</label>;
}

function AlertsPage({ alerts, form, message, loading, browserNotifications, onEnableNotifications, onChange, onCreate, onEvaluate, onRemove }: { alerts: AlertRule[]; form: { symbol: string; rule: string; threshold: string; cooldown_minutes: string }; message: string; loading: boolean; browserNotifications: boolean; onEnableNotifications: () => void; onChange: (form: { symbol: string; rule: string; threshold: string; cooldown_minutes: string }) => void; onCreate: () => void; onEvaluate: () => void; onRemove: (id: string) => void }) {
  return <><div className="page-header"><div><div className="kicker">AUTOMATED MONITORING</div><h1>Alerts.</h1><p>Track price levels and daily moves without constantly watching the market.</p></div><div className="header-actions"><button className="secondary" onClick={onEnableNotifications}><Bell size={16} /> {browserNotifications ? "Browser alerts on" : "Enable browser alerts"}</button><button className="secondary" onClick={onEvaluate}><Bell size={16} /> Evaluate now</button></div></div><div className="disclaimer"><ShieldCheck size={16} /><span><strong>Source-aware alerts.</strong> Notifications are sent only when market data is available and cooldowns prevent duplicates.</span></div><section className="alerts-card"><div className="section-heading activity-heading"><div><div className="kicker">NEW ALERT</div><h2>Create a rule</h2></div></div><div className="alert-form"><label>Symbol<input value={form.symbol} onChange={(event) => onChange({ ...form, symbol: event.target.value })} placeholder="RELIANCE.NS" /></label><label>Condition<select value={form.rule} onChange={(event) => onChange({ ...form, rule: event.target.value })}><option value="price_above">Price rises above</option><option value="price_below">Price falls below</option><option value="change_pct_above">Daily change above</option><option value="change_pct_below">Daily change below</option></select></label><label>Threshold<input type="number" value={form.threshold} onChange={(event) => onChange({ ...form, threshold: event.target.value })} /></label><label>Cooldown (minutes)<input type="number" min="1" value={form.cooldown_minutes} onChange={(event) => onChange({ ...form, cooldown_minutes: event.target.value })} /></label><button className="primary" onClick={onCreate}>Create alert</button></div>{message && <p className="alert-message">{message}</p>}</section><section className="alerts-card"><div className="section-heading activity-heading"><div><div className="kicker">SAVED RULES</div><h2>Your alerts</h2></div><span>{loading ? "Loading…" : `${alerts.length} active`}</span></div>{alerts.length === 0 ? <div className="activity-empty">No alerts yet. Create a price or daily-movement rule above.</div> : <div className="alert-list">{alerts.map((alert) => { const downward = alert.rule.endsWith("below"); return <div className={`alert-row ${downward ? "alert-down" : "alert-up"}`} key={alert.id}><div><strong>{alert.symbol}</strong><small>{alert.rule.replaceAll("_", " ")} {alert.threshold}</small></div><span>Cooldown {alert.cooldown_minutes}m</span><small>{alert.last_triggered_at ? `Last triggered ${new Date(alert.last_triggered_at).toLocaleString()}` : "Not triggered yet"}</small><button className="alert-remove" onClick={() => onRemove(alert.id)} aria-label={`Remove ${alert.symbol} alert`}>×</button></div>; })}</div>}</section></>;
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

function WatchlistsPage({ watchlists, items, quotes, symbol, suggestions, searching, searchOpen, refreshing, onSymbolChange, onSearchFocus, onSelect, onCreate, onAdd, onRemove, onViewStock, onRefresh }: { watchlists: Watchlist[]; items: WatchlistItem[]; quotes: Record<string, StockDetails>; symbol: string; suggestions: StockOption[]; searching: boolean; searchOpen: boolean; refreshing: boolean; onSymbolChange: (value: string) => void; onSearchFocus: () => void; onSelect: (stock: StockOption) => void; onCreate: () => void; onAdd: () => void; onRemove: (symbol: string) => void; onViewStock: (symbol: string, name: string) => void; onRefresh: () => void }) {
  return <><div className="page-header"><div><div className="kicker">PERSONAL WORKSPACE</div><h1>Watchlists.</h1><p>Keep the companies and themes you care about one click away.</p></div><div className="header-actions"><button className="secondary" onClick={onRefresh} disabled={refreshing}><LineChart size={16} /> {refreshing ? "Refreshing" : "Refresh quotes"}</button><button className="primary" onClick={onCreate}><Plus size={17} /> Create watchlist</button></div></div><div className="disclaimer"><ShieldCheck size={16} /><span><strong>AlphaSage workspace.</strong> Your watchlist is saved to your account and synced across sessions.</span></div><section className="watchlist-page-card"><div className="watchlist-page-header"><div><div className="kicker">MARKET TRACKING</div><h2>{watchlists[0]?.name || "Your watchlist"}</h2></div>{watchlists.length > 0 && <span>{items.length} symbols</span>}</div>{watchlists.length === 0 ? <div className="watchlist-page-empty"><strong>Create your first watchlist</strong><p>Save companies here to follow their prices and daily movement.</p><button className="primary compact" onClick={onCreate}><Plus size={15} /> Create watchlist</button></div> : <><div className="watchlist-add"><StockSearchField label="" value={symbol} placeholder="Search symbol or company name" onChange={onSymbolChange} onFocus={onSearchFocus} open={searchOpen} suggestions={suggestions} searching={searching} onSelect={onSelect} onCustom={() => onAdd()} /><button className="primary compact" onClick={onAdd}>Add symbol</button></div>{items.length === 0 ? <div className="activity-empty">Your watchlist is empty. Add a symbol to start tracking it.</div> : <div className="watchlist-page-list">{items.map((item) => { const quote = quotes[item.symbol]; return <div className="watchlist-page-row" key={item.id} onClick={() => onViewStock(item.symbol, quote?.name || item.symbol)} role="button" tabIndex={0}><div className="ticker-icon">{item.symbol.slice(0, 2)}</div><div className="watchlist-page-name"><strong>{quote?.name || item.symbol}</strong><small>{item.symbol}</small></div><div className="watchlist-page-price"><strong>{quote?.price == null ? "—" : `₹${quote.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`}</strong><small className={quote?.change_pct != null && quote.change_pct < 0 ? "negative" : "positive"}>{quote?.change_pct == null ? quote?.status || "Loading" : `${quote.change_pct >= 0 ? "+" : ""}${quote.change_pct.toFixed(2)}%`}</small></div><button className="row-menu" aria-label={`Remove ${item.symbol} from watchlist`} onClick={(event) => { event.stopPropagation(); onRemove(item.symbol); }}>×</button></div>; })}</div>}</>}</section></>;
}

function MarketOverviewPage({ instruments, loading, selected, selectedLoading, onSelect, onBack, onRefresh }: { instruments: MarketInstrument[]; loading: boolean; selected: StockDetails | null; selectedLoading: boolean; onSelect: (instrument: MarketInstrument) => void; onBack: () => void; onRefresh: () => void }) {
  if (selected) return <MarketDetailPage details={selected} loading={selectedLoading} onBack={onBack} />;
  return <><div className="page-header"><div><div className="kicker">MARKET INTELLIGENCE</div><h1>Global markets.</h1><p>Track major indices and understand how markets are moving together.</p></div><button className="secondary" onClick={onRefresh} disabled={loading}><LineChart size={16} /> {loading ? "Refreshing" : "Refresh markets"}</button></div><div className="disclaimer"><ShieldCheck size={16} /><span><strong>Market overview.</strong> Provider data may be delayed or unavailable. Select a market to open its full detail view.</span></div><section className="market-grid">{loading && !instruments.length ? <div className="market-empty">Loading market data…</div> : instruments.map((instrument) => <article className="market-card market-card-clickable" key={instrument.symbol} onClick={() => onSelect(instrument)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") onSelect(instrument); }} role="button" tabIndex={0}><div className="market-card-top"><span>{instrument.region}</span><small>{instrument.status}</small></div><h2>{instrument.name}</h2><strong className={instrument.change_pct != null && instrument.change_pct < 0 ? "market-price negative" : "market-price positive"}>{instrument.price == null ? "—" : instrument.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</strong><p className={instrument.change_pct != null && instrument.change_pct < 0 ? "negative" : "positive"}>{instrument.change_pct == null ? "Data unavailable" : `${instrument.change_pct >= 0 ? "+" : ""}${instrument.change_pct.toFixed(2)}% today`}</p><span className="market-card-link">Open market details <ChevronDown size={14} /></span></article>)}</section></>;
}

function MarketDetailPage({ details, loading, onBack }: { details: StockDetails; loading: boolean; onBack: () => void }) {
  const [range, setRange] = useState("1D");
  const [chartMode, setChartMode] = useState<"area" | "line">("area");
  const [compare, setCompare] = useState(false);
  const [indicators, setIndicators] = useState(false);
  const ranges = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "MAX"];
  const history = details.history || [];
  return <><div className="market-detail-nav"><button className="text-action" onClick={onBack}>← Back to global markets</button><span>Markets / {details.symbol}</span></div><div className="page-header market-detail-page-header"><div><div className="kicker">MARKET DETAIL</div><h1>{details.name}</h1><p>{details.symbol} · {details.provider || "Market data provider"}</p></div><span className="data-pill">{loading ? "Loading" : details.status}</span></div><div className="market-detail-price"><strong>{details.price == null ? "Price unavailable" : details.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</strong><span className={details.change_pct != null && details.change_pct < 0 ? "negative" : "positive"}>{details.change_pct == null ? "—" : `${details.change_pct >= 0 ? "+" : ""}${details.change_pct.toFixed(2)}% (${details.change == null ? "—" : details.change.toFixed(2)}) Today`}</span></div><div className="market-chart-toolbar"><button className={chartMode === "area" ? "active" : ""} onClick={() => setChartMode(chartMode === "area" ? "line" : "area")}><LineChart size={15} /> {chartMode === "area" ? "Area" : "Line"} <ChevronDown size={13} /></button><button className={compare ? "active" : ""} onClick={() => setCompare((value) => !value)}><LineChart size={15} /> Compare <ChevronDown size={13} /></button><button className={indicators ? "active" : ""} onClick={() => setIndicators((value) => !value)}><Settings2 size={15} /> Indicators <ChevronDown size={13} /></button></div><section className="market-detail-chart">{history.length > 1 ? <MarketAreaChart details={details} range={range} chartMode={chartMode} compare={compare} indicators={indicators} /> : <div className="market-empty">Historical chart unavailable for this market.</div>}</section><div className="market-range-tabs">{ranges.map((option) => <button key={option} className={range === option ? "active" : ""} onClick={() => setRange(option)}>{option}</button>)}</div><section className="market-overview-section"><h2>Overview</h2><div className="market-detail-grid"><div><small>Open</small><strong>{details.previous_close ?? "—"}</strong></div><div><small>Low</small><strong>{details.low ?? "—"}</strong></div><div><small>52-week low</small><strong>{details.fundamentals?.week52_low ?? "—"}</strong></div><div><small>High</small><strong>{details.high ?? "—"}</strong></div><div><small>52-week high</small><strong>{details.fundamentals?.week52_high ?? "—"}</strong></div><div><small>Benchmark return</small><strong>{details.benchmark_return_pct == null ? "—" : `${details.benchmark_return_pct.toFixed(2)}%`}</strong></div></div></section><div className="disclaimer"><ShieldCheck size={16} /><span>Prices may be delayed. Indicators and forecasts are research features, not financial advice.</span></div></>;
}

function MarketAreaChart({ details, range, chartMode, compare, indicators }: { details: StockDetails; range: string; chartMode: "area" | "line"; compare: boolean; indicators: boolean }) {
  const history = range === "1D" && (details.intraday_history?.length || 0) > 1 ? details.intraday_history || [] : details.history || [];
  const benchmark = details.benchmark || [];
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const values = history.map((point) => point.close);
  const benchmarkStart = benchmark[0]?.close;
  const baseStart = values[0];
  const benchmarkValues = compare && benchmarkStart && baseStart ? benchmark.map((point) => baseStart * point.close / benchmarkStart).slice(-history.length) : [];
  const movingAverage = values.map((_, index) => index < 19 ? null : values.slice(index - 19, index + 1).reduce((sum, value) => sum + value, 0) / 20);
  const allValues = [...values, ...benchmarkValues.filter((value): value is number => value != null)];
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const span = Math.max(max - min, 1);
  const toY = (value: number) => 220 - ((value - min) / span) * 185;
  const points = history.map((point, index) => `${(index / Math.max(history.length - 1, 1)) * 720},${toY(point.close)}`).join(" ");
  const benchmarkPoints = benchmarkValues.map((value, index) => `${(index / Math.max(benchmarkValues.length - 1, 1)) * 720},${toY(value)}`).join(" ");
  const indicatorPoints = movingAverage.map((value, index) => value == null ? null : `${(index / Math.max(values.length - 1, 1)) * 720},${toY(value)}`).filter(Boolean).join(" ");
  const area = `${points} 720,220 0,220`;
  const direction = details.change_pct != null && details.change_pct < 0 ? "down" : "up";
  const onMove = (event: ReactMouseEvent<SVGSVGElement>) => { const svg = event.currentTarget; const screenPoint = svg.createSVGPoint(); screenPoint.x = event.clientX; screenPoint.y = event.clientY; const transform = svg.getScreenCTM(); if (!transform) return; const chartPoint = screenPoint.matrixTransform(transform.inverse()); const x = Math.max(0, Math.min(720, chartPoint.x)); const index = Math.round((x / 720) * (history.length - 1)); setHoverIndex(Math.max(0, Math.min(history.length - 1, index))); };
  const hovered = hoverIndex == null ? null : history[hoverIndex];
  return <div className={`market-area-chart ${direction}`}><div className="market-chart-axis"><span>{max.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</span><span>{((max + min) / 2).toLocaleString("en-IN", { maximumFractionDigits: 2 })}</span><span>{min.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</span></div><div className="market-chart-canvas"><svg viewBox="0 0 720 240" role="img" aria-label={`${details.name} ${range} area chart`} onMouseMove={onMove} onMouseLeave={() => setHoverIndex(null)}><defs><linearGradient id={`marketAreaFill-${details.symbol}`} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="var(--market-chart)" stopOpacity=".42" /><stop offset="100%" stopColor="var(--market-chart)" stopOpacity=".02" /></linearGradient></defs><line x1="0" x2="720" y1="35" y2="35" className="market-grid-line" /><line x1="0" x2="720" y1="127" y2="127" className="market-grid-line" /><line x1="0" x2="720" y1="220" y2="220" className="market-grid-line" />{details.previous_close != null && <line x1="0" x2="720" y1={toY(details.previous_close)} y2={toY(details.previous_close)} className="market-prev-line" />}{chartMode === "area" && <polygon points={area} fill={`url(#marketAreaFill-${details.symbol})`} />}<polyline points={points} fill="none" stroke="var(--market-chart)" strokeWidth="2.2" vectorEffect="non-scaling-stroke" />{compare && benchmarkPoints && <polyline points={benchmarkPoints} fill="none" stroke="#8ca4bd" strokeWidth="1.5" strokeDasharray="5 4" vectorEffect="non-scaling-stroke" />}{indicators && indicatorPoints && <polyline points={indicatorPoints} fill="none" stroke="#f4c95d" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />}{hoverIndex != null && <><line x1={(hoverIndex / Math.max(history.length - 1, 1)) * 720} x2={(hoverIndex / Math.max(history.length - 1, 1)) * 720} y1="0" y2="220" className="market-hover-line" /><circle cx={(hoverIndex / Math.max(history.length - 1, 1)) * 720} cy={toY(history[hoverIndex].close)} r="4" className="market-hover-dot" /></>}</svg>{hovered && <div className="market-hover-card" style={{ left: `${(hoverIndex! / Math.max(history.length - 1, 1)) * 100}%` }}><strong>Price: {hovered.close.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</strong><span>{formatMarketPointDate(hovered.date)}</span></div>}</div><div className="market-chart-footer"><span>{range} price trend</span><span>Prev. close {details.previous_close ?? "—"}</span></div></div>;
}

