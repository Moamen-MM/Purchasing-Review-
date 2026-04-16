import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    # 1. Look for any data file
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files:
        st.error("No data file found! Please upload your data to GitHub.")
        return None
    
    target = files[0]
    try:
        if target.endswith('.xlsx'):
            df = pd.read_excel(target, engine='openpyxl')
        else:
            df = pd.read_csv(target, sep=None, engine='python')

        # 2. Smart Column Search (Finds names even with extra spaces)
        def find_col(possible_names):
            for name in possible_names:
                for col in df.columns:
                    if name.lower() in str(col).lower():
                        return col
            return None

        # 3. Create Clean Table
        df_final = pd.DataFrame()
        amt_col = find_col(['PO Estimate Total', 'Amount', 'Total'])
        date_col = find_col(['Added time', 'Date', 'Created'])
        sup_col = find_col(['Supplier', 'Vendor'])
        status_col = find_col(['Approval Status', 'Status'])

        if not amt_col or not date_col:
            st.error(f"Missing essential columns (Amount/Date). Found: {list(df.columns)}")
            return None

        df_final['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
        df_final['Date'] = pd.to_datetime(df[date_col], errors='coerce')
        df_final['Supplier'] = df[sup_col].fillna('Unknown') if sup_col else 'Unknown'
        df_final['Status'] = df[status_col].fillna('Pending') if status_col else 'N/A'
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Critical error: {e}")
        return None

df = load_data()

if df is not None:
    # --- FILTERS ---
    st.sidebar.header("Controls")
    statuses = df['Status'].unique().tolist()
    selected = st.sidebar.multiselect("Filter Status:", statuses, default=statuses)
    df_f = df[df['Status'].isin(selected)]

    # --- KPI ---
    c1, c2 = st.columns(2)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Total Orders", f"{len(df_f):,}")

    st.divider()

    # --- CHARTS ---
    l, r = st.columns(2)
    with l:
        st.subheader("Monthly Spending Trend")
        # THE FIX: Try 'ME' (Month End) first, then 'M' for older versions
        try:
            trend = df_f.set_index('Date').resample('ME')['Amount'].sum().reset_index()
        except:
            trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        
        st.plotly_chart(px.line(trend, x='Date', y='Amount', markers=True), use_container_width=True)

    with r:
        st.subheader("Top Suppliers")
        top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h'), use_container_width=True)

    st.subheader("Raw Data View")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
