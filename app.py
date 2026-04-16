import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Intelligence", layout="wide")

# Professional UI Styling
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
        
        def smart_find(keywords):
            for k in keywords:
                for col in df.columns:
                    if k.lower() in col.lower(): return col
            return None

        clean = pd.DataFrame()
        amt_col = smart_find(['PO Estimate Total', 'Total', 'Amount'])
        date_col = smart_find(['Added time', 'Date', 'Created'])
        sup_col = smart_find(['Supplier', 'Vendor'])
        stat_col = smart_find(['Status', 'Approval'])

        if amt_col and date_col:
            clean['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
            clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            clean['Supplier'] = df[sup_col].fillna('Unknown') if sup_col else 'Unknown'
            clean['Status'] = df[stat_col].fillna('Unknown') if stat_col else 'Unknown'
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except: return None

df = load_data()

st.title("🛡️ Procurement Operations Command")
st.divider()

if df is not None:
    # --- SIDEBAR ---
    st.sidebar.header("🕹️ Filters")
    start_date = st.sidebar.date_input("Start Date", df['Date'].min())
    end_date = st.sidebar.date_input("End Date", df['Date'].max())
    
    # --- FILTER EXECUTION (Fixed Syntax) ---
    mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    df_f = df.loc[mask]

    # --- KPI ROW ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Committed", f"${df_f['Amount'].sum():,.0f}")
    m2.metric("PO Volume", f"{len(df_f):,}")
    m3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")

    # --- CHARTS ---
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🗓️ Spending Trajectory")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.area(trend, x='Month', y='Amount', template="plotly_white"), use_container_width=True)
    
    with c2:
        st.subheader("⚖️ Status Allocation")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.5), use_container_width=True)

    # --- DATA EXPLORER ---
    with st.expander("🔍 Transaction Log"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
else:
    st.warning("Data connection standby. Please check GitHub for your data file.")
