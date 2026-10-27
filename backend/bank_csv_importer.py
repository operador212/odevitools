"""CSV bank-statement importer and automatic transaction summary.

This is an initial importer for text-based CSV exports. PDF parsing, OCR,
durable storage, and tax calculations are intentionally separate follow-up tasks.
"""
from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from transaction_classifier import classify_transaction


DATE_HEADERS = {"date", "transaction date", "booking date", "posted date", "data", "data da operacao"}
DESCRIPTION_HEADERS = {
    "description", "details", "transaction", "narrative", "reference", "payee",
    "merchant", "memo", "descricao", "descrição", "detalhes", "beneficiario",
    "beneficiário", "referencia", "referência",
}
AMOUNT_HEADERS = {"amount", "value", "transaction amount", "valor", "montante"}
CREDIT_HEADERS = {"credit", "paid in", "money in", "deposit", "credito", "crédito", "entrada"}
DEBIT_HEADERS = {"debit", "paid out", "money out", "withdrawal", "debito", "débito", "saida", "saída"}


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _parse_amount(value: Any) -> Decimal | None:
    """Parse common UK/European currency number formats conservatively."""
    if value is None:
        return None
    raw = str(value).strip().replace("£", "").replace("€", "").replace("$", "")
    raw = raw.replace("GBP", "").replace("EUR", "").replace(" ", "")
    if not raw or raw in {"-", "—"}:
        return None
    negative = raw.startswith("(") and raw.endswith(")")
    raw = raw.strip("()")
    # If both separators occur, the last one is treated as decimal separator.
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        tail = raw.rsplit(",", 1)[-1]
        raw = raw.replace(",", ".") if len(tail) in (1, 2) else raw.replace(",", "")
    try:
        amount = Decimal(raw)
        return -amount if negative else amount
    except InvalidOperation:
        return None


def _parse_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _find_header(headers: list[str], candidates: set[str]) -> str | None:
    normalized = {_norm(h): h for h in headers}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


def parse_bank_csv(csv_text: str, jurisdiction: str = "UK") -> dict[str, Any]:
    """Parse a bank CSV into normalized transactions and an automated summary.

    Accepts either a signed Amount/Value column or separate Credit and Debit
    columns. It does not silently guess when required columns are missing.
    """
    if jurisdiction.upper() not in {"UK", "PT"}:
        raise ValueError("jurisdiction must be UK or PT")

    sample = csv_text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(csv_text), dialect=dialect)
    if not reader.fieldnames:
        raise ValueError("CSV has no header row")

    headers = list(reader.fieldnames)
    date_col = _find_header(headers, DATE_HEADERS)
    desc_col = _find_header(headers, DESCRIPTION_HEADERS)
    amount_col = _find_header(headers, AMOUNT_HEADERS)
    credit_col = _find_header(headers, CREDIT_HEADERS)
    debit_col = _find_header(headers, DEBIT_HEADERS)

    if not date_col or not desc_col or not (amount_col or credit_col or debit_col):
        raise ValueError(
            "Could not identify date, description and amount/credit/debit columns"
        )

    transactions = []
    skipped_rows = 0
    for row in reader:
        description = str(row.get(desc_col, "") or "").strip()
        date = _parse_date(row.get(date_col))
        if amount_col:
            amount = _parse_amount(row.get(amount_col))
        else:
            credit = _parse_amount(row.get(credit_col)) if credit_col else None
            debit = _parse_amount(row.get(debit_col)) if debit_col else None
            amount = (credit or Decimal("0")) - abs(debit or Decimal("0"))
            if credit is None and debit is None:
                amount = None

        if not description and not date and amount is None:
            continue
        if not description or not date or amount is None:
            skipped_rows += 1
            continue

        classification = classify_transaction(description, float(amount))
        transactions.append({
            "date": date,
            "description": description,
            "amount": str(amount.quantize(Decimal("0.01"))),
            "currency": "GBP" if jurisdiction.upper() == "UK" else "UNKNOWN",
            "category": classification.category,
            "counterparty": classification.counterparty,
            "confidence": classification.confidence,
            "needs_review": classification.needs_review,
            "matched_rule": classification.matched_rule,
        })

    totals_by_category: dict[str, Decimal] = defaultdict(Decimal)
    totals_by_counterparty: dict[str, Decimal] = defaultdict(Decimal)
    totals_by_month: dict[str, Decimal] = defaultdict(Decimal)
    for tx in transactions:
        amount = Decimal(tx["amount"])
        totals_by_category[tx["category"]] += amount
        totals_by_month[tx["date"][:7]] += amount
        if tx["counterparty"]:
            totals_by_counterparty[tx["counterparty"]] += amount

    money = lambda d: str(d.quantize(Decimal("0.01")))
    return {
        "jurisdiction": jurisdiction.upper(),
        "transactions_count": len(transactions),
        "skipped_rows": skipped_rows,
        "totals_by_category": {k: money(v) for k, v in sorted(totals_by_category.items())},
        "totals_by_counterparty": {k: money(v) for k, v in sorted(totals_by_counterparty.items())},
        "net_movement_by_month": {k: money(v) for k, v in sorted(totals_by_month.items())},
        "transactions": transactions,
        "limitations": [
            "CSV importer prototype; test with each bank's export format before production.",
            "Amounts are bank movements, not automatically taxable income or deductible expenses.",
            "PDF/OCR, duplicate reconciliation, report generation and tax calculations are not implemented.",
        ],
    }
