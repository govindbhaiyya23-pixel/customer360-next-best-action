"""Rule-based next-best-action recommendations."""

from __future__ import annotations

import math
from typing import Any

from scoring import score_customer


def _number(customer: Any, field: str, default: float = 0.0) -> float:
    try:
        value = customer.get(field, default)
        if value is None:
            return default
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError, AttributeError):
        return default


def _text(customer: Any, field: str, default: str = "") -> str:
    try:
        value = customer.get(field, default)
        if value is None:
            return default
        return str(value)
    except AttributeError:
        return default


def get_next_best_actions(customer: Any, score: dict | None = None) -> list[dict]:
    """Evaluate all applicable rules and return actions in descending priority order."""
    score = score or score_customer(customer)
    products = {product.strip().casefold() for product in _text(customer, "products_held").split(";") if product.strip()}
    satisfaction = _number(customer, "satisfaction_score", 5)
    balance = _number(customer, "avg_balance")
    utilization = _number(customer, "credit_utilization")
    login_days = _number(customer, "last_login_days_ago")
    tickets = _number(customer, "support_tickets_last_90d")
    tenure = _number(customer, "tenure_months")
    spend = _number(customer, "monthly_spend")
    segment = _text(customer, "segment")
    preferred_channel = _text(customer, "preferred_channel", "App") or "App"

    actions: list[dict] = []

    def add(action: str, reason: str, priority: int, impact: str) -> None:
        actions.append(
            {
                "action": action,
                "reason": reason,
                "priority": max(1, min(100, int(priority))),
                "channel": preferred_channel,
                "expected_impact": impact,
            }
        )

    if score.get("churn_risk_level") == "High" and satisfaction <= 5:
        add(
            "Retention call + loyalty offer",
            f"Churn risk is high and satisfaction is {satisfaction:.0f}/10.",
            96,
            "Improve retention",
        )
    if balance >= 100000 and not any("investment" in p or p in {"fd", "fixed deposit"} for p in products):
        add(
            "Offer investment / FD product",
            f"Average balance is {balance:,.0f}, with no investment or fixed-deposit product listed.",
            72,
            "Grow relationship value",
        )
    if utilization > 70:
        add(
            "Offer credit limit review / EMI conversion",
            f"Credit utilization is {utilization:.0f}%, above the 70% review threshold.",
            84,
            "Improve credit flexibility",
        )
    if login_days > 30:
        add(
            "Send a re-engagement push notification",
            f"No login has been recorded for {login_days:.0f} days.",
            min(90, 58 + int(min(login_days - 30, 32) * 0.65)),
            "Bring the customer back",
        )
    if tickets >= 3:
        add(
            "Schedule a priority service callback",
            f"There were {tickets:.0f} support tickets in the last 90 days.",
            min(98, 76 + int(min(tickets - 3, 5) * 4)),
            "Resolve friction quickly",
        )
    if len(products) == 1 and tenure >= 12:
        add(
            "Recommend a relevant second product",
            f"The customer has one product after {tenure:.0f} months with the business.",
            62,
            "Deepen the relationship",
        )
    if segment.casefold() == "premium" and spend >= 20000:
        add(
            "Invite to the premium rewards program",
            f"Premium customer with monthly spend of {spend:,.0f}.",
            68,
            "Reward loyalty",
        )

    if not actions:
        add(
            "Send a personalized account check-in",
            "No urgent rule was triggered; a light-touch check-in can maintain engagement.",
            28,
            "Maintain engagement",
        )

    fallback_actions = [
        (
            "Share a personalized savings insight",
            "A practical savings tip is a useful low-pressure touchpoint when no higher-priority rule applies.",
            22,
            "Build healthy savings habits",
        ),
        (
            "Offer a financial health check-in",
            "A brief review can uncover changing needs that are not captured by the current profile signals.",
            16,
            "Strengthen the relationship",
        ),
    ]
    for action, reason, priority, impact in fallback_actions:
        if len(actions) >= 3:
            break
        add(action, reason, priority, impact)

    # Stable ordering keeps the experience predictable when priorities tie.
    return sorted(actions, key=lambda item: item["priority"], reverse=True)
