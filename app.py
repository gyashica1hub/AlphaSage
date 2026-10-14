"""
app.py
------
Main Streamlit Dashboard - professional fintech-style layout with a
REAL working Dark/Light mode toggle (built inside the app itself,
independent of Streamlit's own System/Light/Dark menu).

Run karne ke liye: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date

from src.fetch_prices import (
    get_portfolio_with_live_prices,
    get_historical_data,
    get_portfolio_value_history,
)
from src.sentiment import get_stock_sentiment_summary
from src.predict import get_prediction, load_saved_model
from src.portfolio_manager import add_stock, remove_stock, load_portfolio_raw
from src.alerts import check_alerts
from src.kite_integration import is_kite_configured, fetch_real_holdings
from src.backtest import evaluate_and_backtest
from src.explainability import explain_prediction, SHAP_AVAILABLE
from src.portfolio_analytics import diversification_score, performers, risk_score

# ---------------- Page Config ----------------
st.set_page_config(page_title="AlphaSage", layout="wide", page_icon=None)

# ---------------- Theme State ----------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

LIGHT = {
    "bg": "#F6F8FB", "card": "#FFFFFF", "border": "#EEF1F6",
    "text": "#12172B", "subtext": "#8A94A6", "sidebar_bg": "#FFFFFF",
    "up": "#16A34A", "down": "#DC2626", "accent": "#38BDF8",
    "btn_bg": "#12172B", "btn_text": "#FFFFFF", "btn_hover": "#2A3050",
    "notif_loss_bg": "#FDECEC", "notif_loss_text": "#7A1F1F",
    "notif_gain_bg": "#EAFBF0", "notif_gain_text": "#155C33",
    "shadow": "rgba(20, 30, 60, 0.04)",
}

DARK = {
    "bg": "#0A0E17", "card": "#131A2A", "border": "#1E293B",
    "text": "#F1F5F9", "subtext": "#94A3B8", "sidebar_bg": "#0D1420",
    "up": "#22C55E", "down": "#EF4444", "accent": "#38BDF8",
    "btn_bg": "#1E3A5F", "btn_text": "#E2E8F0", "btn_hover": "#38BDF8",
    "notif_loss_bg": "#1F1215", "notif_loss_text": "#FCA5A5",
    "notif_gain_bg": "#0F1F17", "notif_gain_text": "#86EFAC",
    "shadow": "rgba(0, 0, 0, 0.3)",
}

T = DARK if st.session_state.dark_mode else LIGHT

# ---------------- Dynamic CSS (theme-aware) ----------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, sans-serif; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stToolbar"] {{ display: none; }}
    [data-testid="stDecoration"] {{ display: none; }}

    .stApp {{
        background-color: {T['bg']};
        animation: fadeIn 0.4s ease-in;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    /* ---------- Cards ---------- */
    div[data-testid="stMetric"], .custom-card {{
        background-color: {T['card']};
        border: 1px solid {T['border']};
        border-radius: 18px;
        padding: 20px 22px;
        box-shadow: 0 1px 2px {T['shadow']}, 0 4px 16px {T['shadow']};
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px {T['shadow']}, 0 12px 28px {T['shadow']};
    }}
    div[data-testid="stMetricLabel"] {{
        color: {T['subtext']}; font-size: 11.5px; font-weight: 600;
        text-transform: uppercase; letter-spacing: .6px;
    }}
    div[data-testid="stMetricValue"] {{
        color: {T['text']}; font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
        font-weight: 800; font-size: 26px; letter-spacing: -0.5px;
    }}
    div[data-testid="stMetricDelta"] {{ font-weight: 600; }}

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {{
        background-color: {T['sidebar_bg']};
        border-right: 1px solid {T['border']};
    }}
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {T['text']} !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown strong {{
        font-size: 11px; letter-spacing: .8px; color: {T['subtext']} !important;
    }}

    /* ---------- Header ---------- */
    .app-title {{
        font-size: 28px; font-weight: 800; color: {T['text']};
        margin-bottom: 0px; letter-spacing: -0.6px;
    }}
    .app-subtitle {{
        color: {T['subtext']}; font-size: 13.5px; margin-top: 3px; margin-bottom: 8px;
        display: flex; align-items: center; gap: 6px;
    }}
    .live-dot {{
        display: inline-block; width: 7px; height: 7px; border-radius: 50%;
        background: {T['up']}; box-shadow: 0 0 0 0 rgba(22,163,74,0.5);
        animation: pulse 1.8s infinite;
    }}
    @keyframes pulse {{
        0%   {{ box-shadow: 0 0 0 0 rgba(22,163,74,0.45); }}
        70%  {{ box-shadow: 0 0 0 7px rgba(22,163,74,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(22,163,74,0); }}
    }}

    /* ---------- Ticker ---------- */
    .ticker-wrap {{
        width: 100%; overflow: hidden;
        background: {T['card']};
        border: 1px solid {T['border']};
        border-radius: 14px; padding: 12px 0; margin-bottom: 22px;
        box-shadow: 0 1px 2px {T['shadow']}, 0 4px 16px {T['shadow']};
    }}
    .ticker-move {{
        display: inline-block; white-space: nowrap;
        animation: ticker-scroll 32s linear infinite; padding-left: 100%;
    }}
    .ticker-item {{
        display: inline-block; margin: 0 14px; font-size: 13.5px; font-weight: 600;
        color: {T['text']}; background: {T['bg']}; padding: 6px 14px; border-radius: 999px;
        border: 1px solid {T['border']};
    }}
    .ticker-up {{ color: {T['up']}; font-weight: 700; }}
    .ticker-down {{ color: {T['down']}; font-weight: 700; }}
    @keyframes ticker-scroll {{
        0%   {{ transform: translateX(0); }}
        100% {{ transform: translateX(-100%); }}
    }}

    /* ---------- Buttons ---------- */
    div.stButton > button, [data-testid="stPopover"] > button {{
        background-color: {T['btn_bg']}; color: {T['btn_text']} !important;
        border-radius: 10px; border: none; font-weight: 600; padding: 8px 18px;
        transition: transform 0.12s ease, box-shadow 0.12s ease, background-color 0.15s ease;
        box-shadow: 0 1px 3px {T['shadow']};
    }}
    [data-testid="stDownloadButton"] button,
    [data-testid="stPopover"] > button {{
        background: {T['card']} !important; color: {T['text']} !important;
        border: 1px solid {T['border']} !important; border-radius: 12px !important;
        min-height: 42px; font-weight: 600;
    }}
    [data-testid="stDownloadButton"] button p,
    [data-testid="stPopover"] > button p {{ color: {T['text']} !important; }}
    section[data-testid="stSidebar"] div.stButton > button {{
        justify-content: flex-start; background: transparent; border-color: transparent;
        color: {T['subtext']} !important; box-shadow: none; border-radius: 10px;
        font-weight: 600; padding: 8px 12px; text-align: left;
    }}
    section[data-testid="stSidebar"] div.stButton > button div {{ justify-content: flex-start; }}
    section[data-testid="stSidebar"] div.stButton > button:hover {{
        background: {T['card']}; color: {T['text']} !important; border-color: {T['border']};
    }}
    div.stButton > button:hover, [data-testid="stPopover"] > button:hover {{
        background-color: {T['btn_hover']}; color: {T['btn_text']} !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px {T['shadow']};
    }}
    div.stButton > button:active {{ transform: translateY(0px); }}
    div.stButton > button p, [data-testid="stPopover"] > button p {{ color: {T['btn_text']} !important; }}

    /* ---------- Dataframe ---------- */
    .stDataFrame {{
        border-radius: 16px; overflow: hidden; border: 1px solid {T['border']};
        box-shadow: 0 1px 2px {T['shadow']}, 0 4px 16px {T['shadow']};
    }}

    /* ---------- Section titles ---------- */
    .section-title {{
        font-size: 17px; font-weight: 700; color: {T['text']};
        margin-bottom: 12px; margin-top: 4px; letter-spacing: -0.2px;
        display: flex; align-items: center; gap: 8px;
    }}
    .section-title::before {{
        content: ""; display: inline-block; width: 4px; height: 16px;
        background: {T['accent']}; border-radius: 3px;
    }}

    /* ---------- Notifications ---------- */
    .notif-loss {{
        background:{T['notif_loss_bg']}; border-left:3px solid {T['down']};
        color:{T['notif_loss_text']}; padding:11px 15px; border-radius:10px;
        margin-bottom:8px; font-size:13px; font-weight: 500;
    }}
    .notif-gain {{
        background:{T['notif_gain_bg']}; border-left:3px solid {T['up']};
        color:{T['notif_gain_text']}; padding:11px 15px; border-radius:10px;
        margin-bottom:8px; font-size:13px; font-weight: 500;
    }}
    .notif-empty {{ color:{T['subtext']}; font-size:13px; padding:8px 0; }}

    hr {{ border-color: {T['border']}; margin: 1.6em 0; }}

    /* ---------- General text ---------- */
    .stApp p, .stApp label, .stMarkdown, .stMarkdown li {{ color: {T['text']}; }}
    [data-testid="stCaptionContainer"], .stCaption {{ color: {T['subtext']} !important; font-size: 12.5px; }}

    [data-baseweb="tag"], [data-baseweb="tag"] span, [data-baseweb="tag"] div {{
        color: #FFFFFF !important; border-radius: 8px !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: {T['card']} !important;
        border-color: {T['border']} !important;
        color: {T['text']} !important;
        border-radius: 10px !important;
    }}
    div[data-baseweb="select"] span {{ color: {T['text']}; }}
    div[data-baseweb="popover"] li {{ color: {T['text']}; background-color: {T['card']}; }}

    /* ---------- Expander / Form polish ---------- */
    .streamlit-expanderHeader, [data-testid="stExpander"] summary {{
        border-radius: 10px !important; font-weight: 600 !important;
    }}
    [data-testid="stForm"] {{
        border: 1px solid {T['border']}; border-radius: 14px; padding: 16px;
        background-color: {T['bg']};
    }}

    /* ---------- Scrollbar polish ---------- */
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-thumb {{ background: {T['border']}; border-radius: 8px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}

    /* ---------- Chart containers as cards ---------- */
    [data-testid="stPlotlyChart"] {{
        background-color: {T['card']};
        border: 1px solid {T['border']};
        border-radius: 16px;
        padding: 10px;
        box-shadow: 0 1px 2px {T['shadow']}, 0 4px 16px {T['shadow']};
    }}
    </style>
""", unsafe_allow_html=True)


# ==================================================================
# SIDEBAR
# ==================================================================
with st.sidebar:
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown('<div class="app-title" style="font-size:20px;">AlphaSage</div>', unsafe_allow_html=True)
        st.caption("AI-powered investment intelligence")
    with col_b:
        dark_toggle = st.toggle("Dark", value=st.session_state.dark_mode, key="dark_mode_toggle")
        if dark_toggle != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_toggle
            st.rerun()

    st.divider()

    st.markdown("**PLATFORM**")
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "Portfolio"
    for nav_item in ["Dashboard", "Scanner"]:
        if st.button(nav_item, key=f"nav_{nav_item.lower().replace(' ', '_')}", use_container_width=True):
            st.session_state.nav_page = nav_item
            st.rerun()
    st.markdown("**MARKETS**")
    for nav_item in ["Global Markets", "Portfolio", "Watchlist", "News", "Research"]:
        if st.button(nav_item, key=f"nav_{nav_item.lower().replace(' ', '_')}", use_container_width=True):
            st.session_state.nav_page = nav_item
            st.rerun()
    nav_page = st.session_state.nav_page
    if nav_page != "Portfolio":
        st.info(f"{nav_page} is part of the AlphaSage workspace and will be enabled as its data service is implemented.")
        st.stop()

    st.markdown(
        '<div class="custom-card"><strong>✦ Get early access</strong><br>'
        '<span style="color:#94A3B8;font-size:12px">Join the AlphaSage research community for advanced AI features.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("**ACCOUNT**")
    st.markdown(
        '<div class="custom-card" style="margin-top:10px"><strong>Guest mode</strong><br>'
        '<span style="color:#94A3B8;font-size:12px">Sign in to sync your portfolio and watchlist across devices.</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("**DATA SOURCE**")
    kite_available = is_kite_configured()
    if kite_available:
        use_real_kite = st.toggle("Use real Zerodha holdings", value=True)
        st.caption("Connected to your Zerodha account.")
    else:
        use_real_kite = False
        st.caption("Zerodha not connected. Using simulated portfolio (see README to connect, free).")

    st.divider()
    st.markdown("**MANAGE PORTFOLIO**")

    if use_real_kite:
        st.caption("Managed directly in Kite while real holdings are active.")
    else:
        with st.expander("Add New Stock", expanded=False):
            with st.form("add_stock_form", clear_on_submit=True):
                new_symbol = st.text_input("Stock Symbol (e.g. WIPRO)")
                new_name = st.text_input("Company Name (optional)")
                new_qty = st.number_input("Quantity", min_value=0.0, step=1.0)
                new_price = st.number_input("Buy Price", min_value=0.0, step=1.0)
                new_date = st.date_input("Buy Date", value=date.today())
                submitted = st.form_submit_button("Add Stock")
                if submitted:
                    if new_symbol and new_qty > 0 and new_price > 0:
                        add_stock(new_symbol, new_name, new_qty, new_price, str(new_date))
                        st.success(f"{new_symbol} added.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Symbol, quantity aur price bharo.")

        with st.expander("Remove Stock", expanded=False):
            current_data = load_portfolio_raw()
            symbols = [h["symbol"] for h in current_data["holdings"]]
            if symbols:
                to_remove = st.selectbox("Select stock to remove", options=symbols)
                if st.button("Remove Selected Stock"):
                    remove_stock(to_remove)
                    st.success(f"{to_remove} removed.")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.info("Portfolio khali hai.")

    st.divider()
    st.markdown("**NOTIFICATION SETTINGS**")
    loss_threshold = st.slider("Alert if a stock falls below (%)", min_value=-50, max_value=-1, value=-10)
    gain_threshold = st.slider("Alert if a stock rises above (%)", min_value=1, max_value=100, value=15)

    st.divider()
    if st.button("Refresh Prices"):
        st.cache_data.clear()
        st.rerun()


# ==================================================================
# DATA LOADING
# ==================================================================
@st.cache_data(ttl=15)
def load_portfolio(from_kite: bool):
    if from_kite:
        try:
            holdings = fetch_real_holdings()
        except Exception as e:
            st.error(f"Kite fetch failed: {e}. Falling back to simulated portfolio.")
            holdings = load_portfolio_raw()["holdings"]
    else:
        holdings = load_portfolio_raw()["holdings"]

    if not holdings:
        return []
    return get_portfolio_with_live_prices(holdings)


with st.spinner("Fetching live prices..."):
    try:
        portfolio = load_portfolio(use_real_kite)
    except Exception as e:
        st.error(f"Price fetch failed (check internet connection): {e}")
        st.stop()

if not portfolio:
    st.warning("Portfolio khali hai. Sidebar se 'Add New Stock' karke shuru karo.")
    st.stop()

df_portfolio = pd.DataFrame(portfolio)
alerts = check_alerts(portfolio, loss_threshold=loss_threshold, gain_threshold=gain_threshold)


# ==================================================================
# HEADER ROW: title + notification bell
# ==================================================================
col_title, col_export, col_import, col_bell = st.columns([4.2, 1.2, 1.2, 1])
with col_title:
    st.markdown('<p class="app-title">Portfolio</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-subtitle"><span class="live-dot"></span> Track holdings, cost basis, allocation, and portfolio intelligence</p>', unsafe_allow_html=True)

with col_export:
    export_df = pd.DataFrame(portfolio)
    export_columns = ["symbol", "name", "quantity", "avg_buy_price", "buy_date", "sector"]
    st.download_button(
        "Export CSV",
        export_df.reindex(columns=export_columns).to_csv(index=False),
        file_name="alphasage-portfolio.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_import:
    with st.popover("Import CSV", use_container_width=True):
        uploaded_csv = st.file_uploader("Choose a portfolio CSV", type="csv")
        if uploaded_csv is not None:
            try:
                imported = pd.read_csv(uploaded_csv)
                required = {"symbol", "name", "quantity", "avg_buy_price"}
                if not required.issubset(imported.columns):
                    st.error("CSV must include symbol, name, quantity, and avg_buy_price columns.")
                elif st.button("Confirm import", use_container_width=True):
                    for _, item in imported.iterrows():
                        add_stock(
                            str(item["symbol"]), str(item.get("name", "")),
                            float(item["quantity"]), float(item["avg_buy_price"]),
                            str(item.get("buy_date", date.today())), str(item.get("sector", "Other")),
                        )
                    st.success("Portfolio imported.")
                    st.cache_data.clear()
                    st.rerun()
            except (ValueError, TypeError, KeyError) as error:
                st.error(f"Could not import CSV: {error}")

with col_bell:
    bell_label = f"Notifications ({len(alerts)})" if alerts else "Notifications"
    with st.popover(bell_label, use_container_width=True):
        st.markdown("**Alerts**")
        if alerts:
            for a in alerts:
                css_class = "notif-loss" if a["type"] == "loss" else "notif-gain"
                st.markdown(f'<div class="{css_class}">{a["message"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="notif-empty">No alerts right now. You\'ll see a notification here when a stock '
                        f'moves beyond {loss_threshold}% or {gain_threshold}% from your buy price.</div>', unsafe_allow_html=True)
        st.caption("Change thresholds anytime from the sidebar under Notification Settings.")


# ==================================================================
# TICKER BAR
# ==================================================================
ticker_items = ""
for _, row in df_portfolio.iterrows():
    pnl_pct = row["pnl_pct"]
    if pd.isna(pnl_pct):
        ticker_items += f'<span class="ticker-item">{row["symbol"].replace(".NS","")} <span>Data unavailable</span></span>'
        continue
    css = "ticker-up" if pnl_pct >= 0 else "ticker-down"
    arrow = "▲" if pnl_pct >= 0 else "▼"
    ticker_items += f'<span class="ticker-item">{row["symbol"].replace(".NS","")} <span class="{css}">{arrow} {abs(pnl_pct)}%</span></span>'

st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker-move">{ticker_items}</div>
    </div>
""", unsafe_allow_html=True)


# ==================================================================
# TOP METRICS
# ==================================================================
total_invested = df_portfolio["invested_value"].sum()
total_current = df_portfolio["current_value"].sum(min_count=1)
if pd.isna(total_current):
    total_current = None
total_pnl = (total_current - total_invested) if total_current is not None else None
total_pnl_pct = (total_pnl / total_invested * 100) if total_pnl is not None and total_invested else None

m1, m2, m3, m4 = st.columns(4)
m1.metric("Portfolio Value", f"₹{total_current:,.0f}" if total_current is not None else "Unavailable")
m2.metric("Total Invested", f"₹{total_invested:,.0f}")
m3.metric("Total P&L", f"₹{total_pnl:,.0f}" if total_pnl is not None else "Unavailable", f"{total_pnl_pct:.2f}%" if total_pnl_pct is not None else None)
m4.metric("Holdings", f"{len(df_portfolio)}")

st.write("")

# ------------------------------------------------------------------
# AlphaSage portfolio intelligence cards
# ------------------------------------------------------------------
best, worst = performers(portfolio)
diversification = diversification_score(portfolio)
risk = risk_score(portfolio)

best_label = f"{best['name']} ({best['pnl_pct']:+.2f}%)" if best else "Unavailable"
worst_label = f"{worst['name']} ({worst['pnl_pct']:+.2f}%)" if worst else "Unavailable"
diversification_label = f"{diversification}/100" if diversification is not None else "Unavailable"
risk_label = f"{risk}/100" if risk is not None else "Unavailable"
risk_caption = "Lower is better" if risk is not None else "Waiting for market data"
diversification_caption = "Higher is better" if diversification is not None else "Waiting for market data"
st.markdown('<div class="section-title">Portfolio Intelligence</div>', unsafe_allow_html=True)
i1, i2, i3, i4 = st.columns(4)
i1.metric("Best Performer", best_label)
i2.metric("Worst Performer", worst_label)
i3.metric("Diversification Score", diversification_label, diversification_caption)
i4.metric("Risk Score", risk_label, risk_caption)


# ==================================================================
# PORTFOLIO PERFORMANCE CHART + ALLOCATION DONUT
# ==================================================================
col_chart, col_donut = st.columns([2.2, 1])

with col_chart:
    st.markdown('<div class="section-title">Portfolio Performance (6 Months)</div>', unsafe_allow_html=True)
    with st.spinner("Building performance chart..."):
        history = get_portfolio_value_history(portfolio, period="6mo")

    if not history.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=history["Date"], y=history["Value"],
            mode="lines",
            line=dict(color=T["up"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(34,197,94,0.15)" if st.session_state.dark_mode else "rgba(22,163,74,0.12)",
            name="Portfolio Value"
        ))
        fig.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor=T["card"],
            paper_bgcolor=T["card"],
            font=dict(color=T["subtext"]),
            xaxis=dict(gridcolor=T["border"], showgrid=False),
            yaxis=dict(gridcolor=T["border"], showgrid=True, tickprefix="₹"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough historical data to build the chart yet.")

with col_donut:
    st.markdown('<div class="section-title">Portfolio Allocation</div>', unsafe_allow_html=True)
    donut = go.Figure(data=[go.Pie(
        labels=df_portfolio["name"],
         values=df_portfolio["current_value"].fillna(0),
        hole=0.62,
        marker=dict(colors=["#16A34A", "#38BDF8", "#F59E0B", "#8B5CF6", "#EC4899", "#0EA5E9", "#EF4444"]),
        textinfo="none"
    )])
    donut.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(size=10, color=T["text"])),
        paper_bgcolor=T["card"],
    )
    st.plotly_chart(donut, use_container_width=True)

st.write("")

# ==================================================================
# WATCHLIST (Holdings table)
# ==================================================================
st.markdown('<div class="section-title">Watchlist</div>', unsafe_allow_html=True)

display_df = df_portfolio[["name", "symbol", "quantity", "avg_buy_price",
                            "current_price", "current_value", "pnl", "pnl_pct"]].copy()
display_df.columns = ["Stock", "Symbol", "Qty", "Avg Buy Price", "Current Price",
                       "Market Value", "P&L", "P&L %"]

numeric_cols = ["Qty", "Avg Buy Price", "Current Price", "Market Value", "P&L", "P&L %"]
for col in numeric_cols:
    display_df[col] = display_df[col].round(2)

st.dataframe(
    display_df.style.format({
        "Qty": "{:.2f}",
        "Avg Buy Price": "₹{:.2f}",
        "Current Price": "₹{:.2f}",
        "Market Value": "₹{:.2f}",
        "P&L": "₹{:.2f}",
        "P&L %": "{:.2f}%",
    }).map(
        lambda v: f"color: {T['up']}; font-weight:600" if isinstance(v, (int, float)) and v > 0 else (f"color: {T['down']}; font-weight:600" if isinstance(v, (int, float)) and v < 0 else ""),
        subset=["P&L", "P&L %"]
    ),
    use_container_width=True, hide_index=True
)

st.write("")

# ==================================================================
# STOCK DEEP DIVE
# ==================================================================
st.markdown('<div class="section-title">Stock Deep Dive</div>', unsafe_allow_html=True)

selected_stock = st.selectbox(
    "Select a stock to analyze",
    options=df_portfolio["symbol"].tolist(),
    format_func=lambda x: df_portfolio[df_portfolio["symbol"] == x]["name"].values[0]
)

stock_info = df_portfolio[df_portfolio["symbol"] == selected_stock].iloc[0]
company_name = stock_info["name"]

col_left, col_right = st.columns([2, 1])

with st.spinner(f"Loading {company_name} data..."):
    hist_df = get_historical_data(selected_stock, period="6mo")

with col_left:
    st.markdown(f"**{company_name} — Price Chart**")
    if not hist_df.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=hist_df["Date"], open=hist_df["Open"], high=hist_df["High"],
            low=hist_df["Low"], close=hist_df["Close"], name=selected_stock,
            increasing_line_color=T["up"], decreasing_line_color=T["down"],
        )])
        fig.add_hline(y=stock_info["avg_buy_price"], line_dash="dash", line_color=T["accent"],
                      annotation_text=f"Buy Price: ₹{stock_info['avg_buy_price']}")
        fig.update_layout(
            height=400, xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor=T["card"], paper_bgcolor=T["card"],
            font=dict(color=T["subtext"]),
            xaxis=dict(gridcolor=T["border"]), yaxis=dict(gridcolor=T["border"]),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Historical data not available.")

with col_right:
    st.markdown("**AI Insights**")

    with st.spinner("Analyzing news sentiment..."):
        sentiment_data = get_stock_sentiment_summary(company_name)

    sentiment_color = {"Positive": T["up"], "Negative": T["down"], "Neutral": T["subtext"]}
    color = sentiment_color.get(sentiment_data["overall_sentiment"], T["subtext"])
    st.markdown(f"News Sentiment: <span style='color:{color}; font-weight:700'>{sentiment_data['overall_sentiment']}</span>", unsafe_allow_html=True)
    st.caption(f"Score: {sentiment_data['average_score']} (range: -1 to +1)")

    with st.expander("View analyzed headlines"):
        for h in sentiment_data["headlines_analyzed"]:
            st.write(f"- {h['text']} — *{h['label']}*")

    st.divider()

    with st.spinner("Running price prediction model..."):
        pred_data = get_prediction(hist_df, symbol=selected_stock) if not hist_df.empty else {"predicted_price": None, "trend": None, "method": "N/A"}

    trend_color = T["up"] if pred_data["trend"] == "Up" else (T["down"] if pred_data["trend"] == "Down" else T["subtext"])
    predicted_label = f"₹{pred_data['predicted_price']}" if pred_data["predicted_price"] is not None else "Unavailable"
    st.markdown(f"Predicted Next Price: **{predicted_label}**")
    st.markdown(f"Trend: <span style='color:{trend_color}; font-weight:700'>{pred_data['trend']}</span>", unsafe_allow_html=True)
    st.caption(f"Model: {pred_data['method']}")

    st.divider()

    if sentiment_data["overall_sentiment"] == "Positive" and pred_data["trend"] == "Up":
        st.success("Signal: Bullish (Buy/Hold)")
    elif sentiment_data["overall_sentiment"] == "Negative" and pred_data["trend"] == "Down":
        st.error("Signal: Bearish (Caution/Sell)")
    else:
        st.info("Signal: Mixed (Hold)")

st.write("")

# ==================================================================
# MODEL EVALUATION + BACKTESTING
# ==================================================================
st.markdown('<div class="section-title">Model Evaluation & Backtest</div>', unsafe_allow_html=True)
st.caption(f"How well does the prediction model actually perform on {company_name}'s historical data?")

with st.spinner("Running backtest..."):
    model_bt, scaler_bt = load_saved_model(selected_stock)
    backtest_result = None
    if model_bt is not None and not hist_df.empty:
        backtest_result = evaluate_and_backtest(hist_df, model_bt, scaler_bt)

if backtest_result:
    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    bcol1.metric("RMSE", f"₹{backtest_result['rmse']}")
    bcol2.metric("MAE", f"₹{backtest_result['mae']}")
    bcol3.metric("Strategy Return", f"{backtest_result['strategy_return_pct']}%")
    bcol4.metric("Buy & Hold Return", f"{backtest_result['buy_hold_return_pct']}%")

    fig_bt = go.Figure()
    fig_bt.add_trace(go.Scatter(x=list(range(len(backtest_result["actual"]))), y=backtest_result["actual"],
                                 mode="lines", name="Actual Price", line=dict(color=T["text"], width=2)))
    fig_bt.add_trace(go.Scatter(x=list(range(len(backtest_result["predicted"]))), y=backtest_result["predicted"],
                                 mode="lines", name="Predicted Price", line=dict(color=T["accent"], width=2, dash="dot")))
    fig_bt.update_layout(
        height=300, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor=T["card"], paper_bgcolor=T["card"], font=dict(color=T["subtext"]),
        xaxis=dict(title="Test period (days)", gridcolor=T["border"]),
        yaxis=dict(title="Price (₹)", gridcolor=T["border"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_bt, use_container_width=True)
    st.caption("RMSE/MAE measured on a held-out test set (last 20% of data, not seen during training). "
               "Strategy: go long only on days the model predicts an increase; compared against simple buy-and-hold.")
else:
    st.info("Backtest needs a trained model. Run `python src/train_models.py` once to pre-train and save models for your holdings, then refresh this page.")

st.write("")

# ==================================================================
# EXPLAINABILITY (SHAP)
# ==================================================================
st.markdown('<div class="section-title">Why this prediction? (Explainability)</div>', unsafe_allow_html=True)

if SHAP_AVAILABLE:
    with st.spinner("Computing feature importance..."):
        importance = explain_prediction(hist_df, sentiment_score=sentiment_data["average_score"])

    if importance:
        feat_names = list(importance.keys())
        feat_values = list(importance.values())
        colors = [T["up"] if v > 0 else T["down"] for v in feat_values]

        fig_shap = go.Figure(go.Bar(
            x=feat_values, y=feat_names, orientation="h", marker_color=colors
        ))
        fig_shap.update_layout(
            height=280, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor=T["card"], paper_bgcolor=T["card"], font=dict(color=T["subtext"]),
            xaxis=dict(title="Impact on predicted price (SHAP value)", gridcolor=T["border"]),
        )
        st.plotly_chart(fig_shap, use_container_width=True)
        st.caption("Computed using a Random Forest surrogate model (SHAP on LSTM directly is computationally expensive). "
                   "Green bars push the price prediction up, red bars push it down.")
    else:
        st.info("Not enough data to compute feature importance for this stock yet.")
else:
    st.info("Install the 'shap' package (already in requirements.txt) to enable this section.")

st.write("")

# ==================================================================
# MULTI-STOCK COMPARISON
# ==================================================================
st.markdown('<div class="section-title">Compare Stocks</div>', unsafe_allow_html=True)

compare_symbols = st.multiselect(
    "Select stocks to compare (normalized % change over 6 months)",
    options=df_portfolio["symbol"].tolist(),
    default=df_portfolio["symbol"].tolist()[:min(3, len(df_portfolio))],
    format_func=lambda x: df_portfolio[df_portfolio["symbol"] == x]["name"].values[0]
)

if len(compare_symbols) >= 2:
    fig_compare = go.Figure()
    compare_colors = ["#16A34A", "#38BDF8", "#F59E0B", "#8B5CF6", "#EC4899"]

    for idx, sym in enumerate(compare_symbols):
        with st.spinner(f"Loading {sym}..."):
            hist = get_historical_data(sym, period="6mo")
        if not hist.empty:
            normalized = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
            name = df_portfolio[df_portfolio["symbol"] == sym]["name"].values[0]
            fig_compare.add_trace(go.Scatter(
                x=hist["Date"], y=normalized, mode="lines", name=name,
                line=dict(color=compare_colors[idx % len(compare_colors)], width=2)
            ))

    fig_compare.update_layout(
        height=380, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor=T["card"], paper_bgcolor=T["card"], font=dict(color=T["subtext"]),
        xaxis=dict(gridcolor=T["border"]),
        yaxis=dict(title="% change since 6 months ago", gridcolor=T["border"], ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_compare, use_container_width=True)

    compare_table = df_portfolio[df_portfolio["symbol"].isin(compare_symbols)][
        ["name", "symbol", "current_price", "pnl_pct"]
    ].copy()
    compare_table.columns = ["Stock", "Symbol", "Current Price", "P&L %"]
    st.dataframe(compare_table.style.format({"Current Price": "₹{:.2f}", "P&L %": "{:.2f}%"}), use_container_width=True, hide_index=True)
else:
    st.caption("Select at least 2 stocks to compare.")

st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data: yfinance (live) | Sentiment: TextBlob/NewsAPI | Prediction: LSTM | Explainability: SHAP")
