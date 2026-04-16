import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Master Dashboard", layout="wide")

# Professional Styling
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
        
        # Super-Aggressive Column Mapping
        def find_col(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in str(c).lower(): return c
            return None

        clean = pd.DataFrame()
        # Mapping the "Big 4"
        amt_col = find_col(['PO Estimate Total', 'Total', 'Amount', 'Value'])
        date_col = find_col(['Added time', 'Date', 'Created', 'Time'])
        sup_col = find_col(['Supplier', 'Vendor', 'Company'])
        stat_col = find_col(['Status', 'Approval', 'State'])

        if amt_col and date_col:
            clean['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
            clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            clean['Supplier'] = df[sup_col].fillna('Unknown') if sup_col else 'Unknown'
            clean['Status'] = df[stat_col].fillna('N/A') if stat_col else 'N/A'
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except: return None

df = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.title("🔍 Deep Dive Filters")
    
    # 1. Date Range
    min_d, max_d = df['Date'].min().date(), df['Date'].max().date()
    start_d, end_d = st.sidebar.date_input("Date Range", [min_d, max_d])
    
    # 2. Status Selection
    all_stats = sorted(df['Status'].unique().tolist())
    status_sel = st.sidebar.multiselect("Filter by Status", all_stats, default=all_stats)

    # Apply Filters
    mask = (df['Date'].dt.date >= start_d) & (df['Date'].dt.date <= end_d) & (df['Status'].isin(status_sel))
    df_f = df.loc[mask].copy()

    # --- MAIN DASHBOARD ---
    st.title("📊 Procurement Intelligence Command")
    
    # Row 1: Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Commited Value", f"${df_f['Amount'].sum():,.0f}")
    m2.metric("PO Volume", f"{len(df_f):,}")
    m3.metric("Avg Order Value", f"${df_f['Amount'].mean():,.0f}")
    m4.metric("Active Vendors", df_f['Supplier'].nunique())

    st.divider()

    # Row 2: Financial Trends
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📈 Spending Trajectory (Cumulative)")
        # Calculate cumulative spend over time
        trend = df_f.sort_values('Date')
        trend['Cumulative'] = trend['Amount'].cumsum()
        st.plotly_chart(px.area(trend, x='Date', y='Cumulative', template="plotly_white", color_discrete_sequence=['#007bff']), use_container_width=True)
    
    with c2:
        st.subheader("🎯 Portfolio by Status")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.5), use_container_width=True)

    # Row 3: Vendor Analysis
    st.subheader("🏆 Vendor Concentration (Top 15)")
    top_v = df_f.groupby('Supplier')['Amount'].sum().nlargest(15).reset_index()
    fig_bar = px.bar(top_v, x='Amount', y='Supplier', orientation='h', color='Amount', 
                     color_continuous_scale='Blues', text_auto='.2s')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

    # Row 4: Raw Data
    with st.expander("🔍 View Transaction-Level Data"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)

else:
    st.error("❌ Data Mapping Failed. Please check that your Excel file has 'PO Estimate Total' and 'Added time' columns.")
