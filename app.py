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
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.sidebar.title("🔐 Access")
        pw = st.sidebar.text_input("Enter Access Code", type="password")
        if pw == st.secrets["password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password():
    st.stop()

# --- 3. INTUITIVE SLIDERS (Delta Based) ---
st.sidebar.header("🕹️ Scenario Adjustments")
st.sidebar.info("Adjust the sliders to see variance from the Base Case (0%).")

v_delta = st.sidebar.slider("Volume (Homes)", -50, 50, 0, format="%d%%")
y_delta = st.sidebar.slider("Recovery Yield", -30, 30, 0, format="%d%%")
p_delta = st.sidebar.slider("Lumber Market Price", -50, 50, 0, format="%d%%")
t_delta = st.sidebar.slider("Tipping Fee Power", -20, 20, 0, format="%d%%")
c_delta = st.sidebar.slider("Direct Cost Inflation", -20, 20, 0, format="%d%%")

# Convert Deltas to Multipliers
vol_m = 1 + (v_delta / 100)
yld_m = 1 + (y_delta / 100)
prc_m = 1 + (p_delta / 100)
tip_m = 1 + (t_delta / 100)
cst_m = 1 + (c_delta / 100)

# --- 4. DATA ENGINE ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
recovery_rates = [0.50, 0.60, 0.65]
# Original Spreadsheet Totals for Comparison
base_case_rev = [4753166, 12469066, 17820600]

results = []
for i, year in enumerate(years):
    h = base_homes[i] * vol_m
    r = recovery_rates[i] * yld_m
    rev_lumber = (h * 6615 * r * [2.60, 2.82, 3.04][i] * prc_m)
    rev_other = (h * 1200 * tip_m) + (h * 600)
    total_rev = rev_lumber + rev_other
    costs = (h * [1700, 1750, 1850][i] * cst_m)
    margin = total_rev - costs
    
    results.append({"Year": year, "Total Revenue": total_rev, "Margin": margin, "Base": base_case_rev[i]})

df = pd.DataFrame(results)

# --- 5. THE DASHBOARD ---
st.title("Backroads Reclamation: Financial Stress Test")
st.markdown(f"**Current Status:** {v_delta}% Volume | {p_delta}% Price Market | {c_delta}% Cost Basis")

# KPI Row
m1, m2, m3 = st.columns(3)
with m1:
    delta_total = ((df['Total Revenue'].sum() / sum(base_case_rev)) - 1) * 100
    st.metric("3-Year Total Revenue", f"${df['Total Revenue'].sum()/1e6:.1f}M", f"{delta_total:.1f}% vs Plan")
with m2:
    st.metric("Year 3 Gross Margin", f"${df.iloc[2]['Margin']/1e6:.1f}M")
with m3:
    st.metric("Operating Efficiency", f"{(df.iloc[2]['Margin']/df.iloc[2]['Total Revenue'])*100:.1f}%")

st.divider()

# CHART 1: VARIANCE TO PLAN (Side-by-Side Bars)
col1, col2 = st.columns([2, 1])

with col1:
    fig_var = go.Figure()
    fig_var.add_trace(go.Bar(x=df['Year'], y=df['Base'], name='Original Base Case', marker_color=BR_GRAY))
    fig_var.add_trace(go.Bar(x=df['Year'], y=df['Total Revenue'], name='Live Adjusted Scenario', marker_color=BR_GOLD))
    fig_var.update_layout(
        title="Revenue Performance: Base Plan vs. Scenario",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='group'
    )
    st.plotly_chart(fig_var, use_container_width=True)

with col2:
    # CHART 2: THE MARGIN WALK (Waterfall for Year 3)
    y3 = df.iloc[2]
    fig_water = go.Figure(go.Waterfall(
        name="Walk", orientation="v",
        measure=["relative", "total", "relative", "total"],
        x=["Lumber Rev", "Total Revenue", "Direct Costs", "Gross Margin"],
        y=[y3['Total Revenue']*0.85, y3['Total Revenue'], - (y3['Total Revenue'] - y3['Margin']), y3['Margin']],
        connector={"line":{"color":BR_GRAY}},
        increasing={"marker":{"color":BR_GOLD}},
        decreasing={"marker":{"color":BR_RED}},
        totals={"marker":{"color":BR_GRAY}}
    ))
    fig_water.update_layout(title="Year 3 Economics Walk", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_water, use_container_width=True)

# THE TRUTH TABLE
with st.expander("Detailed Year-over-Year Breakdown"):
    st.table(df.style.format("${:,.0f}"))
