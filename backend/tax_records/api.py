"""Authenticated Tax Records API. Routes stay unavailable until OIDC and DB are configured."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from tax_records.access import TenantAccess
from tax_records.dependencies import tenant_access_dependency
from tax_records.models import FinancialTransaction
from tax_records.sessions import get_db_session
from tax_records.import_service import import_bank_csv
from tax_records.review_service import list_transactions, update_transaction_review

router = APIRouter(prefix="/tax-records", tags=["Tax Records v2"])
MAX_CSV_BYTES = 5 * 1024 * 1024


class ReviewRequest(BaseModel):
    review_status: str = Field(min_length=1, max_length=32)


def _transaction_json(item: FinancialTransaction) -> dict:
    return {
        "id": item.id,
        "date": item.transaction_date.isoformat(),
        "description": item.description,
        "amount": str(item.amount),
        "currency": item.currency,
        "review_status": item.review_status,
        "account_id": item.account_id,
        "import_job_id": item.import_job_id,
    }


@router.get("/{tenant_id}/transactions")
def get_transactions(
    tenant_id: str,
    review_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    access: TenantAccess = Depends(tenant_access_dependency("viewer")),
    session: Session = Depends(get_db_session),
):
    try:
        items = list_transactions(session, tenant_id=access.tenant_id,
                                  review_status=review_status, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"items": [_transaction_json(item) for item in items], "count": len(items)}


@router.post("/{tenant_id}/imports/csv")
async def import_csv(
    tenant_id: str,
    jurisdiction: str = Query(pattern="^(UK|PT)$"),
    file: UploadFile = File(...),
    access: TenantAccess = Depends(tenant_access_dependency("contributor")),
    session: Session = Depends(get_db_session),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Envia um ficheiro CSV.")
    raw = await file.read(MAX_CSV_BYTES + 1)
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="O ficheiro excede o limite de 5 MB.")
    try:
        csv_text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="O CSV deve estar codificado em UTF-8.") from exc
    try:
        result = import_bank_csv(session, tenant_id=access.tenant_id,
                                 filename=file.filename, csv_text=csv_text,
                                 jurisdiction=jurisdiction)
        session.commit()
        return result
    except (ValueError, KeyError) as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        session.rollback()
        raise HTTPException(status_code=500, detail="Não foi possível concluir a importação.") from None
    finally:
        await file.close()


@router.patch("/{tenant_id}/transactions/{transaction_id}/review")
def review_transaction(
    tenant_id: str,
    transaction_id: str,
    request: ReviewRequest,
    access: TenantAccess = Depends(tenant_access_dependency("contributor")),
    session: Session = Depends(get_db_session),
):
    try:
        item = update_transaction_review(
            session, tenant_id=access.tenant_id, transaction_id=transaction_id,
            review_status=request.review_status, actor_user_id=access.user_subject,
        )
        session.commit()
        return _transaction_json(item)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
