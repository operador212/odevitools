"""Build a cautious multi-statement report from normalized bank CSV imports.

This creates an accounting-preparation summary, not a tax return or tax-liability
calculation. Bank credits are not automatically taxable income and debits are
not automatically deductible expenses.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Iterable

INCOME_CATEGORIES = {"platform_income", "other_income_candidate"}
EXPENSE_CATEGORIES = {"business_expense_candidate", "business_expense_or_charge"}


def build_tax_report(import_results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    results = list(import_results)
    if not results:
        raise ValueError("At least one parsed statement is required")

    jurisdictions = {str(result.get("jurisdiction", "")).upper() for result in results}
    if len(jurisdictions) != 1 or not jurisdictions.issubset({"UK", "PT"}):
        raise ValueError("All statements must use the same supported jurisdiction (UK or PT)")

    transactions = []
    source_count = 0
    skipped_rows = 0
    for result in results:
        source_count += 1
        skipped_rows += int(result.get("skipped_rows", 0))
        for tx in result.get("transactions", []):
            normalized = dict(tx)
            normalized.setdefault("source_statement", f"statement_{source_count}")
            transactions.append(normalized)

    # Remove exact duplicates across uploaded statements only. This is a
    # conservative signature; similar-but-not-identical transactions remain.
    seen = set()
    unique_transactions = []
    duplicate_count = 0
    for tx in transactions:
        signature = (
            str(tx.get("date", "")),
            str(tx.get("description", "")).strip().casefold(),
            str(tx.get("amount", "")),
            str(tx.get("currency", "")),
        )
        if signature in seen:
            duplicate_count += 1
            continue
        seen.add(signature)
        unique_transactions.append(tx)

    by_currency_category = defaultdict(Decimal)
    by_currency_counterparty = defaultdict(Decimal)
    by_currency_month = defaultdict(Decimal)
    by_currency_year = defaultdict(Decimal)
    income_candidates = defaultdict(Decimal)
    expense_candidates = defaultdict(Decimal)
    review_items = []
    currencies = set()

    for tx in unique_transactions:
        amount = Decimal(str(tx["amount"]))
        currency = str(tx.get("currency") or "UNKNOWN")
        currencies.add(currency)
        category = str(tx.get("category") or "unknown")
        counterparty = str(tx.get("counterparty") or "Unidentified")
        date = str(tx.get("date") or "")
        prefix = currency + ":"
        by_currency_category[prefix + category] += amount
        by_currency_counterparty[prefix + counterparty] += amount
        if len(date) >= 7:
            by_currency_month[prefix + date[:7]] += amount
        if len(date) >= 4:
            by_currency_year[prefix + date[:4]] += amount
        if category in INCOME_CATEGORIES and amount > 0:
            income_candidates[prefix + category] += amount
        if category in EXPENSE_CATEGORIES and amount < 0:
            expense_candidates[prefix + category] += abs(amount)
        if tx.get("needs_review"):
            review_items.append({
                "date": date,
                "description": tx.get("description", ""),
                "amount": str(amount.quantize(Decimal("0.01"))),
                "currency": currency,
                "category": category,
                "reason": tx.get("matched_rule") or "low_confidence_or_unmatched",
            })

    def money_map(mapping):
        return {key: str(value.quantize(Decimal("0.01"))) for key, value in sorted(mapping.items())}

    return {
        "report_type": "tax_preparation_summary",
        "jurisdiction": next(iter(jurisdictions)),
        "source_statements_count": source_count,
        "transactions_imported": len(transactions),
        "transactions_after_exact_deduplication": len(unique_transactions),
        "exact_duplicates_removed": duplicate_count,
        "skipped_rows": skipped_rows,
        "currencies": sorted(currencies),
        "net_bank_movement_by_month": money_map(by_currency_month),
        "net_bank_movement_by_year": money_map(by_currency_year),
        "net_bank_movement_by_category": money_map(by_currency_category),
        "net_bank_movement_by_counterparty": money_map(by_currency_counterparty),
        "income_candidates_not_tax_confirmed": money_map(income_candidates),
        "expense_candidates_not_deductibility_confirmed": money_map(expense_candidates),
        "review_items_count": len(review_items),
        "review_items": review_items,
        "limitations": [
            "This is an automated preparation summary, not a tax return or tax advice.",
            "Bank movements are not equivalent to taxable income or deductible expenses.",
            "Only exact duplicate signatures are removed; near-duplicates require more advanced reconciliation.",
            "Income and expense candidates must be checked against platform statements, invoices and applicable country rules.",
            "No tax liability, VAT, National Insurance, Portuguese Social Security or withholding calculation is performed.",
        ],
    }
