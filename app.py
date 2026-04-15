import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE SETUP ---
st.set_page_config(page_title="Purchasing Dashboard", layout="wide")
st.title("🛒 Purchasing Analysis Dashboard")

# --- DATA LOADING ---
@st.cache_data
def load_and_clean_data():
    # Attempt to find the file under any of these names
    possible_names = [
        "cleaned_purchasing_data.csv", 
        "Purchasing View - 29-01-2026.xlsx - Sheet - 1.csv"
    ]
    
    df = None
    for name in possible_names:
        try:
            # We use header=1 because your CSV has a title in the first row
            df = pd.read_csv(name, header=1)
            break
        except:
            continue
            
    if df is None:
        return None

    # Cleaning the data specifically for your file structure
    df.columns = [str(c).strip() for c in df.columns]
    
    # Selecting the core columns we need
    cols = ['Requester Name', 'PO_Number', 'Supplier', 'Date', 'PO Estimate Total', 'Approval Status', 'Added time']
    df = df[[c for c in cols if c in df.columns]].copy()

    # Convert numeric and date fields
    df['PO Estimate Total'] = pd.to_numeric(df['PO Estimate Total'], errors='coerce')
    df['Added time'] = pd.to_datetime(df['Added time'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Use 'Added time' if 'Date' is empty
    df['Clean Date'] = df['Date'].fillna(df['Added time'])
    
    # Drop rows without critical info
    df = df.dropna(subset=['PO Estimate Total', 'Clean Date'])
    return df

df = load_and_clean_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Results")
    status_list = df["Approval Status"].unique().tolist()
    status_filter = st.sidebar.multiselect("Select Status", options=status_list, default=status_list)
    
    df_filtered = df[df["Approval Status"].isin(status_filter)]

    # --- KPI METRICS ---
    total_spent = df_filtered["PO Estimate Total"].sum()
    po_count = len(df_filtered)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spending", f"${total_spent:,.2f}")
    c2.metric("Total Orders", f"{po_count:,}")
    c3.metric("Avg Order Value", f"${(total_spent/po_count) if po_count > 0 else 0:,.2f}")

    st.divider()

    # --- CHARTS ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Monthly Spending Trend")
        df_trend = df_filtered.set_index('Clean Date').resample('M')['PO Estimate Total'].sum().reset_index()
        fig_trend = px.line(df_trend, x='Clean Date', y='PO Estimate Total', markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.subheader("Top 10 Suppliers")
        top_sup = df_filtered.groupby("Supplier")["PO Estimate Total"].sum().nlargest(10).reset_index()
        fig_sup = px.bar(top_sup, x="PO Estimate Total", y="Supplier", orientation='h', color="PO Estimate Total")
        st.plotly_chart(fig_sup, use_container_width=True)

    # --- DATA TABLE ---
    st.subheader("Order Details")
    st.dataframe(df_filtered.sort_values("Clean Date", ascending=False), use_container_width=True)

else:
    st.error("⚠️ Data file not found! Please ensure your CSV file is uploaded to the main folder in GitHub.")
