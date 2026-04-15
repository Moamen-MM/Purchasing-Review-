import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    try:
        # 1. Read the raw file
        raw_df = pd.read_csv("cleaned_purchasing_data.csv", header=None)
        
        # 2. Find the row that contains 'PO_Number'
        header_row_index = 0
        for i, row in raw_df.head(10).iterrows():
            if row.astype(str).str.contains('PO_Number').any():
                header_row_index = i
                break
        
        # 3. Reload the dataframe using that row as the header
        df = pd.read_csv("cleaned_purchasing_data.csv", header=header_row_index)
        
        # 4. Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # 5. Map the necessary columns using flexible naming
        def get_col(options):
            for opt in options:
                for col in df.columns:
                    if opt.lower() == col.lower() or opt.lower() in col.lower():
                        return col
            return None

        # Define our targets
        target_amt = get_col(['PO Estimate Total', 'Total Amount', 'Amount', 'Total'])
        target_date = get_col(['Added time', 'Date', 'Clean Date'])
        target_status = get_col(['Approval Status', 'Status'])
        target_po = get_col(['PO_Number', 'PO Number', 'Serial'])
        target_supplier = get_col(['Supplier', 'Vendor'])

        # 6. Final Data Cleaning
        df['Amount'] = pd.to_numeric(df[target_amt], errors='coerce')
        df['Date'] = pd.to_datetime(df[target_date], errors='coerce')
        df['Display_Status'] = df[target_status].fillna('Unknown')
        df['Display_Supplier'] = df[target_supplier].fillna('No Supplier')
        df['Display_PO'] = df[target_po].fillna('N/A')

        # Drop rows where we definitely don't have an amount or date
        return df.dropna(subset=['Amount', 'Date'])
    
    except Exception as e:
        st.error(f"Critical Error: {e}")
        return None

df = load_data()

if df is not None:
    # --- DASHBOARD LAYOUT ---
    st.sidebar.header("Filters")
    status_choice = st.sidebar.multiselect("Status", df['Display_Status'].unique(), default=df['Display_Status'].unique())
    df_f = df[df['Display_Status'].isin(status_choice)]

    # KPI Row
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Orders Count", f"{len(df_f):,}")
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.2f}")

    st.divider()

    # Charts Row
    l, r = st.columns(2)
    with l:
        st.subheader("Spending Trend")
        trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', template="plotly_white"), use_container_width=True)
    
    with r:
        st.subheader("Top 10 Suppliers")
        top_s = df_f.groupby('Display_Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_s, x='Amount', y='Display_Supplier', orientation='h', template="plotly_white"), use_container_width=True)

    # Table
    st.subheader("Detailed Logs")
    st.dataframe(df_f[['Date', 'Display_PO', 'Display_Supplier', 'Amount', 'Display_Status']].sort_values('Date', ascending=False), use_container_width=True)
else:
    st.info("Still searching for the correct columns... Please ensure your CSV matches the structure of the original file.")
