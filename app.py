import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Dashboard", layout="wide")

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
                    if k.lower() in c.lower(): return c
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
            clean['Status'] = df[stat_col].fillna('Unknown')
            clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
            return clean.dropna(subset=['Amount', 'Date'])
        return None
    except:
        return None

df = load_data()

if df is not None:
    st.title("🛡️ Procurement Command Center")
    
    # --- SEARCH FILTER ---
    search = st.text_input("🔍 Search Supplier or Status", "").lower()
    df_f = df[df['Supplier'].str.lower().str.contains(search) | df['Status'].str.lower().str.contains(search)]

    # --- KPI ROW ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Spend", f"${df_f['Amount'].sum():,.0f}")
    m2.metric("Orders", len(df_f))
    m3.metric("Avg PO", f"${df_f['Amount'].mean():,.0f}")

    st.divider()

    # --- CHARTS ---
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Spending Trend")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        st.plotly_chart(px.area(trend, x='Month', y='Amount', template="plotly_white"), use_container_width=True)
    
    with c2:
        st.subheader("Status Distribution")
        st.plotly_chart(px.pie(df_f, names='Status', values='Amount', hole=0.4), use_container_width=True)

    # --- SUPPLIERS ---
    st.subheader("Top Suppliers")
    top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
    st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h', color='Amount'), use_container_width=True)

else:
    st.error("Data file not found or column names are incorrect.")
