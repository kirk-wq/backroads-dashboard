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

st.set_page_config(page_title="Backroads Reclamation | Investor Portal", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BR_BLACK}; color: {BR_WHITE}; }}
    section[data-testid="stSidebar"] {{ background-color: {BR_OFF_BLACK} !important; }}
    .stMetric {{ background-color: {BR_OFF_BLACK}; padding: 15px; border-radius: 5px; border-left: 3px solid {BR_GOLD}; border-right: 1px solid {BR_GOLD}; }}
    div[data-testid="stMetricValue"] {{ color: {BR_GOLD} !important; font-size: 2rem !important; font-weight: 700; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.sidebar.title("🔐 Investor Access")
        pw = st.sidebar.text_input("Enter Access Code", type="password")
        if pw == st.secrets["password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password(): st.stop()

# --- 3. SCENARIO PRESETS (THE 'WOW' FEATURE) ---
st.sidebar.header("🎯 Macro Scenarios")
scenario = st.sidebar.radio("Quick-Select Stress Tests:", ["Base Case (v5.4)", "Lumber Market Crash", "Operational Excellence", "Recession Floor"])

# Set defaults based on scenario
if scenario == "Base Case (v5.4)":
    v, y, p, t, c = 0, 0, 0, 0, 0
elif scenario == "Lumber Market Crash":
    v, y, p, t, c = 0, 0, -35, 0, -5
elif scenario == "Operational Excellence":
    v, y, p, t, c = 15, 10, 5, 5, -5
else: # Recession Floor
    v, y, p, t, c = -40, -5, -20, -10, 10

st.sidebar.divider()
st.sidebar.header("🕹️ Fine-Tune Levers")
v_delta = st.sidebar.slider("Volume Variance (Homes)", -50, 50, v)
y_delta = st.sidebar.slider("Recovery Yield Variance", -25, 25, y)
p_delta = st.sidebar.slider("Lumber Price Variance", -50, 50, p)
t_delta = st.sidebar.slider("Tipping Fee Power", -20, 20, t)
c_delta = st.sidebar.slider("Direct Cost Variance", -20, 30, c)

# --- 4. ENGINE ---
years, base_homes, base_rev = ["Year 1", "Year 2", "Year 3"], [457, 960, 1200], [4753166, 12469066, 17820600]
base_margins = [3978038, 10826653, 14805261]
vol_m, yld_m, prc_m, tip_m, cst_m = 1+(v_delta/100), 1+(y_delta/100), 1+(p_delta/100), 1+(t_delta/100), 1+(c_delta/100)

results = []
for i in range(3):
    h = base_homes[i] * vol_m
    rev_l = (h * 6615 * ( [0.5,0.6,0.65][i]*yld_m ) * [2.6, 2.82, 3.04][i] * prc_m)
    rev_o = (h * 1200 * tip_m) + (h * 600)
    total_rev = rev_l + rev_o
    costs = (base_rev[i] - base_margins[i]) * vol_m * cst_m
    results.append({"Year": years[i], "Lumber": rev_l, "Other": rev_o, "Total": total_rev, "Margin": total_rev - costs, "Base": base_rev[i]})

df = pd.DataFrame(results)

# --- 5. THE VIEW ---
st.title("🌲 Backroads Reclamation | Institutional Scenario Planner")
st.subheader(f"Scenario: {scenario}")

# KPI Ribbon
m1, m2, m3, m4 = st.columns(4)
y3 = df.iloc[2]
variance = ((y3['Total'] / base_rev[2]) - 1) * 100
margin_color = "normal" if y3['Margin'] > 0 else "inverse"

with m1: st.metric("Year 3 Revenue", f"${y3['Total']/1e6:.2f}M", f"{variance:.1f}% vs Plan")
with m2: st.metric("Year 3 Gross Margin", f"${y3['Margin']/1e6:.2f}M", delta_color=margin_color)
with m3: st.metric("Efficiency (Margin %)", f"{(y3['Margin']/y3['Total'])*100:.1f}%")
with m4: st.metric("3-Year Cumulative", f"${df['Total'].sum()/1e6:.1f}M")

col_l, col_r = st.columns([2, 1])
with col_l:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Year'], y=df['Base'], name='v5.4 Base Model', marker_color=BR_GRAY))
    fig.add_trace(go.Bar(x=df['Year'], y=df['Total'], name='Live Stress Test', marker_color=BR_GOLD))
    fig.update_layout(title="Revenue Performance: Plan vs. Scenario", template="plotly_dark", barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    fig_w = go.Figure(go.Waterfall(
        orientation="v", measure=["relative", "relative", "total", "relative", "total"],
        x=["Lumber Sales", "Other (Fees)", "Gross Revenue", "Direct Costs", "NET MARGIN"],
        y=[y3['Lumber'], y3['Other'], y3['Total'], -(y3['Total']-y3['Margin']), y3['Margin']],
        totals={"marker":{"color":BR_GOLD}}, increasing={"marker":{"color":BR_GOLD}}, decreasing={"marker":{"color":BR_RED}}
    ))
    fig_w.update_layout(title="Y3 Unit Economics", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_w, use_container_width=True)

with st.expander("📊 Detailed Financial Data Table"):
    tdf = df.copy()
    for c in ["Lumber", "Other", "Total", "Margin", "Base"]: tdf[c] = tdf[c].apply(lambda x: f"${x:,.0f}")
    st.table(tdf)
