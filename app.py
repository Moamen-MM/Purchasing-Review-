import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files:
        st.error("No CSV file found in the repository!")
        return None
    
    target_file = files[0]
    
    try:
        # Try reading with comma first, then semicolon if it fails
        try:
            df = pd.read_csv(target_file, sep=',', engine='python')
            if df.shape[1] <= 1: # If only 1 column found, try semicolon
                df = pd.read_csv(target_file, sep=';', engine='python')
        except:
            df = pd.read_csv(target_file, sep=';', engine='python')

        # Create the display dataframe
        df_final = pd.DataFrame()
        
        # We use a safer way to grab columns by position
        # Indices: PO(2), Supplier(10), Date(27), Amount(36), Status(54)
        df_final['PO'] = df.iloc[:, 2].astype(str)
        df_final['Supplier'] = df.iloc[:, 10].fillna('Unknown')
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54].fillna('Pending')
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Data structure error: The file '{target_file}' doesn't have enough columns. Found {df.shape[1]} columns.")
        st.info("Try saving your Excel file as 'CSV (Comma Delimited)' specifically.")
        return None

df = load_data()

if df is not None:
    # --- FILTERS ---
    st.sidebar.header("Settings")
    status_list = df['Status'].unique().tolist()
    selected_status = st.sidebar.multiselect("Status Filter", status_list, default=status_list)
    df_filtered = df[df['Status'].isin(selected_status)]

    # --- KPI ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Value", f"${df_filtered['Amount'].sum():,.2f}")
    m2.metric("Orders", f"{len(df_filtered):,}")
    m3.metric("Avg Order", f"${df_filtered['Amount'].mean():,.2f}")

    st.divider()
    
    # --- CHARTS ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Spending Trend")
        trend = df_filtered.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', markers=True), use_container_width=True)
    with c2:
        st.subheader("Top Suppliers")
        top_s = df_filtered.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h'), use_container_width=True)

    st.subheader("Detailed Order List")
    st.dataframe(df_filtered.sort_values('Date', ascending=False), use_container_width=True)
