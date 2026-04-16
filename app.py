import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    # 1. Automatic file detection
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files:
        st.error("No data file found in the repository!")
        return None
    
    target = files[0]
    try:
        if target.endswith('.xlsx'):
            df = pd.read_excel(target, engine='openpyxl')
        else:
            df = pd.read_csv(target, sep=None, engine='python')

        # 2. Smart column detection
        def find_col(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in str(c).lower(): return c
            return None

        col_amt = find_col(['PO Estimate Total', 'Amount', 'Total'])
        col_date = find_col(['Added time', 'Date', 'Created'])
        col_sup = find_col(['Supplier', 'Vendor'])
        col_stat = find_col(['Approval Status', 'Status'])

        if not col_amt or not col_date:
            st.error("Could not find Amount or Date columns.")
            return None

        # 3. Data Cleaning
        df_final = pd.DataFrame()
        df_final['Amount'] = pd.to_numeric(df[col_amt], errors='coerce')
        df_final['Date'] = pd.to_datetime(df[col_date], errors='coerce')
        df_final['Supplier'] = df[col_sup].fillna('Unknown') if col_sup else 'Unknown'
        df_final['Status'] = df[col_stat].fillna('Pending') if col_stat else 'N/A'
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error: {e}")
        return None

df = load_data()

if df is not None:
    # --- FILTERS ---
    st.sidebar.header("Dashboard Filters")
    status_list = df['Status'].unique().tolist()
    choice = st.sidebar.multiselect("Select Status", status_list, default=status_list)
    df_f = df[df['Status'].isin(choice)].copy()

    # --- METRICS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Total Orders", f"{len(df_f):,}")
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.2f}")

    st.divider()

    # --- TREND CHART (MANUAL GROUPING - BYPASSES THE ERROR) ---
    st.subheader("Monthly Spending Trend")
    
    # We create a Year-Month string instead of using .resample()
    # This is 100% safe from the 'M' vs 'ME' error
    df_f['Month'] = df_f['Date'].dt.strftime('%Y-%m')
    trend = df_f.groupby('Month')['Amount'].sum().reset_index()
    trend = trend.sort_values('Month')
    
    fig_trend = px.line(trend, x='Month', y='Amount', markers=True, template="plotly_white")
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- TOP SUPPLIERS ---
    st.subheader("Top 10 Suppliers")
    top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
    st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h'), use_container_width=True)

    # --- DATA ---
    st.subheader("Recent Records")
    st.dataframe(df_f[['Date', 'Supplier', 'Amount', 'Status']].sort_values('Date', ascending=False), use_container_width=True)
