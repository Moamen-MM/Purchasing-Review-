import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Page Configuration
st.set_page_config(page_title="Procurement Command Center", layout="wide")

# 2. Professional Styling
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #ebedef; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    try:
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Aggressive Column Discovery
        def find_col(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in c.lower(): return c
            return None

        clean = pd.DataFrame()
        amt_col = find_col(['PO Estimate Total', 'Total', 'Amount'])
        date_col = find_col(['Added time', 'Date', 'Created'])
        sup_col = find_col(['Supplier', 'Vendor'])
        stat_col = find_col(['Status', 'Approval'])

        if amt_col and date_col:
            clean['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
            clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            clean['Supplier'] = df[sup_col].fillna('Unknown') if sup_col else 'Unknown'
            clean['Status'] = df[stat_col].fillna('Unknown') if stat_col else 'Unknown'
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except:
        return None

# --- Main App Execution ---
df = load_data()

if df is not None:
    # SIDEBAR
    st.sidebar.header("🕹️ Control Panel")
    min_d, max_d = df['Date'].min().date(), df['Date'].max().date()
    # Fixed syntax for date input
    date_range = st.sidebar.date_input("Select Period", [min_d, max_d])
    
    # FILTER LOGIC
    if len(date_range) == 2:
        mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
        df_f = df.loc[mask].copy()
    else:
        df_f = df.copy()

    # DASHBOARD HEADER
    st.title("🛡️ Procurement Operations Command")
    st.divider()

    # TOP METRICS
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Committed", f"${df_f['Amount'].sum():,.0f}")
    m2.metric("PO Count", f"{len(df_f):,}")
    m3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")

    # ROW 1: TRENDS & ALLOCATION
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("🗓️ Spending Trajectory")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.area(trend, x='Month', y='Amount', template="plotly_white", color_discrete_sequence=['#007bff']), use_container_width=True)
    
    with col2:
        st.subheader("⚖️ Status Allocation")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.5), use_container_width=True)

    # ROW 2: TOP SUPPLIERS
    st.subheader("🏢 Top 10 High-Volume Vendors")
    top_v = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
    st.plotly_chart(px.bar(top_v, x='Amount', y='Supplier', orientation='h', color='Amount', color_continuous_scale='Blues'), use_container_width=True)

    # DATA LOG
    with st.expander("🔍 Deep Dive: Transaction Log"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)

else:
    st.warning("Dashboard standby. Please check your data file on GitHub.")
