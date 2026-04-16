import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Executive Procurement Insights", layout="wide")

# Custom CSS for a professional "Dark Mode" feel to charts
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #f0f2f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
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
            clean['Status'] = df[stat_col].fillna('N/A')
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            clean['Year'] = clean['Date'].dt.year
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except: return None

df = load_data()

if df is not None:
    # --- SIDEBAR NAV ---
    st.sidebar.title("🎮 Dashboard Controls")
    
    # Date Slider
    min_d, max_d = df['Date'].min().date(), df['Date'].max().date()
    date_range = st.sidebar.slider("Timeline Selection", min_d, max_d, (min_d, max_d))
    
    # Category Filters
    all_suppliers = sorted(df['Supplier'].unique().tolist())
    selected_suppliers = st.sidebar.multiselect("Filter Suppliers", all_suppliers, default=all_suppliers[:10] if len(all_suppliers) > 10 else all_suppliers)
    
    all_stats = df['Status'].unique().tolist()
    selected_stats = st.sidebar.multiselect("Filter Status", all_stats, default=all_stats)

    # Filter Logic
    mask = (df['Date'].dt.date >= date_range[0]) & \
           (df['Date'].dt.date <= date_range[1]) & \
           (df['Status'].isin(selected_stats)) & \
           (df['Supplier'].isin(selected_suppliers))
    
    df_f = df.loc[mask]

    # --- MAIN CONTENT ---
    st.title("🛡️ Procurement Intelligence Command")
    st.caption(f"Analyzing {len(df_f)} records from {date_range[0]} to {date_range[1]}")
    
    # Executive KPIs
    k1, k2, k3, k4 = st.columns(4)
    total_spend = df_f['Amount'].sum()
    k1.metric("Total Spend", f"${total_spend:,.0f}")
    k2.metric("Orders Processed", f"{len(df_f):,}")
    k3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")
    k4.metric("Vendors Engaged", df_f['Supplier'].nunique())

    st.divider()

    # Visual Row 1: Time & Composition
    row1_left, row1_right = st.columns([2, 1])
    
    with row1_left:
        st.subheader("📈 Financial Velocity (Monthly)")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        fig_line = px.area(trend, x='Month', y='Amount', template="plotly_white", color_discrete_sequence=['#007bff'])
        fig_line.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_line, use_container_width=True)
    
    with row1_right:
        st.subheader("🎯 Status Distribution")
        fig_pie = px.pie(df_f, names='Status', values='Amount', hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
        fig_pie.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Visual Row 2: Supplier Rankings
    st.subheader("🏆 Top 15 Suppliers by Committed Value")
    top_v = df_f.groupby('Supplier')['Amount'].sum().nlargest(15).reset_index()
    fig_bar = px.bar(top_v, x='Amount', y='Supplier', orientation='h', 
                     color='Amount', color_continuous_scale='Blues', text_auto='.2s')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Visual Row 3: Detail Explorer
    with st.expander("🔍 Itemized Procurement Log"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)

else:
    st.info("System Standby. Connect your data.xlsx to begin.")
