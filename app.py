import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files:
        st.error("No data file found in the repository!")
        return None
    
    target = files[0]
    try:
        if target.endswith('.xlsx'):
            df = pd.read_excel(target, engine='openpyxl')
        else:
            df = pd.read_csv(target, sep=None, engine='python')

        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]

        # Map columns by searching for keywords
        def find_col(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in c.lower(): return c
            return None

        col_amt = find_col(['PO Estimate Total', 'Amount', 'Total'])
        col_date = find_col(['Added time', 'Date', 'Created'])
        col_sup = find_col(['Supplier', 'Vendor'])
        col_stat = find_col(['Approval Status', 'Status'])

        if not col_amt or not col_date:
            st.error("Could not find Amount or Date columns.")
            return None

        # Build final dataframe
        df_final = pd.DataFrame()
        df_final['Amount'] = pd.to_numeric(df[col_amt], errors='coerce')
        df_final['Date'] = pd.to_datetime(df[col_date], errors='coerce')
        df_final['Supplier'] = df[col_sup].fillna('Unknown') if col_sup else 'Unknown'
        df_final['Status'] = df[col_stat].fillna('Pending') if col_stat else 'N/A'
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error: {e}")
        return None

df = load_data()

if df is not None:
    # --- FILTERS ---
    st.sidebar.header("Dashboard Filters")
    status_list = df['Status'].unique().tolist()
    choice = st.sidebar.multiselect("Select Status", status_list, default=status_list)
    df_f = df[df['Status'].isin(choice)]

    # --- METRICS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Total Orders", f"{len(df_f):,}")
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.2f}")

    st.divider()

    # --- TREND CHART ---
    st.subheader("Monthly Spending Trend")
    # THE CRITICAL FIX: We group by Year and Month manually to avoid the 'M' vs 'ME' error
    df_f['YearMonth'] = df_f['Date'].dt.to_period('M').dt.to_timestamp()
    trend = df_f.groupby('YearMonth')['Amount'].sum().reset_index()
    
    fig_trend = px.line(trend, x='YearMonth', y='Amount', markers=True, template="plotly_white")
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- SUPPLIER BAR CHART ---
    st.subheader("Top 10 Suppliers")
    top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
    fig_bar = px.bar(top_s, x='Amount', y='Supplier', orientation='h', color='Amount')
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- DATA ---
    st.subheader("Recent Order Records")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
