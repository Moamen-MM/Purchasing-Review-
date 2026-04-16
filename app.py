import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🛒 Purchasing Dashboard")

# 1. Direct Load
try:
    # We change the name to 'data.csv' to match your new upload
    df = pd.read_csv("data.csv")
    
    # 2. Hard-rename columns to handle any hidden spaces
    df.columns = [str(c).strip() for c in df.columns]
    
    # 3. Basic Cleaning
    df['Amount'] = pd.to_numeric(df['PO Estimate Total'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Added time'], errors='coerce')
    df = df.dropna(subset=['Amount', 'Date'])

    # 4. Simple Visuals
    st.metric("Total Spending", f"${df['Amount'].sum():,.2f}")
    
    fig = px.bar(df.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index(), 
                 x='Amount', y='Supplier', orientation='h', title="Top 10 Suppliers")
    st.plotly_chart(fig)
    
    st.write("### All Data", df[['PO_Number', 'Supplier', 'Amount']])

except Exception as e:
    st.error(f"Waiting for data... Error: {e}")
    st.info("Make sure 'data.csv' is uploaded to GitHub and the first row is the headers.")
