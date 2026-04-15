import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

@st.cache_data
def load_and_clean_data():
    try:
        # 1. Read the file (trying without header offset first)
        df = pd.read_csv("cleaned_purchasing_data.csv")
        
        # 2. If 'PO_Number' isn't in the first row, it might be the second row
        if 'PO_Number' not in df.columns:
            df = pd.read_csv("cleaned_purchasing_data.csv", header=1)
        
        # 3. Clean all column names (remove hidden spaces/dots)
        df.columns = [str(c).strip().replace('.1', '') for c in df.columns]
        
        # 4. Define the mapping of what we need
        # We search for names that 'contain' these keywords to be safe
        def find_col(name_snippet):
            for col in df.columns:
                if name_snippet.lower() in col.lower():
                    return col
            return None

        col_map = {
            'amount': find_col('PO Estimate Total'),
            'status': find_col('Approval Status'),
            'date': find_col('Added time'),
            'supplier': find_col('Supplier'),
            'requester': find_col('Requester Name')
        }

        # Check if we found the vital columns
        if not col_map['amount'] or not col_map['date']:
            st.error(f"Could not find required columns. Available: {list(df.columns)[:10]}")
            return None

        # 5. Clean the data
        df['Amount'] = pd.to_numeric(df[col_map['amount']], errors='coerce')
        df['Date'] = pd.to_datetime(df[col_map['date']], errors='coerce')
        df['Status'] = df[col_map['status']].fillna('Unknown')
        df['Supplier'] = df[col_map['supplier']].fillna('No Supplier')
        
        return df.dropna(subset=['Amount', 'Date'])
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

df = load_and_clean_data()

if df is not None:
    # --- METRICS ---
    st.sidebar.header("Filter Results")
    status_filter = st.sidebar.multiselect("Select Status", options=df["Status"].unique(), default=df["Status"].unique())
    df_filtered = df[df["Status"].isin(status_filter)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${df_filtered['Amount'].sum():,.2f}")
    c2.metric("Total Orders", f"{len(df_filtered):,}")
    c3.metric("Avg Order", f"${df_filtered['Amount'].mean():,.2f}")

    # --- CHARTS ---
    st.divider()
    l, r = st.columns(2)
    
    with l:
        st.subheader("Monthly Trend")
        df_trend = df_filtered.set_index('Date').resample('M')['Amount'].sum().reset_index()
        st.plotly_chart(px.line(df_trend, x='Date', y='Amount'), use_container_width=True)

    with r:
        st.subheader("Top Suppliers")
        top_sup = df_filtered.groupby("Supplier")["Amount"].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_sup, x="Amount", y="Supplier", orientation='h'), use_container_width=True)

    st.subheader("Recent Activity")
    st.dataframe(df_filtered[['Date', 'PO_Number', 'Supplier', 'Amount', 'Status']].sort_values('Date', ascending=False))
