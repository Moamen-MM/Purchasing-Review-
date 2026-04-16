import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Insights", layout="wide")

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    try:
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Smart Column Finder
        def find(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in c.lower(): return c
            return None

        clean = pd.DataFrame()
        # Find Amount, Date, Supplier, and Status
        clean['Amount'] = pd.to_numeric(df[find(['Total', 'Amount', 'Estimate'])], errors='coerce')
        clean['Date'] = pd.to_datetime(df[find(['Added', 'Date', 'Time'])], errors='coerce')
        clean['Supplier'] = df[find(['Supplier', 'Vendor', 'Company'])].fillna('Unknown')
        clean['Status'] = df[find(['Status', 'State', 'Approval'])].fillna('Unknown')
        
        return clean.dropna(subset=['Amount', 'Date'])
    except: return None

df = load_data()

# --- HEADER ---
st.title("🚀 Purchasing Intelligence Dashboard")
st.markdown("---")

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Navigation & Filters")
    status_filter = st.sidebar.multiselect("Filter by Status", df['Status'].unique(), default=df['Status'].unique())
    df_f = df[df['Status'].isin(status_filter)]

    # --- TOP KPI ROW ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Spend", f"${df_f['Amount'].sum():,.0f}")
    kpi2.metric("Orders", len(df_f))
    kpi3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")
    kpi4.metric("Active Suppliers", df_f['Supplier'].nunique())

    st.markdown("---")

    # --- VISUAL ROW 1: TREND & STATUS ---
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📈 Spending Trend (Monthly)")
        df_f['Month'] = df_f['Date'].dt.strftime('%Y-%m')
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        fig_line = px.line(trend, x='Month', y='Amount', markers=True, template="plotly_white", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig_line, width='stretch')

    with col_right:
        st.subheader("🎯 Status Breakdown")
        fig_pie = px.pie(df_f, names='Status', values='Amount', hole=0.4, template="plotly_white")
        st.plotly_chart(fig_pie, width='stretch')

    # --- VISUAL ROW 2: TOP SUPPLIERS ---
    st.subheader("🏆 Top 10 Suppliers by Value")
    top_sup = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
    fig_bar = px.bar(top_sup, x='Amount', y='Supplier', orientation='h', 
                     color='Amount', color_continuous_scale='Viridis', template="plotly_white")
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, width='stretch')

    # --- DATA TABLE ---
    with st.expander("📂 View Raw Transaction Data"):
        st.dataframe(df_f.sort_values('Date', ascending=False), width='stretch')

else:
    st.error("Could not process data. Check your Excel column names!")
