import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Dashboard", layout="wide")

# Professional UI Styling
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
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
        amt_col = find_col(['PO Estimate Total', 'Total', 'Amount'])
        date_col = find_col(['Added time', 'Date', 'Created'])
        sup_col = find_col(['Supplier', 'Vendor'])
        stat_col = find_col(['Status', 'Approval'])

        if amt_col and date_col:
            clean['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
            clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            clean['Supplier'] = df[sup_col].fillna('Unknown')
            clean['Status'] = df[stat_col].fillna('Pending')
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except: return None

df = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🕹️ Global Filters")
    
    # Date Filter
    min_date, max_date = df['Date'].min().date(), df['Date'].max().date()
    date_range = st.sidebar.slider("Select Date Range", min_date, max_date, (min_date, max_date))
    
    # Status Multi-select
    all_statuses = df['Status'].unique().tolist()
    status_sel = st.sidebar.multiselect("Approval Status", all_statuses, default=all_statuses)
    
    # Supplier Search
    search = st.sidebar.text_input("🔍 Search Supplier", "")

    # Apply Filters
    mask = (df['Date'].dt.date >= date_range[0]) & \
           (df['Date'].dt.date <= date_range[1]) & \
           (df['Status'].isin(status_sel)) & \
           (df['Supplier'].str.contains(search, case=False))
    
    df_f = df.loc[mask]

    # --- HEADER ---
    st.title("🛡️ Procurement Intelligence Hub")
    
    # KPI ROW
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Spend", f"${df_f['Amount'].sum():,.0f}")
    c2.metric("PO Volume", len(df_f))
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.0f}")
    c4.metric("Active Vendors", df_f['Supplier'].nunique())

    st.divider()

    # --- CHARTS ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Monthly Spending Outflow")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.area(trend, x='Month', y='Amount', template="plotly_white"), use_container_width=True)
    
    with col2:
        st.subheader("🎯 Value by Status")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.4), use_container_width=True)

    st.subheader("🏆 Top 10 Suppliers by Committed Value")
    top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
    st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h', color='Amount', color_continuous_scale='Blues'), use_container_width=True)

    # --- TABLE ---
    with st.expander("📋 View Filtered Transaction Log"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
else:
    st.info("Dashboard standby. Connect your data file on GitHub to begin.")
