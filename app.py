import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    # 1. Look for Excel files (.xlsx) or CSVs
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv'))]
    if not files:
        st.error("No data file found in the repository!")
        return None
    
    target_file = files[0]
    
    try:
        # 2. Read the file
        if target_file.endswith('.xlsx'):
            df = pd.read_excel(target_file)
        else:
            df = pd.read_csv(target_file, sep=None, engine='python')

        # 3. Build the clean table using column positions
        df_final = pd.DataFrame()
        df_final['PO'] = df.iloc[:, 2].astype(str)
        df_final['Supplier'] = df.iloc[:, 10].fillna('Unknown')
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54].fillna('Pending')
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error reading {target_file}: {e}")
        return None

df = load_data()

if df is not None:
    # --- DASHBOARD ---
    st.sidebar.header("Filters")
    status_choice = st.sidebar.multiselect("Status", df['Status'].unique(), default=df['Status'].unique())
    df_f = df[df['Status'].isin(status_choice)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Value", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Orders", f"{len(df_f):,}")
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.2f}")

    st.divider()
    
    l, r = st.columns(2)
    with l:
        trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', title="Spending Trend"), use_container_width=True)
    with r:
        top = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Amount', y='Supplier', orientation='h', title="Top Suppliers"), use_container_width=True)

    st.subheader("Raw Data View")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
