import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Intelligence", layout="wide")

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    try:
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. Target your specific columns directly
        clean = pd.DataFrame()
        
        # Amount: Priority on 'PO Estimate Total'
        amt_col = next((c for c in df.columns if 'PO Estimate Total' in c or 'Total' in c), df.columns[36])
        clean['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
        
        # Date: Priority on 'Added time'
        date_col = next((c for c in df.columns if 'Added time' in c or 'Date' in c), df.columns[27])
        clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Supplier & Status
        sup_col = next((c for c in df.columns if 'Supplier' in c), df.columns[10])
        stat_col = next((c for c in df.columns if 'Status' in c), df.columns[54])
        
        clean['Supplier'] = df[sup_col].fillna('Unknown')
        clean['Status'] = df[stat_col].fillna('Unknown')
        
        return clean.dropna(subset=['Amount', 'Date'])
    except: return None

df = load_data()

st.title("🚀 Purchasing Intelligence Dashboard")
st.markdown("---")

if df is not None:
    # --- FILTERS ---
    st.sidebar.header("Filters")
    status_list = df['Status'].unique().tolist()
    selected = st.sidebar.multiselect("Select Status", status_list, default=status_list)
    df_f = df[df['Status'].isin(selected)]

    # --- TOP KPI ROW ---
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Spend", f"${df_f['Amount'].sum():,.0f}")
    k2.metric("Total Orders", len(df_f))
    k3.metric("Avg Order", f"${df_f['Amount'].mean():,.0f}")

    st.markdown("---")

    # --- VISUALS ---
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.subheader("📊 Monthly Spending Trend")
        df_f['Month'] = df_f['Date'].dt.strftime('%Y-%m')
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.line(trend, x='Month', y='Amount', markers=True, template="plotly_white"), width='stretch')

    with col_r:
        st.subheader("🎯 Status Share")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.4), width='stretch')

    # --- BAR CHART ---
    st.subheader("🏆 Top 10 Suppliers")
    top_10 = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
    st.plotly_chart(px.bar(top_10, x='Amount', y='Supplier', orientation='h', color='Amount', template="plotly_white"), width='stretch')

    # --- TABLE ---
    with st.expander("📋 View Data Table"):
        st.dataframe(df_f.sort_values('Date', ascending=False), width='stretch')
else:
    st.error("Still having trouble finding the data columns. Please check the Excel file formatting.")
