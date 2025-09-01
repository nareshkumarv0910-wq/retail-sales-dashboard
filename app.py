
# ------------------ SETUP ------------------
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Retail Sales Dashboard", page_icon="📊", layout="wide")
st.title("📊 Retail Sales Dashboard")

# ------------------ DATA ------------------
@st.cache_data
def load_data(n_rows: int = 2500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    regions = ["North", "South", "East", "West"]
    segments = ["Consumer", "Corporate", "Home Office"]

    df = pd.DataFrame({
        "OrderDate": rng.choice(dates, size=n_rows),
        "Region": rng.choice(regions, size=n_rows, p=[0.28, 0.24, 0.24, 0.24]),
        "Segment": rng.choice(segments, size=n_rows, p=[0.6, 0.25, 0.15]),
        "Product": rng.choice(["Alpha", "Bravo", "Cobalt", "Delta", "Echo"], size=n_rows),
        "Quantity": rng.integers(1, 6, size=n_rows),
        "Discount": np.round(rng.uniform(0, 0.3, size=n_rows), 2)
    })

    base = rng.gamma(shape=2.2, scale=120, size=n_rows)  # realistic spread
    df["Sales"] = np.round(base * (1 - df["Discount"]) + df["Quantity"] * 20, 2)
    margin = 0.22 - (df["Discount"] * 0.45)
    noise = rng.normal(0, 8, size=n_rows)
    df["Profit"] = np.round(df["Sales"] * margin + noise, 2)

    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["Month"] = df["OrderDate"].dt.to_period("M").dt.to_timestamp()
    return df

data = load_data()

# ------------------ SIDEBAR FILTERS ------------------
st.sidebar.header("Filters")

min_d, max_d = data["OrderDate"].min().date(), data["OrderDate"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)

regions = st.sidebar.multiselect(
    "Region",
    options=sorted(data["Region"].unique().tolist()),
    default=sorted(data["Region"].unique().tolist())
)

segments = st.sidebar.multiselect(
    "Segment",
    options=sorted(data["Segment"].unique().tolist()),
    default=sorted(data["Segment"].unique().tolist())
)

# Safety for single date selection
if isinstance(date_range, (date, pd.Timestamp)):
    date_start, date_end = min_d, max_d
else:
    date_start, date_end = date_range

# ------------------ FILTERING ------------------
df = data[
    (data["OrderDate"] >= pd.to_datetime(date_start)) &
    (data["OrderDate"] <= pd.to_datetime(date_end)) &
    (data["Region"].isin(regions)) &
    (data["Segment"].isin(segments))
].copy()

if df.empty:
    st.warning("No data for the selected filters. Try expanding your date range or selections.")
    st.stop()

# ------------------ KPIs ------------------
total_sales = float(df["Sales"].sum())
orders = int(len(df))
aov = float(total_sales / orders) if orders else 0.0

monthly = df.groupby("Month", as_index=False)["Sales"].sum().sort_values("Month")
if len(monthly) >= 2:
    mom = (monthly["Sales"].iloc[-1] - monthly["Sales"].iloc[-2]) / monthly["Sales"].iloc[-2]
else:
    mom = np.nan

# Simple funnel derived from orders for demo
purchases = max(orders, 1)
leads = int(purchases * 3.5)
visitors = int(leads * 3.0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sales", f"₹{total_sales:,.0f}")
k2.metric("Orders", f"{orders:,}")
k3.metric("Avg Order Value", f"₹{aov:,.0f}")
k4.metric("MoM Growth", "—" if np.isnan(mom) else f"{mom:.1%}")

st.markdown("---")

# ------------------ CHARTS ------------------
c1, c2 = st.columns((2, 1))

with c1:
    st.markdown("### 📈 Sales Trend")
    fig_trend = px.line(monthly, x="Month", y="Sales", markers=True,
                        labels={"Sales": "Sales (₹)"},
                        title=None)
    fig_trend.update_traces(line=dict(width=3))
    st.plotly_chart(fig_trend, use_container_width=True)

with c2:
    st.markdown("### 🧩 Segment Share")
    seg = df.groupby("Segment", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
    fig_seg = px.pie(seg, names="Segment", values="Sales")
    st.plotly_chart(fig_seg, use_container_width=True)

st.markdown("### 🗺️ Sales by Region")
reg = df.groupby("Region", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
fig_reg = px.bar(reg, x="Region", y="Sales", color="Region", text_auto=".2s")
fig_reg.update_layout(showlegend=False)
st.plotly_chart(fig_reg, use_container_width=True)

st.markdown("### 🔁 Conversion Funnel")
funnel_df = pd.DataFrame({
    "Stage": ["Visitors", "Leads", "Purchases"],
    "Count": [visitors, leads, purchases]
})
fig_fun = px.funnel(funnel_df, x="Count", y="Stage")
st.plotly_chart(fig_fun, use_container_width=True)

st.markdown("### 🏷️ Top Products by Sales")
prod = (df.groupby("Product", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(10))
fig_prod = px.bar(prod, x="Product", y="Sales", text_auto=".2s")
fig_prod.update_layout(showlegend=False)
st.plotly_chart(fig_prod, use_container_width=True)

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center; font-size:13px; color:#888;'>
        Built by <strong>Naresh Kumar</strong> • Data Analyst • Chennai, India<br>
        <a href='https://www.linkedin.com/in/naresh-kumar-b67b0b326' target='_blank'>LinkedIn</a> |
        <a href='https://github.com/nareshkumarv0910-wq' target='_blank'>GitHub</a>
    </div>
    """,
    unsafe_allow_html=True
)
