"""Seed a handful of demo receivables so the dashboard has data to show.

Run from the backend directory with the virtualenv active:

    python -m scripts.seed_demo
"""
from datetime import date, timedelta

from app.models.receivable import Receivable
from app.services.receivables_service import create_receivable


# Amounts are in paise (Razorpay's smallest INR unit), consistent with
# payment amounts everywhere else in this service.
DEMO_RECEIVABLES = [
    dict(invoice_id="INV-1001", customer_id="cust_acme", customer_name="Acme Retail Pvt Ltd", amount=4_500_00, due_date_offset=-5),
    dict(invoice_id="INV-1002", customer_id="cust_bharat", customer_name="Bharat Textiles", amount=1_20_000_00, due_date_offset=-20),
    dict(invoice_id="INV-1003", customer_id="cust_delta", customer_name="Delta Logistics", amount=3_50_000_00, due_date_offset=-40),
    dict(invoice_id="INV-1004", customer_id="cust_evergreen", customer_name="Evergreen Foods", amount=18_000_00, due_date_offset=-70),
    dict(invoice_id="INV-1005", customer_id="cust_finpay", customer_name="FinPay Solutions", amount=90_000_00, due_date_offset=3),
]


def main() -> None:
    today = date.today()
    for item in DEMO_RECEIVABLES:
        receivable = Receivable(
            invoice_id=item["invoice_id"],
            customer_id=item["customer_id"],
            customer_name=item["customer_name"],
            amount=item["amount"],
            due_date=today + timedelta(days=item["due_date_offset"]),
        )
        create_receivable(receivable)
        print(f"seeded {receivable.invoice_id}")


if __name__ == "__main__":
    main()
