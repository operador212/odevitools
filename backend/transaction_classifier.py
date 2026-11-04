"""Rule-based first pass for classifying bank-statement transaction descriptions.

This module returns confidence and a review flag instead of pretending ambiguous
bank descriptions are certain. It does not calculate tax liability.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass(frozen=True)
class Classification:
    category: str
    counterparty: Optional[str]
    confidence: float
    needs_review: bool
    matched_rule: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# Broad aliases for common descriptors; never classify from "delivery" alone.
COUNTERPARTY_RULES = [
    ("Uber Eats", re.compile(r"\b(UBER\s*EATS|UBEREATS|UBER *BV)\b", re.I)),
    ("Deliveroo", re.compile(r"\b(DELIVEROO|ROOFOODS)\b", re.I)),
    ("Just Eat", re.compile(r"\b(JUST\s*EAT|JUSTEAT|TAKEAWAY\.COM)\b", re.I)),
    ("Amazon Flex", re.compile(r"\b(AMAZON\s*FLEX|AMZN\s*FLEX)\b", re.I)),
    ("Stuart", re.compile(r"\b(STUART\s*DELIVERY|STUART)\b", re.I)),
    ("Gophr", re.compile(r"\b(GOPHR)\b", re.I)),
    ("Evri", re.compile(r"\b(EVRI|HERMES\s*PARCEL)\b", re.I)),
    ("DPD", re.compile(r"\b(DPD\s*(UK|LOCAL)?)\b", re.I)),
    ("Royal Mail", re.compile(r"\b(ROYAL\s*MAIL|PARCELFORCE)\b", re.I)),
]

PERSONAL_TRANSFER = re.compile(
    r"\b(OWN\s*ACCOUNT|INTERNAL\s*TRANSFER|TRANSFER\s*BETWEEN\s*ACCOUNTS)\b",
    re.I,
)
REFUND = re.compile(r"\b(REFUND|REVERSAL|CHARGEBACK)\b", re.I)
PAYMENT_PROCESSOR = re.compile(
    r"\b(STRIPE|PAYPAL|SUMUP|WORLDPAY|ADYEN|WISE)\b", re.I
)
GENERIC_INCOME = re.compile(
    r"\b(FASTER\s*PAYMENT|BACS\s*CREDIT|BANK\s*TRANSFER|CREDIT\s*TRANSFER)\b",
    re.I,
)
GENERIC_EXPENSE = re.compile(
    r"\b(FUEL|PETROL|DIESEL|CHARGING|MOTOR\s*INSURANCE|INSURANCE|REPAIR|MAINTENANCE)\b",
    re.I,
)


def classify_transaction(description: str, amount: Optional[float] = None) -> Classification:
    """Classify one transaction description using conservative deterministic rules.

    Amount should be signed: positive for money received and negative for money
    paid. Normalize each bank's sign convention before calling this function.
    """
    text = (description or "").strip()
    if not text:
        return Classification("unknown", None, 0.0, True, "empty_description")

    for counterparty, pattern in COUNTERPARTY_RULES:
        if pattern.search(text):
            return Classification(
                "platform_income" if amount is None or amount >= 0 else "business_expense_or_charge",
                counterparty,
                0.94,
                False,
                f"platform:{counterparty.lower().replace(' ', '_')}",
            )

    if PERSONAL_TRANSFER.search(text):
        return Classification("own_account_transfer", None, 0.90, False, "own_account_transfer")

    if REFUND.search(text):
        return Classification("refund_or_reversal", None, 0.85, True, "refund_or_reversal")

    if PAYMENT_PROCESSOR.search(text):
        return Classification(
            "payment_processor", None, 0.62, True,
            "payment_processor_requires_context",
        )

    if amount is not None and amount > 0 and GENERIC_INCOME.search(text):
        return Classification("other_income_candidate", None, 0.60, True, "generic_credit")

    if amount is not None and amount < 0 and GENERIC_EXPENSE.search(text):
        return Classification("business_expense_candidate", None, 0.65, True, "expense_keyword")

    return Classification("unknown", None, 0.25, True, "no_rule_matched")
