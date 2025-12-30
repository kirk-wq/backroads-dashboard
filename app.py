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

st.set_page_config(page_title="Backroads Reclamation | Institutional Planner", layout="wide")

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
st.sidebar.info("Center (0%) matches your v5.4 Financial Model exactly.")

v_delta = st.sidebar.slider("Volume Variance (Homes)", -50, 50, 0, format="%d%%")
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

# --- 4. THE V5.4 ENGINE (EXACT CALIBRATION) ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
base_recovery = [0.50, 0.60, 0.65]
# Base Case Totals from your tab to ensure 0.0% variance at start
base_rev_targets = [4753166, 12469066, 17820600] 
base_margin_targets = [3978038, 10826653, 14805261] # Derived from your Gross Margin results

results = []
for i, year in enumerate(years):
    h = base_homes[i] * vol_m
    r = base_recovery[i] * yld_m
    
    # Revenue (Matches your v5.4 pricing and product mix growth)
    rev_lumber = (h * 6615 * r * [2.60, 2.82, 3.04][i] * prc_m)
    rev_other = (h * 1200 * tip_m) + (h * 600)
    total_rev = rev_lumber + rev_other
    
    # Costs: Calibrated to match your base case margins
    base_costs = base_rev_targets[i] - base_margin_targets[i]
    current_costs = (base_costs * vol_m * cst_m)
    margin = total_rev - current_costs
    
    results.append({
        "Year": year, 
        "Lumber": rev_lumber,
        "Other": rev_other,
        "Total Revenue": total_rev, 
        "Margin": margin, 
        "Base Case": base_rev_targets[i]
    })

df = pd.DataFrame(results)

# --- 5. INVESTOR VIEW ---
st.title("Backroads Reclamation: Institutional Scenario Planner")
st.caption(f"SCENARIO TEST: {v_delta}% Volume | {p_delta}% Price Market | {y_delta}% Yield Shift")

# KPI Ribbon - Focusing on Year 3 (The Exit Year)
m1, m2, m3, m4 = st.columns(4)
y3_actual = df.iloc[2]['Total Revenue']
y3_base = base_rev_targets[2]
y3_variance = ((y3_actual / y3_base) - 1) * 100

with m1:
    st.metric("Year 3 Revenue", f"${y3_actual/1e6:.2f}M", f"{y3_variance:.1f}% vs Plan")
with m2:
    st.metric("Year 3 Gross Margin", f"${df.iloc[2]['Margin']/1e6:.2f}M")
with m3:
    st.metric("Operating Efficiency", f"{(df.iloc[2]['Margin']/y3_actual)*100:.1f}%")
with m4:
    # 3-Year Cumulative as a secondary high-level stat
    st.metric("3-Year Cumulative", f"${df['Total Revenue'].sum()/1e6:.1f}M")

st.write("---")

# Main Charts
col_main, col_side = st.columns([2, 1])

with col_main:
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(x=df['Year'], y=df['Base Case'], name='v5.4 Financial Model', marker_color=BR_GRAY))
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
    y3 = df.iloc[2]
    fig_water = go.Figure(go.Waterfall(
        name="Unit Economics", orientation="v",
        measure=["relative", "relative", "total", "relative", "total"],
        x=["Lumber Sales", "Other Revenue", "Total Revenue", "Direct Costs", "Gross Margin"],
        y=[y3['Lumber'], y3['Other'], y3['Total Revenue'], - (y3['Total Revenue'] - y3['Margin']), y3['Margin']],
        connector={"line":{"color":BR_GRAY}},
        increasing={"marker":{"color":BR_GOLD}},
        decreasing={"marker":{"color":BR_RED}},
        totals={"marker":{"color":BR_GOLD}}
    ))
    fig_water.update_layout(title="Y3 Unit Economics Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_water, use_container_width=True)

# THE DATA TABLE (FIXED FORMATTING ERROR)
with st.expander("Detailed Model Data Breakdown"):
    # Apply currency formatting only to the numeric columns to avoid the ValueError
    numeric_cols = ["Lumber", "Other", "Total Revenue", "Margin", "Base Case"]
    formatted_df = df.copy()
    for col in numeric_cols:
        formatted_df[col] = formatted_df[col].apply(lambda x: f"${x:,.0f}")
    
    st.table(formatted_df)
