import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    # Find any data file
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files:
        st.error("No data files found in GitHub!")
        return None
    
    target = files[0]
    st.sidebar.info(f"Reading: {target}")
    
    try:
        if target.endswith('.xlsx'):
            try:
                # Primary attempt: Read normally
                df = pd.read_excel(target, engine='openpyxl')
            except ValueError:
                # Secondary attempt: Use 'xlrd' or a cleaner read if styles are broken
                st.warning("Excel styles are causing an error. Trying to read raw values...")
                # We try to read it by bypassing the style engine if possible
                df = pd.read_excel(target, engine='openpyxl', read_only=True)
        else:
            # For CSVs, we use 'sep=None' to automatically find commas or semicolons
            df = pd.read_csv(target, sep=None, engine='python')

        # Robust Column Mapping (using positions)
        # Based on your file: PO(2), Supplier(10), Date(27), Amount(36), Status(54)
        df_final = pd.DataFrame()
        df_final['PO'] = df.iloc[:, 2].astype(str)
        df_final['Supplier'] = df.iloc[:, 10].fillna('Unknown')
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54].fillna('Pending')
        
        return df_final.dropna(subset=['Amount', 'Date'])
        
    except Exception as e:
        st.error(f"Could not read the file. Error: {e}")
        st.info("💡 QUICK FIX: Open your Excel file, 'Save As' a CSV (Comma Delimited), and upload it as 'data.csv'.")
        return None

df = load_data()

if df is not None:
    # --- DASHBOARD ---
    st.sidebar.header("Filters")
    selected_status = st.sidebar.multiselect("Status:", df['Status'].unique(), default=df['Status'].unique())
    df_f = df[df['Status'].isin(selected_status)]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    col2.metric("Orders", f"{len(df_f):,}")
    col3.metric("Avg PO", f"${df_f['Amount'].mean():,.2f}")

    st.divider()
    
    l, r = st.columns(2)
    with l:
        trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', title="Monthly Trend"), use_container_width=True)
    with r:
        top = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Amount', y='Supplier', orientation='h', title="Top 10 Suppliers"), use_container_width=True)

    st.subheader("Recent Orders")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
