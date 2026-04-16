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
        st.error("No data file found in GitHub!")
        return None
    
    target = files[0]
    try:
        # Load file based on type
        if target.endswith('.xlsx'):
            df = pd.read_excel(target, engine='openpyxl')
        else:
            df = pd.read_csv(target, sep=None, engine='python')

        # Find columns by name
        def find_col(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in str(c).lower(): return c
            return None

        # Cleaned Data
        clean = pd.DataFrame()
        clean['Amount'] = pd.to_numeric(df[find_col(['Amount', 'Total', 'Estimate'])], errors='coerce')
        clean['Date'] = pd.to_datetime(df[find_col(['Added', 'Date', 'Time'])], errors='coerce')
        clean['Supplier'] = df[find_col(['Supplier', 'Vendor'])].fillna('Unknown')
        
        return clean.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error: {e}")
        return None

df = load_data()

if df is not None:
    # KPI
    st.metric("Total Spending", f"${df['Amount'].sum():,.2f}")
    
    # Trend Chart (Safe grouping)
    df['Month'] = df['Date'].dt.strftime('%Y-%m')
    trend = df.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
    st.plotly_chart(px.line(trend, x='Month', y='Amount', title="Monthly Trend"), use_container_width=True)

    # Table
    st.subheader("Data Records")
    st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)
