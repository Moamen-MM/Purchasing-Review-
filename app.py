import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    # 1. Look for any data file (CSV or Excel)
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files:
        st.error("No data file found! Please upload 'data.csv' or 'data.xlsx' to GitHub.")
        return None
    
    target = files[0]
    st.sidebar.info(f"Connected to: {target}")
    
    try:
        # 2. Load the file
        if target.endswith('.xlsx'):
            df = pd.read_excel(target, engine='openpyxl', read_only=True)
        else:
            df = pd.read_csv(target, sep=None, engine='python')

        # 3. Clean mapping using column positions
        df_final = pd.DataFrame()
        df_final['PO'] = df.iloc[:, 2].astype(str)
        df_final['Supplier'] = df.iloc[:, 10].fillna('Unknown')
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54].fillna('Pending')
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

df = load_data()

if df is not None:
    # --- FILTERS ---
    st.sidebar.header("Controls")
    status_list = df['Status'].unique().tolist()
    selected_status = st.sidebar.multiselect("Status:", status_list, default=status_list)
    df_f = df[df['Status'].isin(selected_status)]

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Total Orders", f"{len(df_f):,}")
    c3.metric("Avg Order Value", f"${df_f['Amount'].mean():,.2f}")

    st.divider()
    
    # --- CHARTS ---
    l, r = st.columns(2)
    with l:
        st.subheader("Monthly Spending Trend")
        # FIXED: Using 'ME' for Month End to support new Pandas versions
        try:
            trend = df_f.set_index('Date').resample('ME')['Amount'].sum().reset_index()
        except ValueError:
            # Fallback for older versions
            trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
            
        st.plotly_chart(px.line(trend, x='Date', y='Amount', markers=True, template="plotly_white"), use_container_width=True)
    
    with r:
        st.subheader("Top 10 Suppliers")
        top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h', color='Amount'), use_container_width=True)

    # --- DATA TABLE ---
    st.subheader("Order Log")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
