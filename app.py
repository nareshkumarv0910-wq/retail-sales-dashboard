import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Retail Sales Dashboard", page_icon="📈", layout="wide")

# ------------------ HEADER ------------------
st.title("Retail Sales Dashboard")
st.markdown("""
**Built by Naresh Kumar**  
📍 Chennai, India  
📞 +91 80729 25243  
🔗 [LinkedIn](https://www.linkedin.com/in/naresh-kumar-b67b0b326) | [GitHub](https://github.com/nareshkumar0910-wq)
""")

# ------------------ DATA GENERATION ------------------
@st.cache_data
def load_data(n_rows=2500, seed=91):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    regions = ["North", "South", "East", "West"]
    categories = ["Furniture", "Technology", "Office Supplies"]
    products = [f"Product {chr(65+i)}" for i in range(12)]

    df = pd.DataFrame({
        "OrderDate": rng.choice(dates, size=n_rows),
        "Region": rng.choice(regions, size=n_rows),
        "Category": rng.choice(categories, size=n_rows),
        "Product": rng.choice(products, size=n_rows),
        "Quantity": rng.integers(1, 5, size=n_rows),
        "Discount": np.round(rng.uniform(0, 0.4, size=n_rows), 2)
    })

    base_sales = rng.gamma(2.2, 120, size=n_rows)
    df["Sales"] = np.round(base_sales * (1 - df["Discount"]) + df["Quantity"] * 20, 2)
    margin = 0.25 - df["Discount"] * 0.5
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

regions = st.sidebar.multiselect("Region", sorted(data["Region"].unique()), default=sorted(data["Region"].unique()))
categories = st.sidebar.multiselect("Category", sorted(data["Category"].unique()), default=sorted(data["Category"].unique()))

if isinstance(date_range, (date, pd.Timestamp)):
    date_start, date_end = min_d, max_d
else:
    date_start, date_end = date_range

df = data[
    (data["OrderDate"] >= pd.to_datetime(date_start)) &
    (data["OrderDate"] <= pd.to_datetime(date_end)) &
    (data["Region"].isin(regions)) &
    (data["Category"].isin(categories))
].copy()

if df.empty:
    st.warning("No data for the selected filters. Expand your date range or selections.")
    st.stop()

# ------------------ KPIs ------------------
total_profit = float(df["Profit"].sum())
avg_discount = df["Discount"].mean()
top_product = df.groupby("Product")["Profit"].sum().idxmax()
neg_profit_count = (df["Profit"] < 0).sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("💸 Total Profit", f"₹{total_profit:,.0f}")
k2.metric("🔻 Avg Discount", f"{avg_discount:.1%}")
k3.metric("🏆 Top Product", top_product)
k4.metric("⚠️ Negative Profit Orders", f"{neg_profit_count:,}")

# ------------------ CHARTS ------------------
st.markdown("---")

st.subheader("Profit vs Discount")
fig_scatter = px.scatter(df, x="Discount", y="Profit", color="Category", hover_data=["Product"])
st.plotly_chart(fig_scatter, use_container_width=True)

st.subheader("Top 10 Products by Profit")
top10 = df.groupby("Product", as_index=False)["Profit"].sum().nlargest(10, "Profit")
fig_bar = px.bar(top10, x="Product", y="Profit", color="Product", text_auto=".2s")
fig_bar.update_layout(showlegend=False)
st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Region-wise Profit Heatmap")
region_profit = df.groupby("Region", as_index=False)["Profit"].sum()
fig_heat = px.bar(region_profit, x="Region", y="Profit", color="Region", text_auto=".2s")
fig_heat.update_layout(showlegend=False)
st.plotly_chart(fig_heat, use_container_width=True)

st.subheader("Discount Impact Over Time")
monthly = df.groupby("Month", as_index=False).agg({"Sales": "sum", "Discount": "mean"})
fig_line = px.line(monthly, x="Month", y="Discount", markers=True)
fig_line.update_traces(line_color="orange")
st.plotly_chart(fig_line, use_container_width=True)
