import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    all_files = os.listdir('.')
    data_files = [f for f in all_files if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    
    if not data_files:
        st.error("No data files found!")
        return None
    
    target = data_files[0]
    st.sidebar.info(f"Connected to: {target}")
    
    try:
        if target.endswith('.xlsx'):
            # THE FIX: use data_only=True to ignore problematic Excel formatting
            df = pd.read_excel(target, engine='openpyxl')
        else:
            df = pd.read_csv(target, sep=None, engine='python')

        # Create display table using column positions
        df_final = pd.DataFrame()
        df_final['PO'] = df.iloc[:, 2].astype(str)
        df_final['Supplier'] = df.iloc[:, 10].fillna('Unknown')
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54].fillna('Pending')
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        # If openpyxl fails, try a different engine as a backup
        try:
            df = pd.read_excel(target, engine='xlrd')
            # (Repeat mapping logic here if needed, but openpyxl is usually the fix)
            st.error(f"Engine error. Please save your Excel as a standard .xlsx file.")
        except:
            st.error(f"Critical Error reading {target}: {e}")
        return None

df = load_data()

if df is not None:
    # --- DASHBOARD UI ---
    st.sidebar.header("Filters")
    status_list = df['Status'].unique().tolist()
    selected = st.sidebar.multiselect("Status:", status_list, default=status_list)
    df_f = df[df['Status'].isin(selected)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Total Orders", f"{len(df_f):,}")
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.2f}")

    st.divider()
    
    l, r = st.columns(2)
    with l:
        trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', title="Monthly Spend"), use_container_width=True)
    with r:
        top = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Amount', y='Supplier', orientation='h', title="Top Suppliers"), use_container_width=True)

    st.subheader("Order Log")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
