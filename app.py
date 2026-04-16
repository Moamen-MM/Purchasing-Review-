import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and not f.startswith('.')]
    if not files:
        st.error("No data file found!")
        return None
    
    target = files[0]
    try:
        if target.endswith('.xlsx'):
            df = pd.read_excel(target, engine='openpyxl')
        else:
            df = pd.read_csv(target, sep=None, engine='python')

        # CLEAN HEADERS: Remove spaces and dots
        df.columns = [str(c).strip().replace('.1', '') for c in df.columns]

        # SMART MAPPING: Find columns by name instead of number
        def find_col(possible_names):
            for name in possible_names:
                for col in df.columns:
                    if name.lower() in col.lower():
                        return col
            return None

        # Map our core data fields
        col_map = {
            'po': find_col(['PO_Number', 'PO Number', 'Serial']),
            'supplier': find_col(['Supplier', 'Vendor']),
            'date': find_col(['Added time', 'Date', 'Created']),
            'amount': find_col(['PO Estimate Total', 'Amount', 'Total']),
            'status': find_col(['Approval Status', 'Status'])
        }

        # Check if we found the bare minimum
        if not col_map['amount'] or not col_map['date']:
            st.error(f"Could not find Amount or Date columns. Available: {list(df.columns)[:10]}")
            return None

        # Create the final table
        df_final = pd.DataFrame()
        df_final['PO'] = df[col_map['po']].astype(str) if col_map['po'] else "N/A"
        df_final['Supplier'] = df[col_map['supplier']].fillna('Unknown') if col_map['supplier'] else "N/A"
        df_final['Date'] = pd.to_datetime(df[col_map['date']], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df[col_map['amount']], errors='coerce')
        df_final['Status'] = df[col_map['status']].fillna('Pending') if col_map['status'] else "Unknown"
        
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

df = load_data()

if df is not None:
    # --- UI ---
    st.sidebar.header("Controls")
    selected_status = st.sidebar.multiselect("Filter by Status", df['Status'].unique(), default=df['Status'].unique())
    df_f = df[df['Status'].isin(selected_status)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Orders", f"{len(df_f):,}")
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.2f}")

    st.divider()
    
    l, r = st.columns(2)
    with l:
        # Time-series fix for different Pandas versions
        try:
            trend = df_f.set_index('Date').resample('ME')['Amount'].sum().reset_index()
        except:
            trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', markers=True), use_container_width=True)
    with r:
        top_s = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_s, x='Amount', y='Supplier', orientation='h', color='Amount'), use_container_width=True)

    st.subheader("Purchase Order Log")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
