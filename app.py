import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Intelligence", layout="wide")

# Professional UI Styling
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #ebedef; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
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
        
        # AGGRESSIVE FUZZY MAPPING
        def smart_find(keywords):
            for k in keywords:
                for col in df.columns:
                    if k.lower() in col.lower(): return col
            return None

        clean = pd.DataFrame()
        # Finding the Big 4: Amount, Date, Supplier, Status
        amt_col = smart_find(['PO Estimate Total', 'Total', 'Amount', 'Price', 'Value'])
        date_col = smart_find(['Added time', 'Date', 'Created', 'Time'])
        sup_col = smart_find(['Supplier', 'Vendor', 'Company', 'Entity'])
        stat_col = smart_find(['Status', 'State', 'Approval', 'Phase'])

        if amt_col and date_col:
            clean['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
            clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            clean['Supplier'] = df[sup_col].fillna('Unknown') if sup_col else 'Unknown'
            clean['Status'] = df[stat_col].fillna('Unknown') if stat_col else 'Unknown'
            
            # Additional analysis columns
            clean['YearMonth'] = clean['Date'].dt.strftime('%Y-%m')
            clean['Weekday'] = clean['Date'].dt.day_name()
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except: return None

df = load_data()

# --- HEADER SECTION ---
st.title("🛡️ Procurement Operations Command")
st.caption("Real-time analysis of purchase orders and vendor obligations")
st.divider()

if df is not None:
    # --- SIDEBAR CONTROL PANEL ---
    st.sidebar.header("🕹️ Control Panel")
    # Date Slider
    start_d, end_d = st.sidebar.date_input("Analysis Window", [df['Date'].min(), df['Date'].max()])
    # Status Multi-filter
    all_stats = df['Status'].unique().tolist()
    status_sel = st.sidebar.multiselect("Approval Filters", all_stats, default=all_stats)
    
    # Filter Execution
    mask = (df['Date'].dt.date >= start_d) & (df['Date'].dt.date <= end_ d) & (df['Status'].isin(status_sel))
    df_f = df.loc[mask]

    # --- TOP KPI SCORECARD ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Committed", f"${df_f['Amount'].sum():,.0f}")
    m2.metric("PO Volume", f"{len(df_f):,}")
    m3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")
    m4.metric("Active Vendors", df_f['Supplier'].nunique())

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROW 1: TRENDS & ALLOCATION ---
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🗓️ Spending Trajectory")
        trend = df_f.groupby('YearMonth')['Amount'].sum().reset_index().sort_values('YearMonth')
        fig_trend = px.area(trend, x='YearMonth', y='Amount', template="plotly_white", 
                            color_discrete_sequence=['#007bff'], markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with c2:
        st.subheader("⚖️ Budget Allocation")
        fig_pie = px.pie(df_f, names='Status', values='Amount', hole=0.6, 
                         color_discrete_sequence=px.colors.qualitative.Prism)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- ROW 2: VENDOR CONCENTRATION & TIMING ---
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("🏢 Top 10 High-Volume Vendors")
        top_v = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        fig_bar = px.bar(top_v, x='Amount', y='Supplier', orientation='h', 
                         color='Amount', color_continuous_scale='Blues')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c4:
        st.subheader("⏰ Peak Order Days")
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_df = df_f.groupby('Weekday')['Amount'].count().reindex(days).reset_index()
        fig_day = px.bar(day_df, x='Weekday', y='Amount', color='Amount', color_continuous_scale='Reds')
        st.plotly_chart(fig_day, use_container_width=True)

    # --- DATA EXPLORER ---
    with st.expander("🔍 Deep Dive: Itemized Transaction Log"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)

else:
    st.warning("📥 Dashboard standby. Please ensure data.xlsx is updated in GitHub with valid columns.")
