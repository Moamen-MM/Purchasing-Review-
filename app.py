import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

# 2. Load the Data (Ensure the CSV is in the same folder)
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_purchasing_data.csv")
    df['Clean Date'] = pd.to_datetime(df['Clean Date'])
    return df

try:
    df = load_data()

    # 3. Sidebar Filters
    st.sidebar.header("Filter Data")
    status_filter = st.sidebar.multiselect("Approval Status", options=df["Approval Status"].unique(), default=df["Approval Status"].unique())
    df_filtered = df[df["Approval Status"].isin(status_filter)]

    # 4. KPI Metrics
    total_spent = df_filtered["PO Estimate Total"].sum()
    po_count = len(df_filtered)
    avg_val = df_filtered["PO Estimate Total"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Spending", f"${total_spent:,.2f}")
    col2.metric("Total POs", f"{po_count:,}")
    col3.metric("Avg PO Value", f"${avg_val:,.2f}")

    st.divider()

    # 5. Visualizations
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Spending Over Time")
        # Aggregating by month
        df_trend = df_filtered.resample('M', on='Clean Date').sum().reset_index()
        fig_trend = px.line(df_trend, x='Clean Date', y='PO Estimate Total', markers=True, template="plotly_white")
        st.plotly_chart(fig_trend, use_container_width=True)

    with right_col:
        st.subheader("Top 10 Suppliers")
        top_suppliers = df_filtered.groupby("Supplier")["PO Estimate Total"].sum().nlargest(10).reset_index()
        fig_sup = px.bar(top_suppliers, x="PO Estimate Total", y="Supplier", orientation='h', color="PO Estimate Total")
        st.plotly_chart(fig_sup, use_container_width=True)

    # 6. Data Table
    st.subheader("Raw Data Preview")
    st.dataframe(df_filtered, use_container_width=True)

except FileNotFoundError:
    st.error("Please ensure 'cleaned_purchasing_data.csv' is in the same directory as this code.")
