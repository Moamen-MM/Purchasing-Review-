import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    # Look for the new CSV file
    if os.path.exists("data.csv"):
        target = "data.csv"
    else:
        # Fallback to any CSV in the folder
        files = [f for f in os.listdir('.') if f.endswith('.csv')]
        if not files:
            st.error("Please upload 'data.csv' to GitHub.")
            return None
        target = files[0]

    try:
        # Read the CSV (sep=None handles commas or semicolons automatically)
        df = pd.read_csv(target, sep=None, engine='python')

        # Clean mapping using column positions
        df_final = pd.DataFrame()
        df_final['PO'] = df.iloc[:, 2].astype(str)
        df_final['Supplier'] = df.iloc[:, 10].fillna('Unknown')
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54].fillna('Pending')
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        return None

df = load_data()

if df is not None:
    # --- UI ---
    st.sidebar.header("Controls")
    selected_status = st.sidebar.multiselect("Status:", df['Status'].unique(), default=df['Status'].unique())
    df_f = df[df['Status'].isin(selected_status)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Total Orders", f"{len(df_f):,}")
    c3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.2f}")

    st.divider()
    
    l, r = st.columns(2)
    with l:
        trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', title="Spending Trend"), use_container_width=True)
    with r:
        top = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Amount', y='Supplier', orientation='h', title="Top Suppliers"), use_container_width=True)

    st.subheader("Recent Activity Table")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
