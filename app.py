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
        st.error("No data file found! Please upload 'data.xlsx' or 'data.csv'.")
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

        # 3. Data Cleaning
        df_final = pd.DataFrame()
        df_final['Amount'] = pd.to_numeric(df[col_amt], errors='coerce')
        df_final['Date'] = pd.to_datetime(df[col_date], errors='coerce')
        df_final['Supplier'] = df[col_sup].fillna('Unknown') if col_sup else 'Unknown'
        df_final['Status'] = df[col_stat].fillna('Pending') if status_col else 'N/A'
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

df = load_data()

if df is not None:
    # FILTERS
    status_list = df['Status'].unique().tolist()
    choice = st.sidebar.multiselect("Select Status", status_list, default=status_list)
    df_f = df[df['Status'].isin(choice)].copy()

    # KPIs
    c1, c2 = st.columns(2)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Orders", f"{len(df_f):,}")

    st.divider()

    # TREND CHART (Safe version for Python 3.14)
    st.subheader("Monthly Spending Trend")
    # We group by string to avoid the resample frequency error entirely
    df_f['Month_Key'] = df_f['Date'].dt.strftime('%Y-%m')
    trend = df_f.groupby('Month_Key')['Amount'].sum().reset_index()
    trend = trend.sort_values('Month_Key')
    
    st.plotly_chart(px.line(trend, x='Month_Key', y='Amount', markers=True), use_container_width=True)

    # DATA
    st.subheader("Details")
    st.dataframe(df_f[['Date', 'Supplier', 'Amount', 'Status']].sort_values('Date', ascending=False), use_container_width=True)
