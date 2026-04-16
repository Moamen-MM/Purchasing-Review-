import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_data():
    try:
        # We target the exact filename you have in your screenshot
        df = pd.read_excel("data.xlsx")

        # Create the display table using the column positions from your file
        df_final = pd.DataFrame()
        df_final['PO'] = df.iloc[:, 2].astype(str)
        df_final['Supplier'] = df.iloc[:, 10].fillna('Unknown')
        df_final['Date'] = pd.to_datetime(df.iloc[:, 27], errors='coerce')
        df_final['Amount'] = pd.to_numeric(df.iloc[:, 36], errors='coerce')
        df_final['Status'] = df.iloc[:, 54].fillna('Pending')
        
        # Remove empty rows
        return df_final.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error: {e}")
        return None

df = load_data()

if df is not None:
    # --- METRICS ---
    st.sidebar.header("Filter Status")
    status_list = df['Status'].unique().tolist()
    selected = st.sidebar.multiselect("View:", status_list, default=status_list)
    df_f = df[df['Status'].isin(selected)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Value", f"${df_f['Amount'].sum():,.2f}")
    c2.metric("Total Orders", f"{len(df_f):,}")
    c3.metric("Avg Order", f"${df_f['Amount'].mean():,.2f}")

    st.divider()
    
    # --- CHARTS ---
    l, r = st.columns(2)
    with l:
        trend = df_f.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Date', y='Amount', title="Monthly Spending"), use_container_width=True)
    with r:
        top = df_f.groupby('Supplier')['Amount'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Amount', y='Supplier', orientation='h', title="Top 10 Suppliers"), use_container_width=True)

    st.subheader("Data List")
    st.dataframe(df_f.sort_values('Date', ascending=False), use_container_width=True)
