import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Kluane Partners Dashboard", layout="wide")
st.markdown("""<style> .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; } </style>""", unsafe_allow_html=True)

# --- 2. INPUT LEVERS (Sidebar) ---
st.sidebar.header("Scenario Controls")
vol_adj = st.sidebar.slider("Volume Adjustment (Homes %)", 50, 150, 100) / 100
yield_adj = st.sidebar.slider("Recovery Yield Sensitivity (%)", 80, 120, 100) / 100
mkt_price_adj = st.sidebar.slider("Lumber Market Price (%)", 50, 150, 100) / 100

# --- 3. THE CALCULATIONS (The "Engine") ---
years = ["Year 1", "Year 2", "Year 3"]
base_homes = [457, 960, 1200]
recovery_rates = [0.50, 0.60, 0.65]
bf_per_home = 6615

# Dynamic Logic
results = []
for i, year in enumerate(years):
    homes = base_homes[i] * vol_adj
    recovery = recovery_rates[i] * yield_adj
    total_bf = homes * bf_per_home * recovery
    
    # Mix & Pricing (Refined to match your v5.4 file)
    mix = {"Premium": [0.30, 0.35, 0.40], "Builder": [0.50, 0.48, 0.45], "Industrial": [0.20, 0.17, 0.15]}
    prices = {"Premium": [3.50, 3.68, 3.86], "Builder": [2.50, 2.63, 2.76], "Industrial": [1.50, 1.58, 1.66]}
    
    lumber_rev = (
        (total_bf * mix["Premium"][i] * prices["Premium"][i] * mkt_price_adj) +
        (total_bf * mix["Builder"][i] * prices["Builder"][i] * mkt_price_adj) +
        (total_bf * mix["Industrial"][i] * prices["Industrial"][i] * mkt_price_adj)
    )
    
    tipping_rev = homes * 1200
    materials_rev = homes * 600
    total_rev = lumber_rev + tipping_rev + materials_rev
    
    results.append({"Year": year, "Lumber": lumber_rev, "Other": tipping_rev + materials_rev, "Total": total_rev})

df = pd.DataFrame(results)

# --- 4. DASHBOARD DISPLAY ---
st.title("🌲 Kluane Partners: Interactive Financial Model")
c1, c2, c3 = st.columns(3)
c1.metric("Year 3 Lumber Revenue", f"${df.iloc[2]['Lumber']:,.0f}")
c2.metric("Year 3 Total Revenue", f"${df.iloc[2]['Total']:,.0f}")
c3.metric("3-Year Cumulative", f"${df['Total'].sum():,.0f}")

# --- 5. VISUALS ---
fig = go.Figure()
fig.add_trace(go.Bar(x=df['Year'], y=df['Lumber'], name='Lumber Revenue', marker_color='#2E7D32'))
fig.add_trace(go.Bar(x=df['Year'], y=df['Other'], name='Tipping & Materials', marker_color='#FFA000'))
fig.update_layout(barmode='stack', title="Revenue Projections")
st.plotly_chart(fig, use_container_width=True)
