import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    
    try:
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        # Clean up column names (remove spaces/dots)
        df.columns = [str(c).strip() for c in df.columns]

        # Helper to find column even if name is slightly different
        def find_any(keys):
            for k in keys:
                for col in df.columns:
                    if k.lower() in col.lower(): return col
            return None

    except Exception as e:
        st.error(f"File Load Error: {e}")
        return None

    # CRITICAL MAPPING
    final = pd.DataFrame()
    
    # 1. Find Amount (Looking for Total, Estimate, or Price)
    amt_col = find_any(['PO Estimate Total', 'Total', 'Amount', 'Price'])
    # 2. Find Date (Looking for Time, Date, or Created)
    date_col = find_any(['Added time', 'Date', 'Created', 'Time'])
    # 3. Find Supplier
    sup_col = find_any(['Supplier', 'Vendor', 'Company'])
    # 4. Find Status
    stat_col = find_any(['Approval Status', 'Status', 'State'])

    if amt_col and date_col:
        final['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
        final['Date'] = pd.to_datetime(df[date_col], errors='coerce')
        final['Supplier'] = df[sup_col].fillna('Unknown') if sup_col else 'N/A'
        final['Status'] = df[stat_col].fillna('N/A') if stat_col else 'N/A'
        
        # Show what we found in the sidebar for debugging
        st.sidebar.success(f"Linked: {amt_col} & {date_col}")
        return final.dropna(subset=['Amount', 'Date'])
    else:
        st.sidebar.error("Could not find 'Amount' or 'Date' columns.")
        st.sidebar.write("Available columns:", list(df.columns)[:10])
        return None

df = load_data()

if df is not None:
    # FILTERS
    status_list = ["All"] + df['Status'].unique().tolist()
    choice = st.sidebar.selectbox("Filter by Status", status_list)
    
    df_display = df if choice == "All" else df[df['Status'] == choice]

    # TOP ROW
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_display['Amount'].sum():,.2f}")
    c2.metric("Total Orders", len(df_display))
    c3.metric("Avg Order", f"${df_display['Amount'].mean():,.2f}")

    st.divider()

    # TREND CHART
    st.subheader("Monthly Spending Trend")
    df_display['Month'] = df_display['Date'].dt.strftime('%Y-%m')
    trend = df_display.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
    st.plotly_chart(px.line(trend, x='Month', y='Amount', markers=True), width='stretch')

    # DATA LIST
    st.subheader("All Records")
    st.dataframe(df_display.sort_values('Date', ascending=False), width='stretch')
else:
    st.info("👋 Welcome! Please ensure your Excel file has 'Date' and 'Amount' columns.")
