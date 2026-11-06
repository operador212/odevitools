"""Tenant-scoped persistence models. Amounts use Decimal-backed Numeric columns."""
from __future__ import annotations
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def new_id() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class Tenant(Base):
    __tablename__ = "tax_tenants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/London")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    jurisdictions: Mapped[list["JurisdictionProfile"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    accounts: Mapped[list["FinancialAccount"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    imports: Mapped[list["ImportJob"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    transactions: Mapped[list["FinancialTransaction"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")

class JurisdictionProfile(Base):
    __tablename__ = "tax_jurisdiction_profiles"
    __table_args__ = (UniqueConstraint("tenant_id", "country_code", "tax_year", name="uq_tax_jurisdiction_year"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    tax_year: Mapped[str] = mapped_column(String(24), nullable=False)
    rule_pack_version: Mapped[str] = mapped_column(String(32), nullable=False, default="unconfigured")
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    tenant: Mapped[Tenant] = relationship(back_populates="jurisdictions")

class FinancialAccount(Base):
    __tablename__ = "tax_financial_accounts"
    __table_args__ = (CheckConstraint("length(currency) = 3", name="ck_tax_account_currency"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(80))
    account_token: Mapped[str | None] = mapped_column(String(160))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    tenant: Mapped[Tenant] = relationship(back_populates="accounts")
    transactions: Mapped[list["FinancialTransaction"]] = relationship(back_populates="account")

class ImportJob(Base):
    __tablename__ = "tax_import_jobs"
    __table_args__ = (UniqueConstraint("tenant_id", "file_sha256", name="uq_tax_import_file_per_tenant"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    error_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tenant: Mapped[Tenant] = relationship(back_populates="imports")
    transactions: Mapped[list["FinancialTransaction"]] = relationship(back_populates="import_job")

class Category(Base):
    __tablename__ = "tax_categories"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_tax_category_code"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tenant: Mapped[Tenant] = relationship(back_populates="categories")

class FinancialTransaction(Base):
    __tablename__ = "tax_transactions"
    __table_args__ = (CheckConstraint("length(currency) = 3", name="ck_tax_transaction_currency"),
        Index("ix_tax_transaction_tenant_date", "tenant_id", "transaction_date"),
        Index("ix_tax_transaction_import_row", "import_job_id", "source_row_number"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[str | None] = mapped_column(ForeignKey("tax_financial_accounts.id", ondelete="SET NULL"))
    import_job_id: Mapped[str | None] = mapped_column(ForeignKey("tax_import_jobs.id", ondelete="SET NULL"), index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2, asdecimal=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    source_row_number: Mapped[int | None] = mapped_column(Integer)
    source_fingerprint: Mapped[str | None] = mapped_column(String(64))
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="needs_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    tenant: Mapped[Tenant] = relationship(back_populates="transactions")
    account: Mapped[FinancialAccount | None] = relationship(back_populates="transactions")
    import_job: Mapped[ImportJob | None] = relationship(back_populates="transactions")
    splits: Mapped[list["TransactionSplit"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")

class TransactionSplit(Base):
    __tablename__ = "tax_transaction_splits"
    __table_args__ = (CheckConstraint("length(currency) = 3", name="ck_tax_split_currency"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("tax_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("tax_categories.id", ondelete="SET NULL"))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2, asdecimal=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    transaction: Mapped[FinancialTransaction] = relationship(back_populates="splits")

class ClassificationSuggestion(Base):
    __tablename__ = "tax_classification_suggestions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("tax_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("tax_categories.id", ondelete="SET NULL"))
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(40), nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

class AuditEvent(Base):
    __tablename__ = "tax_audit_events"
    __table_args__ = (Index("ix_tax_audit_tenant_created", "tenant_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(48), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(48), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    change_reference: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
