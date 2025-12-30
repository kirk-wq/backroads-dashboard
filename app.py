import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. SECURITY (Must be at the top) ---
def password_entered():
    if st.session_state["password"] == st.secrets["password"]:
        st.session_state["password_correct"] = True
    else:
        st.error("😕 Access Denied")

def check_password():
    if "password_correct" not in st.session_state:
        st.sidebar.text_input("Enter Access Code", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()

# --- 2. LAYOUT & STYLING ---
st.set_page_config(page_title="Backroads Reclamation | Investor Portal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 2rem; color: #ffffff; }
    div[data-testid="stMetricDelta"] { font-size: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ALL 5 SCENARIO CONTROLS (Sidebar) ---
st.sidebar.title("🎮 Scenario Levers")
vol_adj = st.sidebar.slider("Volume Adjustment (Homes)", 50, 150, 100, help="Stress test house throughput") / 100
yield_adj = st.sidebar.slider("Recovery Rate Sensitivity", 80, 120, 100, help="Operational yield efficiency") / 100
price_adj = st.sidebar.slider("Lumber Price Adjustment", 50, 150, 100, help="Market volatility (Bear/Bull)") / 100
tip_adj = st.sidebar.slider("Tipping Fee Adjustment", 80, 120, 100, help="Negotiating power on waste fees") / 100
cost_adj = st.sidebar.slider("Direct Cost Sensitivity", 80, 130, 100, help="Impact of fuel/labor/logistics inflation") / 100

# --- 4. THE ENGINE (v5.4 Logic) ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
recovery_rates = [0.50, 0.60, 0.65]
# Base Case Gross Margin from your Excel (Y1: 3.9M, Y2: 10.8M, Y3: 14.8M)
# We assume direct costs are approx 15-20% of revenue based on your margin
base_direct_cost_per_home = [1700, 1750, 1850] 

results = []
for i, year in enumerate(years):
    homes = base_homes[i] * vol_adj
    recovery = recovery_rates[i] * yield_adj
    total_bf = homes * 6615 * recovery
    
    # Revenue Calculations
    mix = {"Prem": [0.30, 0.35, 0.40], "Bld": [0.50, 0.48, 0.45], "Ind": [0.20, 0.17, 0.15]}
    prices = {"Prem": [3.50, 3.68, 3.86], "Bld": [2.50, 2.63, 2.76], "Ind": [1.50, 1.58, 1.66]}
    
    lumber_rev = (
        (total_bf * mix["Prem"][i] * prices["Prem"][i] * price_adj) +
        (total_bf * mix["Bld"][i] * prices["Bld"][i] * price_adj) +
        (total_bf * mix["Ind"][i] * prices["Ind"][i] * price_adj)
    )
    
    other_rev = (homes * 1200 * tip_adj) + (homes * 600) # Tipping + Materials
    total_rev = lumber_rev + other_rev
    
    # Cost & Margin logic
    total_costs = (homes * base_direct_cost_per_home[i] * cost_adj)
    gross_margin = total_rev - total_costs
    
    results.append({
        "Year": year, 
        "Lumber": lumber_rev, 
        "Other": other_rev, 
        "Total": total_rev, 
        "Margin": gross_margin,
        "Margin %": (gross_margin / total_rev) * 100
    })

df = pd.DataFrame(results)

# --- 5. VISUAL DASHBOARD ---
st.title("Backroads Reclmation: Interactive Financial Command Center")
st.subheader("Simulating Upside and Downside Scenarios")

# Top Row: The "Money" Metrics
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total 3-Year Revenue", f"${df['Total'].sum()/1e6:.1f}M", 
              delta=f"{(vol_adj*price_adj*100)-100:.1f}% vs Base")
with c2:
    st.metric("Year 3 Gross Margin", f"${df.iloc[2]['Margin']/1e6:.1f}M")
with c3:
    st.metric("Avg. Margin %", f"{df['Margin %'].mean():.1f}%")
with c4:
    st.metric("Revenue / Home", f"${df.iloc[2]['Total']/base_homes[2]/vol_adj:,.0f}")

# Main Visuals
col_left, col_right = st.columns([2, 1])

with col_left:
    # Stacked Area Chart looks more "Professional Finance" than bars
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Lumber'], name='Lumber Revenue', stackgroup='one', fill='tonexty', line=dict(color='#2E7D32')))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Other'], name='Tipping/Recovery', stackgroup='one', fill='tonexty', line=dict(color='#FFA000')))
    fig.update_layout(title="Revenue Growth Path", template="plotly_dark", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    # Donut chart for Year 3 Mix
    labels = ['Lumber Sales', 'Tipping & Recovery']
    values = [df.iloc[2]['Lumber'], df.iloc[2]['Other']]
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=['#2E7D32', '#FFA000'])])
    fig_pie.update_layout(title="Y3 Revenue Breakdown", template="plotly_dark")
    st.plotly_chart(fig_pie, use_container_width=True)

# Data Table for Diligent Investors
with st.expander("View Full Financial Data Table"):
    st.dataframe(df.style.format({"Lumber": "${:,.0f}", "Other": "${:,.0f}", "Total": "${:,.0f}", "Margin": "${:,.0f}", "Margin %": "{:.1f}%"}))
