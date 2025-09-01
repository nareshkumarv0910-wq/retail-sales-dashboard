# ------------------ SETUP ------------------
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Retail Sales Dashboard", page_icon="📊", layout="wide")

# ------------------ BACKGROUND IMAGE ------------------
st.markdown("""
    <style>
        .main {
            background-image: url("https://images.unsplash.com/photo-1612832021046-0c5f7e3e5f4e?auto=format&fit=crop&w=1920&q=80");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }

        .block-container {
            background-color: rgba(10, 15, 28, 0.85);
            padding: 2rem;
            border-radius: 12px;
        }
    </style>
""", unsafe_allow_html=True)


# ------------------ HEADER ------------------
st.markdown("""
    <style>
        .custom-header {
            text-align: center;
            font-size: 32px;
            font-weight: 700;
            color: #93c5fd;
            margin-bottom: 20px;
        }
    </style>
    <div class="custom-header">Naresh Kumar — Retail Insights Dashboard</div>
""", unsafe_allow_html=True)

# ------------------ EMBEDDED IMAGE ------------------
st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <img src='https://images.unsplash.com/photo-1612832021046-0c5f7e3e5f4e?auto=format&fit=crop&w=1920&q=80'
             width='850'
             style='border-radius:12px; box-shadow:0 0 12px #60a5fa;'/>
        <div style='font-size:14px; color:#94a3b8; margin-top:8px;'>Retail Intelligence • Powered by Naresh Kumar</div>
    </div>
""", unsafe_allow_html=True)

# ------------------ DATA ------------------
@st.cache_data
def load_data(n_rows=2500, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    regions = ["North", "South", "East", "West"]
    segments = ["Consumer", "Corporate", "Home Office"]
    products = ["Alpha", "Bravo", "Cobalt", "Delta", "Echo"]

    df = pd.DataFrame({
        "OrderDate": rng.choice(dates, size=n_rows),
        "Region": rng.choice(regions, size=n_rows),
        "Segment": rng.choice(segments, size=n_rows),
        "Product": rng.choice(products, size=n_rows),
        "Quantity": rng.integers(1, 6, size=n_rows),
        "Discount": np.round(rng.uniform(0, 0.3, size=n_rows), 2)
    })

    base = rng.gamma(shape=2.2, scale=120, size=n_rows)
    df["Sales"] = np.round(base * (1 - df["Discount"]) + df["Quantity"] * 20, 2)
    margin = 0.22 - (df["Discount"] * 0.45)
    noise = rng.normal(0, 8, size=n_rows)
    df["Profit"] = np.round(df["Sales"] * margin + noise, 2)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["Month"] = df["OrderDate"].dt.to_period("M").dt.to_timestamp()
    return df

data = load_data()

# ------------------ FILTERS ------------------
st.sidebar.header("🔍 Filters")
min_d, max_d = data["OrderDate"].min().date(), data["OrderDate"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)

regions = st.sidebar.multiselect("Region", sorted(data["Region"].unique()), default=sorted(data["Region"].unique()))
segments = st.sidebar.multiselect("Segment", sorted(data["Segment"].unique()), default=sorted(data["Segment"].unique()))

if isinstance(date_range, (date, pd.Timestamp)):
    date_start, date_end = min_d, max_d
else:
    date_start, date_end = date_range

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
orders = len(df)
aov = total_sales / orders if orders else 0.0
monthly = df.groupby("Month", as_index=False)["Sales"].sum().sort_values("Month")
mom = (monthly["Sales"].iloc[-1] - monthly["Sales"].iloc[-2]) / monthly["Sales"].iloc[-2] if len(monthly) >= 2 else np.nan

purchases = max(orders, 1)
leads = int(purchases * 3.5)
visitors = int(leads * 3.0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Total Sales", f"₹{total_sales:,.0f}")
k2.metric("📦 Orders", f"{orders:,}")
k3.metric("🧾 Avg Order Value", f"₹{aov:,.0f}")
k4.metric("📈 MoM Growth", "—" if np.isnan(mom) else f"{mom:.1%}")

# ------------------ DOWNLOAD ------------------
st.download_button(
    label="📥 Download Filtered Data",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales.csv",
    mime="text/csv"
)

st.markdown("---")

# ------------------ CHARTS ------------------
c1, c2 = st.columns((2, 1))

with c1:
    st.markdown("### 📈 Sales Trend")
    fig_trend = px.line(monthly, x="Month", y="Sales", markers=True)
    fig_trend.update_traces(line=dict(width=3))
    st.plotly_chart(fig_trend, use_container_width=True)

with c2:
    st.markdown("### 🧩 Segment Share")
    seg = df.groupby("Segment", as_index=False)["Sales"].sum()
    fig_seg = px.pie(seg, names="Segment", values="Sales")
    st.plotly_chart(fig_seg, use_container_width=True)

st.markdown("### 🗺️ Sales by Region")
reg = df.groupby("Region", as_index=False)["Sales"].sum()
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
prod = df.groupby("Product", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False).head(10)
fig_prod = px.bar(prod, x="Product", y="Sales", text_auto=".2s")
fig_prod.update_layout(showlegend=False)
st.plotly_chart(fig_prod, use_container_width=True)

# ------------------ FOOTER ------------------
st.markdown("""
    <style>
        .footer-container {
            text-align: center;
            padding-top: 40px;
            padding-bottom: 20px;
            font-family: 'Segoe UI', sans-serif;
            color: #cbd5e1;
        }

        .footer-name {
            font-size: 20px;
            font-weight: 600;
            color: #60a5fa;
        }

        .footer-links a {
            margin: 0 12px;
            text-decoration: none;
            font-size: 16px;
            color: #93c5fd;
            transition: all 0.3s ease;
        }

        .footer-links a:hover {
            color: #bfdbfe;
            text-shadow: 0 0 6px #bfdbfe;
        }

        .footer-line {
            height: 2px;
            background: linear-gradient(to right, #60a5fa, #93c5fd);
            margin: 30px auto 20px;
            width: 60%;
            border-radius: 4px;
        }

        .footer-badge {
            font-size: 13px;
            color: #94a3b8;
            margin-top: 10px;
        }
    </style>

    <div class="footer-container">
        <div class="footer-line"></div>
        <div class="footer-name">Naresh Kumar — Data Analyst</div>
        <div class="footer-links">
            📞 +91 80729 25243 |
            <a href='https://www.linkedin.com/in/naresh-kumar-b67b0b326' target='_blank'>LinkedIn</a> |
            <a href='https://github.com/nareshkumarv0910-wq' target='_blank'>GitHub</a>
        </div>
        <div class="footer-badge">Built using Streamlit, Plotly & Python • Chennai, India</div>
    </div>
""", unsafe_allow_html=True)
