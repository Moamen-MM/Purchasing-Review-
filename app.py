import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    try:
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        # Simple search for columns
        def find(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in str(c).lower(): return c
            return None
        
        clean = pd.DataFrame()
        clean['Amount'] = pd.to_numeric(df[find(['Total', 'Amount'])], errors='coerce')
        clean['Date'] = pd.to_datetime(df[find(['Added', 'Date'])], errors='coerce')
        clean['Supplier'] = df[find(['Supplier', 'Vendor'])].fillna('Unknown')
        return clean.dropna(subset=['Amount', 'Date'])
    except: return None

df = load_data()
st.title("🛒 Purchasing Dashboard")

if df is not None:
    st.metric("Total Spending", f"${df['Amount'].sum():,.2f}")
    # Safe Trend Chart
    df['Month'] = df['Date'].dt.strftime('%Y-%m')
    trend = df.groupby('Month')['Amount'].sum().reset_index()
    st.plotly_chart(px.line(trend, x='Month', y='Amount'))
    st.dataframe(df.sort_values('Date', ascending=False))
else:
    st.error("Please ensure your data file is uploaded to GitHub.")
