from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from nba_engine import get_next_best_actions
from scoring import score_customer


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CUSTOMER_FILE = DATA_DIR / "customers.csv"
TRANSACTION_FILE = DATA_DIR / "transactions.csv"

COLORS = {
    "ink": "#152238",
    "muted": "#6b7890",
    "blue": "#4169e1",
    "teal": "#12a594",
    "orange": "#f4a340",
    "red": "#e15b64",
    "purple": "#8064d8",
}


st.set_page_config(
    page_title="Customer 360 · Next Best Action",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { --ink:#152238; --muted:#6b7890; --line:#e8edf4; --paper:#ffffff; }
      .stApp { background: #f5f7fb; color: var(--ink); }
      [data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
      .block-container { padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1480px; }
      h1, h2, h3 { letter-spacing: -0.025em; }
      .eyebrow { color:#4169e1; text-transform:uppercase; letter-spacing:.12em;
                 font-weight:800; font-size:.72rem; margin-bottom:.25rem; }
      .hero { padding: 1.35rem 1.6rem; background:linear-gradient(120deg,#182944,#304d78);
              border-radius:20px; color:white; margin-bottom:1rem; }
      .hero h1 { color:white; margin:0; font-size:2rem; }
      .hero p { color:#d8e3f6; margin:.4rem 0 0; }
      .metric-card, .profile-card, .action-card, .info-card {
        background:var(--paper); border:1px solid var(--line); border-radius:16px;
        padding:1rem 1.1rem; box-shadow:0 5px 18px rgba(28,48,79,.035);
      }
      .metric-label { color:var(--muted); font-size:.82rem; font-weight:600; }
      .metric-value { color:var(--ink); font-size:1.65rem; font-weight:800; margin-top:.2rem; }
      .metric-note { color:var(--muted); font-size:.76rem; margin-top:.15rem; }
      .profile-name { font-size:1.45rem; font-weight:800; color:var(--ink); }
      .profile-meta { color:var(--muted); margin:.25rem 0 .8rem; }
      .pill { display:inline-block; border-radius:999px; padding:.25rem .65rem; font-size:.75rem;
              font-weight:700; background:#edf2ff; color:#3558c9; margin:.1rem .2rem .1rem 0; }
      .action-top { display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; }
      .action-title { color:var(--ink); font-size:1.02rem; font-weight:800; }
      .action-copy { color:var(--muted); font-size:.88rem; margin:.55rem 0; line-height:1.5; }
      .priority { border-radius:999px; padding:.28rem .65rem; font-size:.75rem; font-weight:800;
                  white-space:nowrap; background:#fff2dc; color:#996116; }
      .priority.high { background:#ffe9e9; color:#ad333c; }
      .priority.low { background:#e8f7f2; color:#13775e; }
      .section-note { color:var(--muted); font-size:.88rem; margin-top:-.5rem; }
      div[data-testid="stMetric"] { background:white; border:1px solid var(--line);
                                    padding:1rem 1.1rem; border-radius:16px; }
      div[data-testid="stMetricLabel"] { color:var(--muted); }
      .stTabs [data-baseweb="tab-list"] { gap:.35rem; }
      .stTabs [data-baseweb="tab"] { border-radius:10px 10px 0 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the generated CSVs and normalize the fields used in the dashboard."""
    if not CUSTOMER_FILE.exists() or not TRANSACTION_FILE.exists():
        from generate_data import generate_all

        generate_all()

    customers = pd.read_csv(CUSTOMER_FILE)
    transactions = pd.read_csv(TRANSACTION_FILE, parse_dates=["date"])
    customers["customer_id"] = customers["customer_id"].fillna("").astype(str)
    customers["name"] = customers["name"].fillna("Unknown customer").astype(str)
    transactions["customer_id"] = transactions["customer_id"].fillna("").astype(str)
    transactions["amount"] = pd.to_numeric(transactions["amount"], errors="coerce").fillna(0)
    return customers, transactions


def money(value: float) -> str:
    return f"₹{value:,.0f}"


def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-note">{note or "&nbsp;"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(fig: go.Figure, height: int = 330) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["muted"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e8edf4")
    fig.update_yaxes(gridcolor="#edf1f6", zeroline=False)
    return fig


def render_profile(customer: pd.Series) -> None:
    product_list = [p.strip() for p in str(customer.get("products_held", "")).split(";") if p.strip()]
    pills = "".join(f'<span class="pill">{product}</span>' for product in product_list) or (
        '<span class="pill">No products listed</span>'
    )
    st.markdown(
        f"""
        <div class="profile-card">
          <div class="eyebrow">Customer profile</div>
          <div class="profile-name">👤 {customer.get("name", "Unknown customer")}</div>
          <div class="profile-meta">{customer.get("customer_id", "—")} · {customer.get("city", "—")} · {customer.get("segment", "—")} segment</div>
          {pills}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_card(action: dict) -> None:
    priority = int(action.get("priority", 0))
    badge_class = "high" if priority >= 75 else ("low" if priority < 45 else "")
    st.markdown(
        f"""
        <div class="action-card">
          <div class="action-top">
            <div class="action-title">✨ {action.get("action", "Personalized check-in")}</div>
            <div class="priority {badge_class}">Priority {priority}</div>
          </div>
          <div class="action-copy"><b>Why this?</b> {action.get("reason", "A personalized customer check-in may be useful.")}</div>
          <div><span class="pill">📣 {action.get("channel", "App")}</span>
          <span class="pill">📈 {action.get("expected_impact", "Strengthen engagement")}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def customer_score_frame(customers: pd.DataFrame) -> pd.DataFrame:
    scores = customers.apply(score_customer, axis=1, result_type="expand")
    return pd.concat([customers.reset_index(drop=True), scores.reset_index(drop=True)], axis=1)


customers, transactions = load_data()
if customers.empty:
    st.error("No customer records found. Run `python generate_data.py` to create the demo data.")
    st.stop()

scored = customer_score_frame(customers)

st.sidebar.markdown("## 🧭 Customer 360")
st.sidebar.caption("Explore customer health and recommended actions.")
segments = ["All segments"] + sorted(customers["segment"].dropna().astype(str).unique().tolist())
cities = ["All cities"] + sorted(customers["city"].dropna().astype(str).unique().tolist())
selected_segment = st.sidebar.selectbox("Segment", segments)
selected_city = st.sidebar.selectbox("City", cities)

filtered = customers.copy()
if selected_segment != "All segments":
    filtered = filtered[filtered["segment"].astype(str) == selected_segment]
if selected_city != "All cities":
    filtered = filtered[filtered["city"].astype(str) == selected_city]

if filtered.empty:
    st.sidebar.warning("No customers match these filters.")
    filtered = customers

customer_options = filtered.sort_values("name").to_dict("records")
customer_by_key = {
    f'{item["name"]} · {item["customer_id"]}': item["customer_id"] for item in customer_options
}
search = st.sidebar.text_input("Find by name or customer ID", placeholder="e.g. Aanya or CUST-0102")
if search.strip():
    query = search.strip().casefold()
    matching = [
        key for key, customer_id in customer_by_key.items()
        if query in key.casefold() or query in customer_id.casefold()
    ]
    if matching:
        customer_by_key = {key: customer_by_key[key] for key in matching}
    else:
        st.sidebar.caption("No match; showing filtered customers.")

selected_label = st.sidebar.selectbox("Selected customer", list(customer_by_key.keys()))
selected_id = customer_by_key[selected_label]
selected_customer = customers.loc[customers["customer_id"] == selected_id].iloc[0]
selected_transactions = transactions[transactions["customer_id"] == selected_id].copy()
selected_score = score_customer(selected_customer)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow" style="color:#a9c2ff">Customer intelligence workspace</div>
      <h1>Customer 360 &amp; Next Best Action</h1>
      <p>A clear view of customer health, value, and the next action worth taking.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

overview_tab, customer_tab, nba_tab, queue_tab, about_tab = st.tabs(
    ["📊 Overview", "👤 Customer 360", "✨ Next Best Action", "📥 Action Queue", "ℹ️ About"]
)

with overview_tab:
    st.subheader("Portfolio overview")
    st.markdown('<div class="section-note">A quick read on the current customer base.</div>', unsafe_allow_html=True)
    average_satisfaction = pd.to_numeric(customers["satisfaction_score"], errors="coerce").mean()
    average_spend = pd.to_numeric(customers["monthly_spend"], errors="coerce").mean()
    high_risk_pct = float((scored["churn_risk_level"] == "High").mean() * 100)
    kpis = st.columns(4)
    with kpis[0]:
        metric_card("Total customers", f"{len(customers):,}", "Across all segments")
    with kpis[1]:
        metric_card("Avg. satisfaction", f"{average_satisfaction:.1f} / 10", "Customer-reported score")
    with kpis[2]:
        metric_card("High churn risk", f"{high_risk_pct:.1f}%", "Based on explainable signals")
    with kpis[3]:
        metric_card("Avg. monthly spend", money(average_spend), "Per customer")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Segment distribution")
        segment_counts = customers["segment"].value_counts().rename_axis("Segment").reset_index(name="Customers")
        fig = px.pie(
            segment_counts, names="Segment", values="Customers", hole=0.68,
            color_discrete_sequence=[COLORS["blue"], COLORS["teal"], COLORS["orange"]],
        )
        fig.update_traces(textposition="outside", textinfo="label+percent")
        st.plotly_chart(chart_layout(fig, 340), use_container_width=True)
    with right:
        st.markdown("#### Churn-risk distribution")
        risk_counts = scored["churn_risk_level"].value_counts().reindex(
            ["Low", "Medium", "High"], fill_value=0
        ).rename_axis("Risk").reset_index(name="Customers")
        fig = px.bar(
            risk_counts, x="Risk", y="Customers", color="Risk", text="Customers",
            color_discrete_map={"Low": COLORS["teal"], "Medium": COLORS["orange"], "High": COLORS["red"]},
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(chart_layout(fig, 340), use_container_width=True)

    spend_col, trend_col = st.columns(2)
    with spend_col:
        st.markdown("#### Spend by category")
        if transactions.empty:
            st.info("No transaction data is available yet.")
        else:
            category_spend = transactions.groupby("category", as_index=False)["amount"].sum().sort_values("amount")
            fig = px.bar(category_spend, x="amount", y="category", orientation="h", text_auto=",.0f",
                         color_discrete_sequence=[COLORS["purple"]])
            fig.update_layout(xaxis_title="Transaction amount (₹)", yaxis_title="")
            st.plotly_chart(chart_layout(fig, 340), use_container_width=True)
    with trend_col:
        st.markdown(f"#### Monthly transaction trend · {selected_customer['name']}")
        if selected_transactions.empty:
            st.info("No transactions are available for this customer.")
        else:
            trend = (
                selected_transactions.assign(month=selected_transactions["date"].dt.to_period("M").dt.to_timestamp())
                .groupby("month", as_index=False)["amount"].sum()
            )
            fig = px.line(trend, x="month", y="amount", markers=True, color_discrete_sequence=[COLORS["blue"]])
            fig.update_layout(xaxis_title="", yaxis_title="Transaction amount (₹)")
            fig.update_traces(line_width=3)
            st.plotly_chart(chart_layout(fig, 340), use_container_width=True)

with customer_tab:
    st.subheader("Customer 360 view")
    render_profile(selected_customer)
    details = st.columns(4)
    with details[0]:
        metric_card("Tenure", f'{int(selected_customer.get("tenure_months", 0))} mo', "Relationship length")
    with details[1]:
        metric_card("Average balance", money(float(selected_customer.get("avg_balance", 0))), "Current account value")
    with details[2]:
        metric_card("Monthly spend", money(float(selected_customer.get("monthly_spend", 0))), "Estimated monthly spend")
    with details[3]:
        metric_card("Satisfaction", f'{int(selected_customer.get("satisfaction_score", 0))} / 10', "Latest customer score")

    st.markdown("#### Health indicators")
    health = st.columns(3)
    health[0].metric("Engagement score", f'{selected_score["engagement_score"]} / 100')
    health[1].metric("Churn risk", selected_score["churn_risk_level"], f'{selected_score["churn_risk_score"]} / 100')
    health[2].metric("Value tier", selected_score["value_tier"], "Estimated from spend and balance")

    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("#### Spend mix")
        if selected_transactions.empty:
            st.info("No transaction data for this customer.")
        else:
            mix = selected_transactions.groupby("category", as_index=False)["amount"].sum()
            fig = px.pie(mix, names="category", values="amount", hole=.58,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition="inside", textinfo="label+percent")
            st.plotly_chart(chart_layout(fig, 330), use_container_width=True)
    with chart2:
        st.markdown("#### Customer signals")
        signal_data = pd.DataFrame(
            {
                "Signal": ["Engagement", "Satisfaction", "Value", "Low risk"],
                "Score": [
                    selected_score["engagement_score"],
                    int(selected_customer.get("satisfaction_score", 0)) * 10,
                    selected_score["value_score"],
                    100 - selected_score["churn_risk_score"],
                ],
            }
        )
        fig = px.bar(signal_data, x="Score", y="Signal", orientation="h", range_x=[0, 100],
                     color="Signal", color_discrete_sequence=[COLORS["blue"], COLORS["teal"], COLORS["orange"], COLORS["purple"]])
        fig.update_layout(showlegend=False, xaxis_title="Score out of 100", yaxis_title="")
        st.plotly_chart(chart_layout(fig, 330), use_container_width=True)

with nba_tab:
    st.subheader("Next best actions")
    st.markdown(
        f'<div class="section-note">Recommended next steps for <b>{selected_customer["name"]}</b>, ranked by priority.</div>',
        unsafe_allow_html=True,
    )
    action_list = get_next_best_actions(selected_customer, selected_score)
    for action in action_list[:3]:
        render_action_card(action)
        st.write("")

with queue_tab:
    st.subheader("Action queue")
    st.markdown(
        '<div class="section-note">One highest-priority recommendation per customer. Sort columns to triage the work.</div>',
        unsafe_allow_html=True,
    )
    queue_rows = []
    for _, customer in customers.iterrows():
        score = score_customer(customer)
        top_action = get_next_best_actions(customer, score)[0]
        queue_rows.append(
            {
                "Customer ID": customer["customer_id"],
                "Name": customer["name"],
                "Segment": customer["segment"],
                "City": customer["city"],
                "Risk": score["churn_risk_level"],
                "Risk score": score["churn_risk_score"],
                "Top action": top_action["action"],
                "Priority": top_action["priority"],
                "Channel": top_action["channel"],
                "Expected impact": top_action["expected_impact"],
            }
        )
    queue = pd.DataFrame(queue_rows).sort_values(["Priority", "Risk score"], ascending=False)
    st.download_button(
        "⬇️ Download action queue CSV",
        data=queue.to_csv(index=False).encode("utf-8"),
        file_name="customer_action_queue.csv",
        mime="text/csv",
        use_container_width=False,
    )
    st.dataframe(queue, use_container_width=True, hide_index=True, height=540)

with about_tab:
    st.subheader("About this dashboard")
    st.markdown(
        """
        <div class="info-card">
          <h3>Simple, explainable customer intelligence</h3>
          <p>This demo combines a synthetic customer profile and transaction history to surface
          health indicators and practical follow-up actions. It does not use a heavy ML model.</p>
          <h4>How the scores work</h4>
          <ul>
            <li><b>Engagement</b> blends recent logins, recent transactions, satisfaction, and support load.</li>
            <li><b>Churn risk</b> increases with inactivity, lower satisfaction, more support tickets, and high credit utilization.</li>
            <li><b>Value tier</b> uses monthly spend and average balance as a lightweight customer value proxy.</li>
          </ul>
          <h4>How actions are picked</h4>
          <p>Transparent rules inspect risk, product holdings, balance, credit utilization, login recency,
          support tickets, tenure, and segment. The top three actions show why they were recommended
          and use the customer's preferred channel.</p>
          <p>All records are synthetic demo data. Scores and recommendations are directional examples,
          not financial advice or production decisions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption("Synthetic demo data · Rules are transparent and designed for exploration.")
