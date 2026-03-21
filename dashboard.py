import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

LOGS_DIR = "logs"
SIGNALS_FILE = os.path.join(LOGS_DIR, "signals.csv")
SUMMARY_FILE = os.path.join(LOGS_DIR, "daily_summary.txt")

st.set_page_config(page_title="Neural Network for Crypto", page_icon="📈", layout="wide")


def load_csv(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def inject_styles():
    st.markdown(
        """
        <style>
            .main { background-color: #0e1117; }
            .hero-box {
                padding: 1.2rem 1.4rem;
                border-radius: 18px;
                background: linear-gradient(135deg, #121826 0%, #0f172a 100%);
                border: 1px solid rgba(255,255,255,0.08);
                margin-bottom: 1rem;
            }
            .metric-chip {
                display: inline-block;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                background: rgba(99, 102, 241, 0.15);
                color: #c7d2fe;
                font-size: 0.85rem;
                margin-right: 0.4rem;
                margin-bottom: 0.4rem;
            }
            .market-card {
                background: linear-gradient(180deg, #121826 0%, #111827 100%);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 20px;
                padding: 1rem;
                margin-bottom: 1rem;
                box-shadow: 0 8px 20px rgba(0,0,0,0.18);
            }
            .market-title {
                font-size: 1.05rem;
                font-weight: 700;
                color: #f8fafc;
                margin-bottom: 0.65rem;
                line-height: 1.35;
            }
            .signal-badge {
                display: inline-block;
                padding: 0.35rem 0.65rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
                margin-right: 0.35rem;
                margin-bottom: 0.45rem;
            }
            .badge-watch { background: rgba(245, 158, 11, 0.16); color: #fbbf24; }
            .badge-strong { background: rgba(16, 185, 129, 0.16); color: #34d399; }
            .badge-top { background: rgba(59, 130, 246, 0.16); color: #60a5fa; }
            .badge-ignore { background: rgba(148, 163, 184, 0.16); color: #cbd5e1; }
            .meta-line {
                color: #cbd5e1;
                font-size: 0.92rem;
                margin-bottom: 0.3rem;
            }
            .reason-box {
                margin-top: 0.7rem;
                color: #94a3b8;
                font-size: 0.88rem;
                padding: 0.7rem 0.8rem;
                border-radius: 14px;
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.05);
            }
            .section-title {
                font-size: 1.1rem;
                font-weight: 700;
                margin-top: 0.5rem;
                margin-bottom: 0.9rem;
                color: #f8fafc;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, help_text=None):
    st.metric(label=label, value=value, help=help_text)


def render_header():
    st.markdown(
        """
        <div class="hero-box">
            <h1 style="margin-bottom:0.35rem;">📈 Neural Network for Crypto</h1>
            <div style="color:#94a3b8; font-size:1rem;">
                Real-time public-data research + paper-trading dashboard
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "This interface shows ranked paper-trading opportunities and simulated trades only. "
        "It does not place real bets or connect to a live account."
    )


def render_overview(signals_df, trades_df):
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    top_conf = "-"
    if not signals_df.empty and "confidence" in signals_df.columns:
        try:
            top_conf = f"{float(signals_df['confidence'].max()):.2f}"
        except Exception:
            top_conf = "-"

    with c1:
        metric_card("Ranked Signals", len(signals_df))
    with c2:
        metric_card("Paper Trades", len(trades_df))
    with c3:
        metric_card("Highest Confidence", top_conf)
    with c4:
        metric_card("Last Refresh", datetime.now().strftime("%H:%M:%S"))


def badge_class(label: str) -> str:
    label = str(label).upper()
    if "HIGHEST" in label:
        return "badge-top"
    if "STRONG" in label:
        return "badge-strong"
    if "WATCH" in label:
        return "badge-watch"
    return "badge-ignore"


def render_top_opportunities(signals_df):
    st.markdown('<div class="section-title">Top Paper-Trading Opportunities</div>', unsafe_allow_html=True)
    if signals_df.empty:
        st.warning("No ranked opportunities yet. Run supervisor.py first.")
        return

    sort_df = signals_df.copy()
    if "confidence" in sort_df.columns:
        sort_df = sort_df.sort_values(by="confidence", ascending=False)

    top_df = sort_df.head(8).reset_index(drop=True)
    cols = st.columns(2)

    for idx, (_, row) in enumerate(top_df.iterrows()):
        with cols[idx % 2]:
            label = row.get("signal_label", "UNKNOWN")
            side = row.get("side", "UNKNOWN")
            market = row.get("market", row.get("market_title", "Unknown Market"))
            wallet = row.get("wallet_copied", row.get("trader_wallet", "Unknown"))
            confidence = row.get("confidence", "-")
            reason = row.get("reason", "No reason available")
            market_url = row.get("market_url")

            st.markdown(
                f"""
                <div class="market-card">
                    <div class="market-title">{market}</div>
                    <div>
                        <span class="signal-badge {badge_class(label)}">{label}</span>
                        <span class="signal-badge badge-ignore">Observed side: {side}</span>
                        <span class="signal-badge badge-ignore">Confidence: {confidence}</span>
                    </div>
                    <div class="meta-line"><b>Source wallet:</b> {wallet}</div>
                    <div class="reason-box">{reason}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if pd.notna(market_url) and market_url:
                st.link_button("Open market on Polymarket", market_url, use_container_width=True)


def render_signal_charts(signals_df):
    st.markdown('<div class="section-title">Signal Visualizations</div>', unsafe_allow_html=True)
    if signals_df.empty or "confidence" not in signals_df.columns:
        st.info("No signal chart data yet.")
        return

    chart_df = signals_df.copy().head(25)
    fig = px.bar(
        chart_df,
        x="confidence",
        y="market",
        color="signal_label",
        orientation="h",
        title="Top Ranked Opportunities by Confidence",
    )
    fig.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)


def render_paper_trades(trades_df):
    st.markdown('<div class="section-title">Paper Trade Ledger</div>', unsafe_allow_html=True)
    if trades_df.empty:
        st.warning("No paper trades yet. Run supervisor.py first.")
        return

    st.dataframe(trades_df.sort_index(ascending=False), use_container_width=True, height=420)


def render_trade_chart(trades_df):
    st.markdown('<div class="section-title">Simulated Fill Prices</div>', unsafe_allow_html=True)
    if trades_df.empty or "fill_price" not in trades_df.columns:
        st.info("No fill-price data yet.")
        return

    chart_df = trades_df.copy().tail(30)
    chart_df["trade_index"] = range(1, len(chart_df) + 1)
    fig = px.line(
        chart_df,
        x="trade_index",
        y="fill_price",
        color="side" if "side" in chart_df.columns else None,
        hover_data=[col for col in ["market", "signal_label", "confidence"] if col in chart_df.columns],
        title="Recent Simulated Fill Prices",
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_raw_data(signals_df, trades_df):
    with st.expander("Raw data"):
        st.markdown("**Signals CSV**")
        st.dataframe(signals_df, width="stretch")
        st.markdown("**Paper Trade Ledger**")
        st.dataframe(trades_df, width="stretch")


def main():
    inject_styles()
    render_header()

    refresh_seconds = st.sidebar.slider("Auto-refresh hint (seconds)", min_value=5, max_value=120, value=15)
    st.sidebar.caption(
        "Tip: Streamlit does not auto-refresh by itself here. Re-run manually or use a refresh extension if desired."
    )
    st.sidebar.write(f"Suggested refresh interval: {refresh_seconds}s")

    signals_df = load_csv(SIGNALS_FILE)
    trades_df = load_csv(SUMMARY_FILE)

    render_overview(signals_df, trades_df)

    left, right = st.columns([1.2, 1])
    with left:
        render_top_opportunities(signals_df)
        render_signal_charts(signals_df)
    with right:
        render_paper_trades(trades_df)
        render_trade_chart(trades_df)

    render_raw_data(signals_df, trades_df)


if __name__ == "__main__":
    main()
