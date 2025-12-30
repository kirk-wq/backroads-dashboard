import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. BRANDING & COLORS ---
BR_BLACK, BR_OFF_BLACK, BR_GOLD = "#010101", "#231f1f", "#ab895e"
BR_GRAY, BR_RED, BR_WHITE = "#9f9f9f", "#e51937", "#f1f1f1"

st.set_page_config(page_title="Backroads Reclamation | Debt & Equity Portal", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BR_BLACK}; color: {BR_WHITE}; }}
    section[data-testid="stSidebar"] {{ background-color: {BR_OFF_BLACK} !important; }}
    .stMetric {{ background-color: {BR_OFF_BLACK}; padding: 15px; border-radius: 5px; border-left: 3px solid {BR_GOLD}; }}
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; font-size: 1.8rem !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
if "password_correct" not in st.session_state:
    st.sidebar.title("🔐 Investor Access")
    pw = st.sidebar.text_input("Enter Access Code", type="password")
    if pw == st.secrets["password"]:
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- 3. YEAR-BY-YEAR CONTROLS ---
st.sidebar.header("🕹️ Scenario Controls")
st.sidebar.info("Adjust specific years to test loan repayment and cash cushions.")

# We create a dictionary to store multipliers for each year
mults = {}
tab1, tab2, tab3 = st.sidebar.tabs(["Year 1", "Year 2", "Year 3"])

with tab1:
    mults[0] = {
        "v": st.slider("Y1 Volume Variance", -50, 50, 0, key="v1") / 100,
        "y": st.slider("Y1 Yield Variance", -25, 25, 0, key="y1") / 100,
        "p": st.slider("Y1 Price Variance", -50, 50, 0, key="p1") / 100,
        "c": st.slider("Y1 Cost Variance", -20, 30, 0, key="c1") / 100
    }
with tab2:
    mults[1] = {
        "v": st.slider("Y2 Volume Variance", -50, 50, 0, key="v2") / 100,
        "y": st.slider("Y2 Yield Variance", -25, 25, 0, key="y2") / 100,
        "p": st.slider("Y2 Price Variance", -50, 50, 0, key="p2") / 100,
        "c": st.slider("Y2 Cost Variance", -20, 30, 0, key="c2") / 100
    }
with tab3:
    mults[2] = {
        "v": st.slider("Y3 Volume Variance", -50, 50, 0, key="v3") / 100,
        "y": st.slider("Y3 Yield Variance", -25, 25, 0, key="y3") / 100,
        "p": st.slider("Y3 Price Variance", -50, 50, 0, key="p3") / 100,
        "c": st.slider("Y3 Cost Variance", -20, 30, 0, key="c3") / 100
    }

# --- 4. ENGINE (v5.6 Aligned with ERA Grants) ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
base_rev_targets = [4753166, 12469066, 17820600]
base_margin_targets = [3978038, 10826653, 14805261]
era_grants = [0, 610000, 575000] # Non-operating inflows

results = []
for i in range(3):
    m = mults[i]
    h = base_homes[i] * (1 + m["v"])
    r = [0.5, 0.6, 0.65][i] * (1 + m["y"])
    
    rev_l = (h * 6615 * r * [2.6, 2.82, 3.04][i] * (1 + m["p"]))
    rev_o = (h * 1800) # Tipping + Materials
    total_rev = rev_l + rev_o
    
    costs = (base_rev_targets[i] - base_margin_targets[i]) * (1 + m["v"]) * (1 + m["c"])
    op_margin = total_rev - costs
    total_cash_inflow = op_margin + era_grants[i]
    
    results.append({
        "Year": years[i], 
        "Lumber": rev_l, 
        "Op Margin": op_margin, 
        "ERA Grant": era_grants[i],
        "Total Cash Inflow": total_cash_inflow,
        "Base Plan": base_rev_targets[i]
    })

df = pd.DataFrame(results)

# --- 5. DASHBOARD VIEW ---
st.title("Backroads Reclamation | Debt Service & Cash Flow Portal")
st.markdown("Assess loan repayment capacity by adjusting year-specific operational variables.")

# Metric Row
c1, c2, c3, c4 = st.columns(4)
total_inflow = df['Total Cash Inflow'].sum()
with c1: st.metric("3-Yr Total Cash Inflow", f"${total_inflow/1e6:.2f}M", help="Operating Margin + ERA Grants")
with c2: st.metric("Y2 ERA Grant", "$610K", "Confirmed")
with c3: st.metric("Y3 Total Cash", f"${df.iloc[2]['Total Cash Inflow']/1e6:.2f}M")
with c4: st.metric("Avg. Margin Strength", f"{(df['Op Margin'].sum()/df['Lumber'].sum()*100):.1f}%")

st.divider()

col_main, col_side = st.columns([2, 1])

with col_main:
    # CHART: Cash Breakdown including ERA
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Op Margin'], name='Operating Margin', marker_color=BR_GOLD))
    fig.add_trace(go.Bar(x=df['Year'], y=df['ERA Grant'], name='ERA Reimbursement (Non-Op)', marker_color=BR_WHITE))
    fig.update_layout(title="Total Cash Available for Debt Service", barmode='stack', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with col_side:
    # Liquidity Waterfall
    y2 = df.iloc[1]
    fig_w = go.Figure(go.Waterfall(
        orientation="v", measure=["relative", "relative", "total"],
        x=["Op Margin", "ERA Grant", "CASH AVAILABLE"],
        y=[y2['Op Margin'], y2['ERA Grant'], y2['Total Cash Inflow']],
        totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}
    ))
    fig_w.update_layout(title="Year 2 Liquidity Detail", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_w, use_container_width=True)

# Data Table
with st.expander("📝 View Detailed Cash Flow Table"):
    st.info("Note: ERA Year 4 Reimbursement ($799,872) is not pictured in charts but is confirmed in the project schedule.")
    tdf = df.copy()
    for col in ["Lumber", "Op Margin", "ERA Grant", "Total Cash Inflow", "Base Plan"]:
        tdf[col] = tdf[col].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
