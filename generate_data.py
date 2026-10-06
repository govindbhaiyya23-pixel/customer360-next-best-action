"""Generate deterministic synthetic customer and transaction data for the demo."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
RNG = np.random.default_rng(2026)

CITIES = ["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune", "Ahmedabad", "Chennai", "Jaipur"]
PRODUCTS = ["Savings", "Credit Card", "Personal Loan", "Insurance", "Fixed Deposit", "Investment"]
CATEGORIES = ["Groceries", "Travel", "Dining", "Bills", "Shopping", "Healthcare", "Transport", "Entertainment"]
CHANNELS = ["App", "Email", "SMS", "Call"]


def _customer_rows(count: int = 500) -> pd.DataFrame:
    records = []
    first_names = [
        "Aanya", "Aarav", "Aditya", "Anaya", "Arjun", "Diya", "Ishaan", "Kavya",
        "Meera", "Neha", "Rohan", "Saanvi", "Vihaan", "Zoya", "Kabir", "Tara",
    ]
    last_names = [
        "Shah", "Patel", "Reddy", "Iyer", "Mehta", "Kapoor", "Nair", "Rao",
        "Singh", "Das", "Joshi", "Khan", "Pillai", "Gupta", "Verma", "Desai",
    ]
    segment_values = ["Retail", "Premium", "SME"]

    for i in range(1, count + 1):
        segment = str(RNG.choice(segment_values, p=[0.64, 0.21, 0.15]))
        spend_base = {"Retail": 8500, "Premium": 34000, "SME": 56000}[segment]
        balance_base = {"Retail": 52000, "Premium": 390000, "SME": 520000}[segment]
        monthly_spend = max(700, float(RNG.lognormal(np.log(spend_base), 0.62)))
        avg_balance = max(1500, float(RNG.lognormal(np.log(balance_base), 0.85)))

        product_count = int(RNG.choice([1, 2, 3, 4], p=[0.38, 0.34, 0.20, 0.08]))
        held_products = RNG.choice(PRODUCTS, size=product_count, replace=False).tolist()
        # Keep credit utilization meaningful only for customers with a card.
        has_card = "Credit Card" in held_products
        records.append(
            {
                "customer_id": f"CUST-{i:04d}",
                "name": f"{RNG.choice(first_names)} {RNG.choice(last_names)}",
                "age": int(RNG.integers(21, 71)),
                "gender": str(RNG.choice(["Female", "Male", "Non-binary"], p=[0.48, 0.49, 0.03])),
                "city": str(RNG.choice(CITIES)),
                "segment": segment,
                "tenure_months": int(RNG.integers(1, 181)),
                "products_held": ";".join(held_products),
                "num_products": product_count,
                "monthly_spend": round(monthly_spend, 2),
                "avg_balance": round(avg_balance, 2),
                "last_login_days_ago": int(min(RNG.gamma(1.8, 17), 120)),
                "last_transaction_days_ago": int(min(RNG.gamma(1.7, 15), 120)),
                "support_tickets_last_90d": int(RNG.choice([0, 1, 2, 3, 4, 5], p=[0.40, 0.25, 0.16, 0.10, 0.06, 0.03])),
                "satisfaction_score": int(RNG.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], p=[0.01, 0.02, 0.04, 0.07, 0.11, 0.14, 0.20, 0.20, 0.14, 0.07])),
                "loan_active": str(RNG.choice(["Y", "N"], p=[0.31, 0.69])),
                "credit_utilization": round(float(RNG.uniform(5, 98) if has_card else 0), 1),
                "email_opt_in": str(RNG.choice(["Y", "N"], p=[0.76, 0.24])),
                "preferred_channel": str(RNG.choice(CHANNELS, p=[0.53, 0.24, 0.13, 0.10])),
            }
        )

    return pd.DataFrame(records)


def _transaction_rows(customers: pd.DataFrame, count: int = 3000) -> pd.DataFrame:
    end = pd.Timestamp.today().normalize()
    start = end - pd.Timedelta(days=365)
    day_offsets = RNG.integers(0, 366, size=count)
    customer_indices = RNG.integers(0, len(customers), size=count)
    categories = RNG.choice(CATEGORIES, size=count, p=[0.19, 0.10, 0.15, 0.16, 0.16, 0.07, 0.11, 0.06])
    amounts = RNG.lognormal(mean=np.log(1800), sigma=1.05, size=count)
    amounts = np.clip(amounts, 80, 95000).round(2)

    return pd.DataFrame(
        {
            "customer_id": customers.iloc[customer_indices]["customer_id"].to_numpy(),
            "date": (start + pd.to_timedelta(day_offsets, unit="D")).date,
            "category": categories,
            "amount": amounts,
        }
    ).sort_values("date", ascending=False, ignore_index=True)


def generate_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create both CSV files and return the generated frames."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    customers = _customer_rows(500)
    transactions = _transaction_rows(customers, 3000)
    customers.to_csv(DATA_DIR / "customers.csv", index=False)
    transactions.to_csv(DATA_DIR / "transactions.csv", index=False)
    return customers, transactions


if __name__ == "__main__":
    customer_data, transaction_data = generate_all()
    print(f"Wrote {len(customer_data):,} customers to {DATA_DIR / 'customers.csv'}")
    print(f"Wrote {len(transaction_data):,} transactions to {DATA_DIR / 'transactions.csv'}")
