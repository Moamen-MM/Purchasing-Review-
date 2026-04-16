import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Intelligence", layout="wide", initial_sidebar_state="expanded")

# Professional Styling
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
        
        clean = pd.DataFrame()
        # Direct Keyword Mapping
        amt_col = next((c for c in df.columns if 'PO Estimate Total' in c or 'Total' in c), None)
        date_col = next((c for c in df.columns if 'Added time' in c or 'Date' in c), None)
        sup_col = next((c for c in df.columns if 'Supplier' in c), None)
        stat_col = next((c for c in df.columns if 'Status' in c or 'State' in c), None)
        
        clean['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
        clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
        clean['Supplier'] = df[sup_col].fillna('Unknown')
        clean['Status'] = df[stat_col].fillna('Unknown')
        
        # Derived features
        clean['Day'] = clean['Date'].dt.day_name()
        clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
        
        return clean.dropna(subset=['Amount', 'Date'])
    except: return None

df = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.title("🛠️ Analysis Tools")
    # Date Range Filter
    min_date, max_date = df['Date'].min().date(), df['Date'].max().date()
    start_date, end_date = st.sidebar.date_input("Date Range", [min_date, max_date])
    
    # Status Multi-select
    all_status = df['Status'].unique().tolist()
    status_sel = st.sidebar.multiselect("Approval Status", all_status, default=all_status)
    
    # Apply Filters
    mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date) & (df['Status'].isin(status_sel))
    df_f = df.loc[mask]

    # --- MAIN DASHBOARD ---
    st.title("📈 Procurement Operations Center")
    
    # KPI SECTION
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Spend", f"${df_f['Amount'].sum():,.0f}")
    k2.metric("PO Count", f"{len(df_f):,}")
    k3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")
    k4.metric("Active Vendors", df_f['Supplier'].nunique())

    st.divider()

    # VISUAL ROW 1: TREND & STATUS
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Monthly Spending Outflow")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.area(trend, x='Month', y='Amount', template="plotly_white", color_discrete_sequence=['#1f77b4']), use_container_width=True)
    
    with col2:
        st.subheader("Status Breakdown")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)

    # VISUAL ROW 2: SUPPLIERS & VOLUME
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top 10 High-Value Suppliers")
        top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h', color='Amount', template="plotly_white"), use_container_width=True)
        
    with col4:
        st.subheader("Volume by Day of Week")
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_vol = df_f.groupby('Day')['Amount'].count().reindex(days).fillna(0).reset_index()
        st.plotly_chart(px.bar(day_vol, x='Day', y='Amount', color_discrete_sequence=['#ff7f0e']), use_container_width=True)

    # RECENT DATA
    with st.expander("🔍 Detailed Transaction Log"):
        st.dataframe(df_f[['Date', 'Supplier', 'Amount', 'Status']].sort_values('Date', ascending=False), use_container_width=True)

else:
    st.info("Waiting for data... Please ensure your Excel file is uploaded correctly.")
