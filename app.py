import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Dashboard", layout="wide")

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    try:
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        df.columns = [str(c).strip() for c in df.columns]
        
        def find_col(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in str(c).lower(): return c
            return None

        clean = pd.DataFrame()
        amt_name = find_col(['PO Estimate Total', 'Total', 'Amount'])
        date_name = find_col(['Added time', 'Date', 'Created'])
        sup_name = find_col(['Supplier', 'Vendor'])
        stat_name = find_col(['Status', 'Approval'])

        if amt_name and date_name:
            # THE DATA HAMMER: Removes EGP, $, commas, and spaces so math works
            s_amt = df[amt_name].astype(str).str.replace(r'[^\d.]', '', regex=True)
            clean['Amount'] = pd.to_numeric(s_amt, errors='coerce')
            
            clean['Date'] = pd.to_datetime(df[date_name], errors='coerce')
            clean['Supplier'] = df[sup_name].fillna('Unknown')
            clean['Status'] = df[stat_name].fillna('N/A')
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except: return None

df = load_data()

if df is not None and not df.empty:
    st.title("🛡️ Procurement Intelligence Command")
    
    # --- SIDEBAR ---
    st.sidebar.header("🕹️ Filter Controls")
    all_stats = sorted(df['Status'].unique().tolist())
    sel_stats = st.sidebar.multiselect("Filter Status", all_stats, default=all_stats)
    
    # Filter data
    df_f = df[df['Status'].isin(sel_stats)]

    # --- KPI ROW ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Committed", f"${df_f['Amount'].sum():,.0f}")
    c2.metric("Order Count", len(df_f))
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.0f}")

    st.divider()

    # --- CHARTS ---
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("🗓️ Spending Trend")
        # Ensure trend is sorted by date
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.area(trend, x='Month', y='Amount', template="plotly_white"), use_container_width=True)
    
    with col_b:
        st.subheader("🎯 Status Split")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.4), use_container_width=True)

    # --- VENDORS ---
    st.subheader("🏆 Top 10 Suppliers")
    top_v = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
    st.plotly_chart(px.bar(top_v, x='Amount', y='Supplier', orientation='h', color='Amount', color_continuous_scale='Blues'), use_container_width=True)

else:
    st.error("🚨 Dashboard is empty! Please check that your Excel file has prices in the 'PO Estimate Total' column.")
