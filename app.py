import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Command Center", layout="wide")

# Styling for a professional dashboard look
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #f0f2f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    try:
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        df.columns = [str(c).strip() for c in df.columns]
        
        def find_col(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in str(c).lower(): return c
            return None

        clean = pd.DataFrame()
        amt_name = find_col(['PO Estimate Total', 'Total', 'Amount'])
        date_name = find_col(['Added time', 'Date', 'Created'])
        sup_name = find_col(['Supplier', 'Vendor'])
        stat_name = find_col(['Status', 'Approval'])

        if amt_name and date_name:
            # CLEANING NUMBERS: Removes currency symbols, commas, and spaces
            s_amt = df[amt_name].astype(str).str.replace(r'[^\d.]', '', regex=True)
            clean['Amount'] = pd.to_numeric(s_amt, errors='coerce')
            
            clean['Date'] = pd.to_datetime(df[date_name], errors='coerce')
            clean['Supplier'] = df[sup_name].fillna('Unknown') if sup_name else 'Unknown'
            clean['Status'] = df[stat_name].fillna('N/A') if stat_name else 'N/A'
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            
            # Drop rows where critical data failed to convert
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except Exception as e:
        st.error(f"Error processing columns: {e}")
        return None

df = load_data()

if df is not None and not df.empty:
    # --- SIDEBAR FILTERS ---
    st.sidebar.title("🔍 Global Filters")
    
    # Ensure date range includes the entire dataset by default
    min_d, max_d = df['Date'].min().date(), df['Date'].max().date()
    date_range = st.sidebar.date_input("Analysis Window", [min_d, max_d])
    
    status_list = sorted(df['Status'].unique().tolist())
    status_sel = st.sidebar.multiselect("Filter Status", status_list, default=status_list)

    # Filter Application
    if len(date_range) == 2:
        mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1]) & (df['Status'].isin(status_sel))
        df_f = df.loc[mask].copy()
    else:
        df_f = df.copy()

    # --- MAIN UI ---
    st.title("🛡️ Procurement Intelligence Command")
    
    # KPI SECTION
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Commited Value", f"${df_f['Amount'].sum():,.0f}")
    k2.metric("Total POs", f"{len(df_f):,}")
    k3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")
    k4.metric("Vendors", df_f['Supplier'].nunique())

    st.divider()

    # CHARTS
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🗓️ Spending Trajectory")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.area(trend, x='Month', y='Amount', template="plotly_white", markers=True), use_container_width=True)
    
    with c2:
        st.subheader("⚖️ Status Allocation")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.5), use_container_width=True)

    # BAR CHART
    st.subheader("🏆 Top Suppliers by Value")
    top_v = df_f.groupby('Supplier')['Amount'].sum().nlargest(15).reset_index()
    st.plotly_chart(px.bar(top_v, x='Amount', y='Supplier', orientation='h', color='Amount', color_continuous_scale='Blues'), use_container_width=True)

    # RAW DATA
    with st.expander("🔍 View Raw Transactions"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)

else:
    st.error("🚨 Data found, but could not be visualized.")
    st.info("Check if your 'Amount' column contains currency text or if your 'Date' column is empty.")
