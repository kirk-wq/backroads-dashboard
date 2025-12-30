import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. BRANDING & COLORS ---
BR_BLACK = "#010101"
BR_OFF_BLACK = "#231f1f"
BR_GOLD = "#ab895e"
BR_GRAY = "#9f9f9f"
BR_RED = "#e51937"
BR_WHITE = "#f1f1f1"

st.set_page_config(page_title="Backroads Reclamation | Scenario Manager", layout="wide")

# Custom CSS for Branding
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BR_BLACK}; color: {BR_WHITE}; }}
    section[data-testid="stSidebar"] {{ background-color: {BR_OFF_BLACK} !important; }}
    .stMetric {{ background-color: {BR_OFF_BLACK}; padding: 15px; border-radius: 5px; border-left: 3px solid {BR_GOLD}; }}
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; font-size: 1.8rem !important; }}
    div[data-testid="stMetricLabel"] {{ color: {BR_WHITE} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.sidebar.title("🔐 Access Required")
        pw = st.sidebar.text_input("Enter Access Code", type="password")
        if pw:
            if pw == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.sidebar.error("😕 Access Denied")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. THE LEVERS (CENTERED AT 0%) ---
st.sidebar.header("🕹️ Scenario Adjustments")
st.sidebar.info("Center (0%) is your Base Case Financial Model. Adjust to test sensitivity.")

v_delta = st.sidebar.slider("Volume Variance", -50, 50, 0, format="%d%%")
y_delta = st.sidebar.slider("Recovery Yield Variance", -25, 25, 0, format="%d%%")
p_delta = st.sidebar.slider("Lumber Price Variance", -50, 50, 0, format="%d%%")
t_delta = st.sidebar.slider("Tipping Fee Negotiating Power", -20, 20, 0, format="%d%%")
c_delta = st.sidebar.slider("Direct Cost Variance", -20, 30, 0, format="%d%%")

# Multipliers
vol_m = 1 + (v_delta / 100)
yld_m = 1 + (y_delta / 100)
prc_m = 1 + (p_delta / 100)
tip_m = 1 + (t_delta / 100)
cst_m = 1 + (c_delta / 100)

# --- 4. CALCULATION ENGINE ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
recovery_rates = [0.50, 0.60, 0.65]
base_rev_targets = [4753166, 12469066, 17820600] # From your v5.4

results = []
for i, year in enumerate(years):
    h = base_homes[i] * vol_m
    r = recovery_rates[i] * yld_m
    
    # Revenue (Based on your weighted price growth)
    rev_lumber = (h * 6615 * r * [2.60, 2.82, 3.04][i] * prc_m)
    rev_other = (h * 1200 * tip_m) + (h * 600)
    total_rev = rev_lumber + rev_other
    
    # Margin (Based on your v5.4 costs)
    costs = (h * [1700, 1750, 1850][i] * cst_m)
    margin = total_rev - costs
    
    results.append({
        "Year": year, 
        "Total Revenue": total_rev, 
        "Margin": margin, 
        "Base Case": base_rev_targets[i]
    })

df = pd.DataFrame(results)

# --- 5. INVESTOR VIEW ---
st.title("Backroads Reclamation: Institutional Scenario Planner")
st.caption(f"LIVE TEST: {v_delta}% Volume | {p_delta}% Market Price | {c_delta}% Cost Basis")

# KPI Ribbon
m1, m2, m3, m4 = st.columns(4)
total_actual = df['Total Revenue'].sum()
total_base = sum(base_rev_targets)
rev_variance = ((total_actual / total_base) - 1) * 100

with m1:
    st.metric("3-Year Revenue", f"${total_actual/1e6:.1f}M", f"{rev_variance:.1f}% vs Plan")
with m2:
    st.metric("Year 3 Gross Margin", f"${df.iloc[2]['Margin']/1e6:.1f}M")
with m3:
    st.metric("Year 3 Margin %", f"{(df.iloc[2]['Margin']/df.iloc[2]['Total Revenue'])*100:.1f}%")
with m4:
    st.metric("Revenue per Home", f"${df.iloc[2]['Total Revenue']/(base_homes[2]*vol_m):,.0f}")

st.write("---")

# Main Comparison Chart
col_main, col_side = st.columns([2, 1])

with col_main:
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(x=df['Year'], y=df['Base Case'], name='Financial Model (v5.4)', marker_color=BR_GRAY))
    fig_comp.add_trace(go.Bar(x=df['Year'], y=df['Total Revenue'], name='Live Stress Test', marker_color=BR_GOLD))
    fig_comp.update_layout(
        title="Revenue Variance: Base Plan vs. Scenario",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_comp, use_container_width=True)

with col_side:
    # Year 3 Unit Economics Waterfall
    y3 = df.iloc[2]
    fig_water = go.Figure(go.Waterfall(
        name="Unit Economics", orientation="v",
        measure=["relative", "total", "relative", "total"],
        x=["Lumber Sales", "Total Rev", "Direct Costs", "Gross Margin"],
        y=[y3['Total Revenue']*0.88, y3['Total Revenue'], - (y3['Total Revenue'] - y3['Margin']), y3['Margin']],
        connector={"line":{"color":BR_GRAY}},
        increasing={"marker":{"color":BR_GOLD}},
        decreasing={"marker":{"color":BR_RED}},
        totals={"marker":{"color":BR_GOLD}}
    ))
    fig_water.update_layout(title="Y3 Unit Economics Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_water, use_container_width=True)

# THE DATA TABLE
with st.expander("Detailed Model Data"):
    st.table(df.style.format("${:,.0f}"))
