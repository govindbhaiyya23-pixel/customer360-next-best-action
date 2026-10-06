# Customer 360 and Next Best Action Engine

A lightweight Streamlit dashboard that brings synthetic customer profiles, transaction patterns, explainable health scores, and practical next-best-action recommendations into one place.
🔗 Live Demo:** https://customer-360-next-best-action--govindbhaiyya23.replit.app/customer360/

## Problem

Customer data is spread across products, channels and support systems. Teams can't see the full picture, so they miss customers who are about to churn and customers who are ready for another product.

## Solution

One dashboard that unifies customer data, scores each customer's health, and recommends the top three explainable actions with the reason, priority and best channel.

> All included records are generated demo data. Scores and suggestions are directional examples, not financial advice or production decisions.

## Features

- **Overview dashboard:** portfolio KPIs, customer segment mix, churn-risk distribution, category spend, and a selected customer's monthly transaction trend.
- **Customer 360:** searchable customer profiles, segment/city filters, product holdings, spend mix, and engagement, churn-risk, and value indicators.
- **Next Best Action:** up to three ranked rule-based recommendations with the reason, priority, preferred channel, and expected impact.
- **Action Queue:** sortable top recommendation for every customer with a CSV download.
- **About:** concise explanations of the scoring inputs and recommendation rules.
- **Synthetic dataset:** 500 customers and 3,000 transactions generated deterministically for a repeatable demo.

## Run locally

```bash
python -m pip install -r requirements.txt
python generate_data.py
streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

The dashboard loads `data/customers.csv` and `data/transactions.csv`. If either file is missing, it generates both automatically on startup.

## Architecture

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit UI, filters, pages, charts, and cached data loading |
| `generate_data.py` | Reproducible synthetic customer and transaction CSV generation |
| `scoring.py` | Explainable engagement, churn-risk, and value scoring |
| `nba_engine.py` | Rule-based next-best-action evaluation and ranking |
| `data/` | Generated CSV data used by the demo |
| `.streamlit/config.toml` | Headless server and visual theme settings |

## Scoring and recommendations

The churn score combines login recency, transaction recency, satisfaction, recent support tickets, and credit utilization. Engagement combines activity recency, satisfaction, and support load. Value tier is a simple proxy based on monthly spend and average balance. Rule triggers are implemented in `nba_engine.py`; each recommendation includes an explanation and uses the customer's preferred channel.
## Business Impact

- **Earlier churn detection:** flags at-risk customers using login recency, satisfaction, support tickets and credit utilization
- **Targeted cross-sell:** surfaces product opportunities for customers with high balances or a single product
- **Prioritised outreach:** the Action Queue ranks customers so teams contact the right people first
- **Explainable by design:** every recommendation shows why it was made, so teams can trust and audit it

## Future Scope

- ML-based churn and propensity models
- What-if simulator for scenario testing
- Live CRM and transaction data integration
- Expected revenue impact per action
- 
## Screenshots

_Screenshots placeholder — add dashboard captures here._
