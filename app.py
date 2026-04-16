import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Executive Dashboard", layout="wide")

# --- POWER BI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
    .stPlotlyChart { background-color: #ffffff; border-radius: 10px; padding: 5px; }
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
        
        def find(keys):
            for k in keys:
                for c in df.columns:
                    if k.lower() in str(c).lower(): return c
            return None

        # Clean Mappings
        clean = pd.DataFrame()
        amt_col = find(['PO Estimate Total', 'Total', 'Amount'])
        date_col = find(['Added time', 'Date', 'Created'])
        sup_col = find(['Supplier', 'Vendor'])
        stat_col = find(['Status', 'Approval'])
        item_col = find(['Item', 'Category', 'Description'])

        if amt_col and date_col:
            # Clean numeric data (Remove currency/commas)
            s_amt = df[amt_col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            clean['Amount'] = pd.to_numeric(s_amt, errors='coerce')
            clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            clean['Supplier'] = df[sup_col].fillna('Other') if sup_col else 'Other'
            clean['Status'] = df[stat_col].fillna('N/A') if stat_col else 'N/A'
            clean['Item'] = df[item_col].fillna('General') if item_col else 'General'
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except: return None

df = load_data()

if df is not None:
    # --- SLICERS (Sidebar) ---
    st.sidebar.title("📑 Report Filters")
    date_range = st.sidebar.date_input("Period", [df['Date'].min(), df['Date'].max()])
    sel_status = st.sidebar.multiselect("Status", df['Status'].unique(), default=df['Status'].unique())
    sel_supplier = st.sidebar.multiselect("Supplier", df['Supplier'].unique(), default=df['Supplier'].unique()[:5])

    # Filter Logic
    mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1]) & \
           (df['Status'].isin(sel_status)) & (df['Supplier'].isin(sel_supplier))
    df_f = df.loc[mask]

    # --- TOP ROW: KPI CARDS ---
    st.title("🚀 Procurement Intelligence Center")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Commited", f"${df_f['Amount'].sum():,.0f}")
    c2.metric("PO Volume", len(df_f))
    c3.metric("Avg PO", f"${df_f['Amount'].mean():,.0f}")
    c4.metric("Active Vendors", df_f['Supplier'].nunique())
    c5.metric("Item Categories", df_f['Item'].nunique())

    st.markdown("---")

    # --- MIDDLE ROW: TRENDS & ALLOCATION ---
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.subheader("🗓️ Financial Outflow Trend")
        t = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.area(t, x='Month', y='Amount', template="plotly_white", color_discrete_sequence=['#118DFF']), use_container_width=True)
    
    with col_r:
        st.subheader("🎯 Value by Status")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)

    # --- BOTTOM ROW: RANKINGS ---
    col_bl, col_br = st.columns(2)
    with col_bl:
        st.subheader("🏆 Top Suppliers")
        top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h', color='Amount', template="none"), use_container_width=True)
    
    with col_br:
        st.subheader("📦 Top Items/Categories")
        top_i = df_f.groupby('Item')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_i, x='Amount', y='Item', color='Item', template="none"), use_container_width=True)

    # --- DATA EXPLORER ---
    with st.expander("🔍 View Transaction Details"):
        st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
else:
    st.error("Data mapping failed. Check column names.")
