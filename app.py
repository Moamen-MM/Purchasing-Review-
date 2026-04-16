import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    try:
        # Load the data - skip the first row (the title)
        df = pd.read_csv("data.csv", header=0)
        
        # Instead of names, we use positions (0, 1, 2...)
        # Based on your file structure:
        # Col 2 = PO_Number, Col 10 = Supplier, Col 27 = Added time, Col 36 = Amount
        
        df_final = pd.DataFrame()
        df_final['PO'] = df.iloc[:, 2]
        df_final['Supplier'] = df.iloc[:, 10]
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54] # Approval Status
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error: {e}")
        # Show the columns to help debug if it fails
        if 'df' in locals():
            st.write("Columns found:", list(df.columns))
        return None

df = load_data()

if df is not None:
    # --- VISUALS ---
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Spent", f"${df['Amount'].sum():,.2f}")
    with c2:
        st.metric("Total Orders", f"{len(df):,}")

    st.divider()
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Spending Trend")
        trend = df.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount'), use_container_width=True)
        
    with col_r:
        st.subheader("Top Suppliers")
        top = df.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Amount', y='Supplier', orientation='h'), use_container_width=True)

    st.subheader("Data View")
    st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)
