"""Tenant-scoped transaction review operations; intentionally not exposed as API routes."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from tax_records.models import AuditEvent, FinancialTransaction

REVIEW_STATUSES = {"unreviewed", "needs_review", "confirmed", "ignored", "possible_duplicate"}


def list_transactions(
    session: Session, *, tenant_id: str, review_status: str | None = None, limit: int = 100
) -> list[FinancialTransaction]:
    """Return only the requested tenant's transactions, with a hard bounded page size."""
    if not tenant_id:
        raise ValueError("A verified tenant_id is required")
    if review_status is not None and review_status not in REVIEW_STATUSES:
        raise ValueError("Unsupported review status")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Limit must be a positive integer")
    bounded_limit = min(limit, 500)
    statement = select(FinancialTransaction).where(FinancialTransaction.tenant_id == tenant_id)
    if review_status is not None:
        statement = statement.where(FinancialTransaction.review_status == review_status)
    statement = statement.order_by(
        FinancialTransaction.transaction_date.desc(), FinancialTransaction.id
    ).limit(bounded_limit)
    return list(session.scalars(statement).all())


def update_transaction_review(
    session: Session,
    *,
    tenant_id: str,
    transaction_id: str,
    review_status: str,
    actor_user_id: str | None = None,
) -> FinancialTransaction:
    """Update review state only when the transaction belongs to the verified tenant."""
    if not tenant_id:
        raise ValueError("A verified tenant_id is required")
    if review_status not in REVIEW_STATUSES:
        raise ValueError("Unsupported review status")
    transaction = session.scalar(select(FinancialTransaction).where(
        FinancialTransaction.id == transaction_id,
        FinancialTransaction.tenant_id == tenant_id,
    ))
    if transaction is None:
        # Do not reveal whether an identifier exists in another tenant.
        raise ValueError("Transaction was not found in this workspace")
    previous_status = transaction.review_status
    if previous_status != review_status:
        transaction.review_status = review_status
        session.add(AuditEvent(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="transaction_review_status_changed",
            entity_type="financial_transaction",
            entity_id=transaction.id,
            change_reference=f"{previous_status}->{review_status}",
        ))
        session.flush()
    return transaction
