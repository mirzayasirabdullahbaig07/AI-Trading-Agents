"""
app.py  —  AI Trading Agent Dashboard
Run: streamlit run app.py

Developer: set your OpenAI key once in config.py — users never see it.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from config import OPENAI_API_KEY, STARTING_BALANCE
from kraken_client import get_ticker, get_ohlc, add_indicators
from ai_agent import analyze_market, portfolio_summary
from paper_trader import PaperTrader

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Trading Agent", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.buy  {background:#0d2e0d;color:#4caf50;padding:6px 20px;border-radius:8px;font-size:1.4rem;font-weight:700;display:inline-block}
.sell {background:#2e0d0d;color:#f44336;padding:6px 20px;border-radius:8px;font-size:1.4rem;font-weight:700;display:inline-block}
.hold {background:#2e2a0d;color:#ff9800;padding:6px 20px;border-radius:8px;font-size:1.4rem;font-weight:700;display:inline-block}
</style>
""", unsafe_allow_html=True)

# ── Guard: make sure developer filled in the key ──────────────────────────────
if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your"):
    st.error("⚠️ Developer: open **config.py** and paste your real OpenAI API key.")
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    if "trader"  not in st.session_state:
        st.session_state.trader  = PaperTrader(STARTING_BALANCE).dump()
    if "signal"  not in st.session_state:
        st.session_state.signal  = None
    if "signals" not in st.session_state:
        st.session_state.signals = []
    if "ticker"  not in st.session_state:
        st.session_state.ticker  = None
    if "df"      not in st.session_state:
        st.session_state.df      = pd.DataFrame()

init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 AI Trading Agent")
    st.caption("Live Kraken data · GPT-4o signals · Paper trading")
    st.divider()

    st.subheader("📈 Market")
    pair = st.selectbox("Pair", ["XBTUSD","ETHUSD","SOLUSD","ADAUSD","DOTUSD","LINKUSD"])
    interval_label = st.selectbox("Candle interval", ["1 min","5 min","15 min","1 hour","4 hours"], index=3)
    interval = {"1 min":1,"5 min":5,"15 min":15,"1 hour":60,"4 hours":240}[interval_label]

    st.divider()

    st.subheader("💼 Portfolio")
    pt = PaperTrader()
    pt.load(st.session_state.trader)
    ticker_val = st.session_state.ticker or {}
    prices     = {pair: ticker_val.get("last", 0)} if ticker_val else {}

    st.metric("Cash",            f"${pt.state['balance']:,.2f}")
    st.metric("Portfolio value", f"${pt.portfolio_value(prices):,.2f}")
    st.metric("Return",          f"{pt.return_pct(prices):+.2f}%")

    trade_size = st.slider("Trade size (% of cash)", 5, 50, 20, 5)
    auto       = st.toggle("Auto-execute signals", value=False)

    if st.button("🔄 Reset portfolio"):
        st.session_state.trader  = PaperTrader(STARTING_BALANCE).dump()
        st.session_state.signals = []
        st.session_state.signal  = None
        st.rerun()

    st.divider()
    st.caption("Paper trading only — no real money")
    st.caption("lablab.ai AI Trading Agents Hackathon")

# ── Main header ───────────────────────────────────────────────────────────────
st.title(f"🤖 AI Trading Agent — {pair}")

c1, c2 = st.columns(2)
fetch   = c1.button("📡 Fetch market data", use_container_width=True)
analyze = c2.button("🧠 Analyze with AI",   use_container_width=True, type="primary")

# ── Fetch data ────────────────────────────────────────────────────────────────
if fetch or analyze:
    with st.spinner("Fetching Kraken data..."):
        ticker = get_ticker(pair)
        df     = get_ohlc(pair, interval)
        if not df.empty:
            df = add_indicators(df)
        st.session_state.ticker = ticker
        st.session_state.df     = df

ticker = st.session_state.ticker
df     = st.session_state.df

# ── Ticker strip ──────────────────────────────────────────────────────────────
if ticker and not ticker.get("error"):
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Price",    f"${ticker['last']:,.2f}")
    m2.metric("24h High", f"${ticker['high']:,.2f}")
    m3.metric("24h Low",  f"${ticker['low']:,.2f}")
    m4.metric("Volume",   f"{ticker['volume']:,.0f}")
    m5.metric("Spread",   f"${ticker['ask']-ticker['bid']:,.2f}")
elif ticker and ticker.get("error"):
    st.error(f"Kraken error: {ticker['error']}")

st.divider()

# ── Charts + Signal ───────────────────────────────────────────────────────────
left, right = st.columns([3, 1])

with left:
    if not df.empty:
        tab1, tab2, tab3 = st.tabs(["📈 Price + Bollinger", "📊 RSI", "🔀 MACD"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df["time"], open=df["open"], high=df["high"],
                low=df["low"], close=df["close"], name=pair,
                increasing_line_color="#4caf50", decreasing_line_color="#f44336",
            ))
            if "bb_upper" in df.columns:
                fig.add_trace(go.Scatter(x=df["time"], y=df["bb_upper"], name="BB Upper",
                    line=dict(color="rgba(100,149,237,0.5)", dash="dash")))
                fig.add_trace(go.Scatter(x=df["time"], y=df["bb_lower"], name="BB Lower",
                    line=dict(color="rgba(100,149,237,0.5)", dash="dash"),
                    fill="tonexty", fillcolor="rgba(100,149,237,0.06)"))
                fig.add_trace(go.Scatter(x=df["time"], y=df["bb_mid"], name="BB Mid",
                    line=dict(color="rgba(100,149,237,0.3)"), showlegend=False))
            fig.update_layout(height=380, template="plotly_dark",
                              margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            if "rsi" in df.columns:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df["time"], y=df["rsi"], name="RSI",
                                          line=dict(color="#7c4dff")))
                fig2.add_hline(y=70, line_dash="dash", line_color="red",   annotation_text="Overbought 70")
                fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold 30")
                fig2.update_layout(height=280, template="plotly_dark",
                                   margin=dict(l=0,r=0,t=10,b=0), yaxis_range=[0,100])
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Not enough candles for RSI yet.")

        with tab3:
            if "macd" in df.columns:
                colors = ["#4caf50" if v >= 0 else "#f44336" for v in df["macd_hist"].fillna(0)]
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=df["time"], y=df["macd"],        name="MACD",   line=dict(color="#00bcd4")))
                fig3.add_trace(go.Scatter(x=df["time"], y=df["macd_signal"], name="Signal", line=dict(color="#ff9800")))
                fig3.add_trace(go.Bar(    x=df["time"], y=df["macd_hist"],   name="Hist",   marker_color=colors))
                fig3.update_layout(height=280, template="plotly_dark", margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Not enough candles for MACD yet.")
    else:
        st.info("👆 Click **Fetch market data** to load charts.")

# ── AI Signal panel ───────────────────────────────────────────────────────────
with right:
    st.subheader("AI Signal")

    if analyze:
        if df.empty or not ticker or ticker.get("error"):
            st.error("Fetch market data first.")
        else:
            with st.spinner("GPT-4o is analyzing..."):
                last = df.iloc[-1]
                def safe(col):
                    try: return round(float(last[col]), 4)
                    except: return None

                indics = {k: safe(k) for k in
                          ["rsi","macd","macd_signal","macd_hist","bb_upper","bb_mid","bb_lower"]}
                recent = df.tail(5)[["time","open","high","low","close","volume"]].copy()
                recent["time"] = recent["time"].astype(str)

                sig = analyze_market(
                    api_key=OPENAI_API_KEY,   # ← from config.py, never shown to users
                    pair=pair,
                    ticker=ticker,
                    indicators=indics,
                    recent_candles=recent.to_dict(orient="records"),
                )
                st.session_state.signal  = sig
                st.session_state.signals.append(sig)

                if auto and sig["signal"] in ("BUY","SELL"):
                    pt = PaperTrader(); pt.load(st.session_state.trader)
                    if sig["signal"] == "BUY":
                        pt.buy(pair, ticker["last"], pt.state["balance"] * (trade_size/100), sig)
                    else:
                        pt.sell(pair, ticker["last"], sig)
                    st.session_state.trader = pt.dump()
                    st.toast(f"Auto-executed {sig['signal']}", icon="✅")

    sig = st.session_state.signal
    if sig:
        css = {"BUY":"buy","SELL":"sell","HOLD":"hold"}.get(sig["signal"],"hold")
        st.markdown(f'<div class="{css}">{sig["signal"]}</div>', unsafe_allow_html=True)
        st.metric("Confidence", f"{sig.get('confidence',0)}%")
        st.metric("Risk",       f"{sig.get('risk_score',5)}/10")
        st.caption("**Reasoning**")
        st.write(sig.get("reasoning",""))
        if sig.get("key_factors"):
            st.caption("**Key factors**")
            for f in sig["key_factors"]:
                st.write(f"• {f}")
        if sig.get("entry_price"):
            st.caption("**Levels**")
            st.write(f"Entry:  ${sig['entry_price']:,.2f}")
            st.write(f"Stop:   ${sig.get('stop_loss',0):,.2f}")
            st.write(f"Target: ${sig.get('take_profit',0):,.2f}")

        st.divider()
        if ticker and not ticker.get("error"):
            if st.button("✅ BUY now", type="primary", use_container_width=True):
                pt = PaperTrader(); pt.load(st.session_state.trader)
                res = pt.buy(pair, ticker["last"], pt.state["balance"]*(trade_size/100), sig)
                st.session_state.trader = pt.dump()
                st.success(f"Bought {res['trade']['qty']:.5f} @ ${ticker['last']:,.2f}") if res["ok"] else st.error(res["msg"])

            if st.button("🔴 SELL now", use_container_width=True):
                pt = PaperTrader(); pt.load(st.session_state.trader)
                res = pt.sell(pair, ticker["last"], sig)
                st.session_state.trader = pt.dump()
                if res["ok"]:
                    (st.success if res["pnl"] >= 0 else st.error)(f"PnL: ${res['pnl']:+,.2f}")
                else:
                    st.error(res["msg"])
    else:
        st.info("Click **Analyze with AI** to get a signal.")

# ── Portfolio ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📊 Portfolio")

pt = PaperTrader(); pt.load(st.session_state.trader)
ticker_now = st.session_state.ticker or {}
prices     = {pair: ticker_now.get("last", 0)} if ticker_now else {}

p1,p2,p3,p4 = st.columns(4)
p1.metric("Total value",    f"${pt.portfolio_value(prices):,.2f}",
          delta=f"${pt.portfolio_value(prices)-pt.state['initial_balance']:+,.2f}")
p2.metric("Cash",           f"${pt.state['balance']:,.2f}")
p3.metric("Unrealized PnL", f"${pt.unrealized_pnl(prices):+,.2f}")
p4.metric("Realized PnL",   f"${pt.state['realized_pnl']:+,.2f}")

if pt.state["positions"]:
    st.subheader("Open positions")
    rows = []
    for p, pos in pt.state["positions"].items():
        cur = prices.get(p, pos["avg_entry"])
        pnl = pos["qty"] * (cur - pos["avg_entry"])
        rows.append({"Pair": p, "Qty": f"{pos['qty']:.5f}",
                     "Entry": f"${pos['avg_entry']:,.2f}", "Now": f"${cur:,.2f}",
                     "PnL": f"${pnl:+,.2f}",
                     "PnL%": f"{pnl/(pos['qty']*pos['avg_entry'])*100:+.2f}%"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

trades = pt.state["trades"]
if trades:
    st.subheader("Trade history")
    display = [{"#": t["id"], "Type": t["type"], "Pair": t["pair"],
                "Price": f"${t['price']:,.2f}", "Qty": f"{t['qty']:.5f}",
                "Value": f"${t['usd']:,.2f}",
                "PnL":   f"${t['pnl']:+,.2f}" if t["pnl"] else "—",
                "Confidence": f"{t['confidence']}%", "Time": t["time"]}
               for t in reversed(trades[-30:])]
    st.dataframe(pd.DataFrame(display), use_container_width=True, hide_index=True)

    sells = [t for t in trades if t["type"] == "SELL"]
    if len(sells) >= 2:
        pnl_df = pd.DataFrame({"Trade":[t["id"] for t in sells],"PnL":[t["pnl"] for t in sells]})
        fig_p  = px.bar(pnl_df, x="Trade", y="PnL", color="PnL",
                        color_continuous_scale=["#f44336","#4caf50"],
                        title="PnL per closed trade", template="plotly_dark")
        fig_p.update_layout(height=230, margin=dict(l=0,r=0,t=30,b=0), showlegend=False)
        st.plotly_chart(fig_p, use_container_width=True)

if len(st.session_state.signals) > 1:
    st.subheader("Signal history")
    sh = [{"Signal": s["signal"], "Confidence": f"{s.get('confidence',0)}%",
           "Risk": f"{s.get('risk_score',0)}/10", "Entry": f"${s.get('entry_price',0):,.2f}",
           "Pair": s.get("pair",""), "Time": s.get("timestamp","")[:19]}
          for s in reversed(st.session_state.signals[-10:])]
    st.dataframe(pd.DataFrame(sh), use_container_width=True, hide_index=True)

if trades:
    if st.button("🤖 AI portfolio summary"):
        with st.spinner("Generating summary..."):
            st.info(portfolio_summary(OPENAI_API_KEY, trades, prices))

st.divider()
st.caption(f"Updated {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC · Paper trading · lablab.ai Hackathon")
