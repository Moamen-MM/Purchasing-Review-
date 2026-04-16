import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    # Find any data file in the repo
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files:
        st.error("No data files found in GitHub!")
        return None
    
    target = files[0]
    st.sidebar.info(f"Attempting to read: {target}")
    
    try:
        if target.endswith('.xlsx'):
            # THE FIX: use read_only=True to ignore the broken Excel styles/validations
            df = pd.read_excel(target, engine='openpyxl', read_only=True)
        else:
            # Auto-detect separator for CSVs
            df = pd.read_csv(target, sep=None, engine='python')

        # Robust Column Mapping (using positions)
        # PO(2), Supplier(10), Date(27), Amount(36), Status(54)
        df_final = pd.DataFrame()
        df_final['PO'] = df.iloc[:, 2].astype(str)
        df_final['Supplier'] = df.iloc[:, 10].fillna('Unknown')
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54].fillna('Pending')
        
        return df_final.dropna(subset=['Amount', 'Date'])
        
    except Exception as e:
        st.error(f"Critical Error: {e}")
        st.markdown("""
        ### ⚠️ How to fix this error:
        Your Excel file has internal 'Data Validation' or 'Styles' that are crashing the reader. 
        **Please do the following:**
        1. Open your Excel file on your computer.
        2. Go to **File > Save As**.
        3. Select **CSV (Comma Delimited) (*.csv)**.
        4. Upload that **new .csv file** to GitHub and delete the .xlsx file.
        """)
        return None

df = load_data()

if df is not None:
    # --- DASHBOARD ---
    st.sidebar.header("Dashboard Controls")
    selected_status = st.sidebar.multiselect("Status:", df['Status'].unique(), default=df['Status'].unique())
    df_f = df[df['Status'].isin(selected_status)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Orders", f"{len(df_f):,}")
    c3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.2f}")

    st.divider()
    
    l, r = st.columns(2)
    with l:
        trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', title="Monthly Trend"), use_container_width=True)
    with r:
        top = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Amount', y='Supplier', orientation='h', title="Top 10 Suppliers"), use_container_width=True)

    st.subheader("Purchase Order Log")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
