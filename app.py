import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Procurement Intelligence", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_file_exists=True)

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files: return None
    target = files[0]
    try:
        df = pd.read_excel(target) if target.endswith('.xlsx') else pd.read_csv(target, sep=None, engine='python')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping specific to your file structure
        clean = pd.DataFrame()
        amt_col = next((c for c in df.columns if 'PO Estimate Total' in c or 'Total' in c), None)
        date_col = next((c for c in df.columns if 'Added time' in c or 'Date' in c), None)
        sup_col = next((c for c in df.columns if 'Supplier' in c), None)
        stat_col = next((c for c in df.columns if 'Status' in c or 'State' in c), None)
        
        clean['Amount'] = pd.to_numeric(df[amt_col], errors='coerce')
        clean['Date'] = pd.to_datetime(df[date_col], errors='coerce')
        clean['Supplier'] = df[sup_col].fillna('Unknown')
        clean['Status'] = df[stat_col].fillna('Unknown')
        clean['Day'] = clean['Date'].dt.day_name()
        clean['Month'] = clean['Date'].dt.strftime('%Y-%m')
        
        return clean.dropna(subset=['Amount', 'Date'])
    except: return None

df = load_data()

# --- SIDEBAR & NAVIGATION ---
st.sidebar.title("🛠️ Analysis Tools")
if df is not None:
    date_range = st.sidebar.date_input("Date Range", [df['Date'].min(), df['Date'].max()])
    status_sel = st.sidebar.multiselect("Approval Status", df['Status'].unique(), default=df['Status'].unique())
    
    # Filter Logic
    mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1]) & (df['Status'].isin(status_sel))
    df_f = df.loc[mask]

    # --- MAIN DASHBOARD ---
    st.title("📈 Procurement Operations Center")
    
    # KPI SECTION
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Committed", f"${df_f['Amount'].sum():,.0f}", help="Total value of all filtered POs")
    c2.metric("PO Count", len(df_f))
    c3.metric("Avg PO Value", f"${df_f['Amount'].mean():,.0f}")
    c4.metric("Unique Vendors", df_f['Supplier'].nunique())

    st.markdown("---")

    # ROW 1: TRENDS
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Monthly Financial Outflow")
        trend = df_f.groupby('Month')['Amount'].sum().reset_index().sort_values('Month')
        fig = px.area(trend, x='Month', y='Amount', color_discrete_sequence=['#3366cc'], template="plotly_white")
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("Status Distribution")
        fig_pie = px.pie(df_f, names='Status', values='Amount', hole=0.5, 
                         color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, width='stretch')

    # ROW 2: SUPPLIERS & HEATMAP
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top 10 High-Value Suppliers")
        top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        fig_bar = px.bar(top_s, x='Amount', y='Supplier', orientation='h', color='Amount', template="plotly_white")
        st.plotly_chart(fig_bar, width='stretch')
        
    with col4:
        st.subheader("Ordering Activity Heatmap")
        # Days of week order
        order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heat = df_f.groupby('Day')['Amount'].count().reindex(order).reset_index()
        fig_heat = px.bar(heat, x='Day', y='Amount', title="Volume by Day of Week", color='Amount')
        st.plotly_chart(fig_heat, width='stretch')

    # ROW 3: RECENT TRANSACTIONS
    st.subheader("🔍 Detailed Transaction Log")
    st.dataframe(df_f[['Date', 'Supplier', 'Amount', 'Status']].sort_values('Date', ascending=False), 
                 width='stretch', height=400)

else:
    st.info("Upload your Excel data to begin analysis.")
