import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Executive Purchasing Dashboard", layout="wide")

# --- CUSTOM POWER BI STYLE ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    h1 { color: #1f4e78; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    try:
        # Load file
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        df.columns = [str(c).strip() for c in df.columns]
        
        # SMART COLUMN FINDER
        def find_col(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in str(c).lower(): return c
            return None

        # Map Columns
        amt_col = find_col(['PO Estimate Total', 'Total', 'Amount', 'Value'])
        date_col = find_col(['Added time', 'Date', 'Created'])
        sup_col = find_col(['Supplier', 'Vendor'])
        stat_col = find_col(['Status', 'Approval'])
        cat_col = find_col(['Category', 'Item', 'Type', 'Description'])

        if amt_col and date_col:
            clean = pd.DataFrame()
            # DATA HAMMER: Remove everything except numbers and decimals (Fixes EGP/$ errors)
            s_amt = df[amt_col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            clean['Amount'] = pd.to_numeric(s_amt, errors='coerce')
            
            clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            clean['Supplier'] = df[sup_col].fillna('Unknown') if sup_col else 'Unknown'
            clean['Status'] = df[stat_col].fillna('N/A') if stat_col else 'N/A'
            clean['Category'] = df[cat_col].fillna('Other') if cat_col else 'General'
            
            # Helper Columns
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            clean['Weekday'] = clean['Date'].dt.day_name()
            
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except: return None

df = load_data()

if df is not None and not df.empty:
    st.title("📊 Executive Procurement Command Center")
    st.markdown("---")

    # --- SIDEBAR FILTERS (Slicers) ---
    st.sidebar.header("🕹️ Report Slicers")
    
    # Date Slider
    min_date, max_date = df['Date'].min().date(), df['Date'].max().date()
    date_range = st.sidebar.slider("Timeline", min_date, max_date, (min_date, max_date))
    
    # Multiselects
    all_stats = sorted(df['Status'].unique().tolist())
    sel_stats = st.sidebar.multiselect("Status Filter", all_stats, default=all_stats)
    
    # Filter Data
    mask = (df['Date'].dt.date >= date_range[0]) & \
           (df['Date'].dt.date <= date_range[1]) & \
           (df['Status'].isin(sel_stats))
    df_f = df.loc[mask]

    # --- KPI CARDS (Cards) ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Committed", f"${df_f['Amount'].sum():,.0f}")
    k2.metric("Total Orders", f"{len(df_f):,}")
    k3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")
    k4.metric("Active Vendors", df_f['Supplier'].nunique())

    st.divider()

    # --- ROW 1: TREND & STATUS ---
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📈 Financial Outflow Trend")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        fig_area = px.area(trend, x='Month', y='Amount', template="plotly_white", 
                           color_discrete_sequence=['#1f4e78'], markers=True)
        st.plotly_chart(fig_area, use_container_width=True)

    with c2:
        st.subheader("🎯 Distribution by Status")
        fig_donut = px.pie(df_f, names='Status', values='Amount', hole=0.5, 
                           color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_donut, use_container_width=True)

    # --- ROW 2: SUPPLIERS & WEEKDAYS ---
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("🏆 Top 10 Suppliers")
        top_v = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        fig_bar = px.bar(top_v, x='Amount', y='Supplier', orientation='h', 
                         color='Amount', color_continuous_scale='Blues')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c4:
        st.subheader("⏰ Peak Ordering Days")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_data = df_f.groupby('Weekday')['Amount'].count().reindex(day_order).reset_index()
        st.plotly_chart(px.bar(day_data, x='Weekday', y='Amount', color_discrete_sequence=['#ff7f0e']), use_container_width=True)

    # --- ROW 3: CATEGORY ANALYSIS (New Power BI Visual) ---
    st.subheader("📦 Spending by Category / Item Type")
    cat_data = df_f.groupby('Category')['Amount'].sum().reset_index().sort_values('Amount', ascending=False)
    st.plotly_chart(px.bar(cat_data, x='Category', y='Amount', color='Category', template="plotly_white"), use_container_width=True)

    # --- DATA EXPLORER ---
    with st.expander("🔍 Deep Dive: Itemized Transaction Log"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)

else:
    st.error("🚨 Blank Boxes Detected! The code found your file, but the 'Amount' or 'Date' columns are unreadable.")
    st.info("Check your column names in the Excel file.")
