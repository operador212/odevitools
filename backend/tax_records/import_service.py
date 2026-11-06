"""Persist normalized CSV imports without exposing a public endpoint.

The caller must supply a tenant_id obtained from a trusted authentication layer.
This service never trusts a tenant id from an uploaded CSV and never stores the
original statement bytes. Exact matching is flagged for review, not discarded.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bank_csv_importer import parse_bank_csv
from tax_records.models import AuditEvent, ClassificationSuggestion, FinancialAccount, FinancialTransaction, ImportJob, Tenant

PARSER_VERSION = "csv-v1"


def _fingerprint(tx: dict[str, Any]) -> str:
    normalized = "|".join((
        str(tx["date"]),
        re.sub(r"\s+", " ", str(tx["description"]).strip().casefold()),
        str(Decimal(str(tx["amount"])).quantize(Decimal("0.01"))),
        str(tx["currency"]).upper(),
    ))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def import_bank_csv(
    session: Session,
    *,
    tenant_id: str,
    filename: str,
    csv_text: str,
    jurisdiction: str,
    account_id: str | None = None,
) -> dict[str, Any]:
    """Import one CSV into a tenant workspace; caller owns transaction commit."""
    if not tenant_id:
        raise ValueError("A verified tenant_id is required")
    tenant = session.get(Tenant, tenant_id)
    if tenant is None:
        raise ValueError("Tenant workspace does not exist")
    if account_id:
        account = session.scalar(select(FinancialAccount).where(
            FinancialAccount.id == account_id,
            FinancialAccount.tenant_id == tenant_id,
        ))
        if account is None:
            raise ValueError("Financial account does not belong to this workspace")
    if not filename or len(filename) > 255:
        raise ValueError("A valid source filename is required")
    if not csv_text or not csv_text.strip():
        raise ValueError("CSV file is empty")

    parsed = parse_bank_csv(csv_text, jurisdiction)
    file_hash = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
    existing_job = session.scalar(select(ImportJob).where(
        ImportJob.tenant_id == tenant_id,
        ImportJob.file_sha256 == file_hash,
    ))
    if existing_job is not None:
        return {
            "import_id": existing_job.id,
            "status": "already_imported",
            "transactions_added": 0,
            "possible_duplicates": 0,
            "skipped_rows": 0,
            "idempotent_replay": True,
        }

    job = ImportJob(
        tenant_id=tenant_id,
        source_filename=filename,
        file_sha256=file_hash,
        parser_version=PARSER_VERSION,
        status="processing",
    )
    session.add(job)
    session.flush()

    added = 0
    possible_duplicates = 0
    for row_number, item in enumerate(parsed["transactions"], start=2):
        fingerprint = _fingerprint(item)
        duplicate = session.scalar(select(FinancialTransaction.id).where(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.source_fingerprint == fingerprint,
        ).limit(1))
        review_status = "possible_duplicate" if duplicate else (
            "needs_review" if item.get("needs_review") else "unreviewed"
        )
        if duplicate:
            possible_duplicates += 1
        transaction = FinancialTransaction(
            tenant_id=tenant_id,
            account_id=account_id,
            import_job_id=job.id,
            transaction_date=date.fromisoformat(item["date"]),
            description=item["description"],
            amount=Decimal(item["amount"]),
            currency=item["currency"].upper(),
            source_row_number=row_number,
            source_fingerprint=fingerprint,
            review_status=review_status,
        )
        session.add(transaction)
        session.flush()
        session.add(ClassificationSuggestion(
            transaction_id=transaction.id,
            confidence=Decimal(str(item.get("confidence", 0))).quantize(Decimal("0.0001")),
            rationale=str(item.get("matched_rule") or "No deterministic rule matched; manual review required"),
            engine_version="transaction-classifier-v1",
            reviewed=False,
        ))
        added += 1

    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    session.add(AuditEvent(
        tenant_id=tenant_id,
        action="csv_import_completed",
        entity_type="import_job",
        entity_id=job.id,
        change_reference=file_hash,
    ))
    session.flush()
    return {
        "import_id": job.id,
        "status": job.status,
        "transactions_added": added,
        "possible_duplicates": possible_duplicates,
        "skipped_rows": parsed["skipped_rows"],
        "idempotent_replay": False,
    }
