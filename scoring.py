"""Lightweight, explainable customer health and value scoring."""

from __future__ import annotations

import math
from typing import Any


def _number(customer: Any, field: str, default: float = 0.0) -> float:
    try:
        value = customer.get(field, default)
        if value is None:
            return default
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError, AttributeError):
        return default


def _clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(round(max(low, min(high, value))))


def score_customer(customer: Any) -> dict[str, Any]:
    """Return engagement, churn-risk, and value scores from customer-level signals."""
    login_days = max(0, _number(customer, "last_login_days_ago"))
    transaction_days = max(0, _number(customer, "last_transaction_days_ago"))
    tickets = max(0, _number(customer, "support_tickets_last_90d"))
    satisfaction = max(1, min(10, _number(customer, "satisfaction_score", 5)))
    utilization = max(0, min(100, _number(customer, "credit_utilization")))
    monthly_spend = max(0, _number(customer, "monthly_spend"))
    balance = max(0, _number(customer, "avg_balance"))

    # Each factor is bounded so an extreme input cannot overwhelm the score.
    risk = (
        min(login_days, 120) * 0.25
        + min(transaction_days, 120) * 0.20
        + (10 - satisfaction) * 3.8
        + min(tickets, 8) * 4.5
        + max(0, utilization - 50) * 0.30
    )
    churn_score = _clamp(risk)
    churn_level = "High" if churn_score >= 62 else ("Medium" if churn_score >= 35 else "Low")

    engagement = _clamp(
        100
        - min(login_days, 120) * 0.35
        - min(transaction_days, 120) * 0.22
        - min(tickets, 8) * 3
        + satisfaction * 2.2
    )
    value_score = _clamp(
        min(monthly_spend / 1000, 60)
        + min(balance / 5000, 40)
    )
    value_tier = "Gold" if value_score >= 68 else ("Silver" if value_score >= 34 else "Bronze")

    return {
        "engagement_score": engagement,
        "churn_risk_score": churn_score,
        "churn_risk_level": churn_level,
        "value_score": value_score,
        "value_tier": value_tier,
    }
