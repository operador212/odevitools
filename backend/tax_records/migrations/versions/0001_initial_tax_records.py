"""Initial ODEVI Tax Records v2 schema."""
from alembic import op
import sqlalchemy as sa
revision = "0001_tax_records"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("tax_tenants", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("tax_jurisdiction_profiles", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False), sa.Column("tax_year", sa.String(24), nullable=False),
        sa.Column("rule_pack_version", sa.String(32), nullable=False), sa.Column("confirmed_by_user", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "country_code", "tax_year", name="uq_tax_jurisdiction_year"))
    op.create_index("ix_tax_jurisdiction_profiles_tenant_id", "tax_jurisdiction_profiles", ["tenant_id"])
    op.create_table("tax_financial_accounts", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False), sa.Column("provider", sa.String(80)),
        sa.Column("account_token", sa.String(160)), sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(currency) = 3", name="ck_tax_account_currency"))
    op.create_index("ix_tax_financial_accounts_tenant_id", "tax_financial_accounts", ["tenant_id"])
    op.create_table("tax_import_jobs", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_filename", sa.String(255), nullable=False), sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("parser_version", sa.String(32), nullable=False), sa.Column("status", sa.String(24), nullable=False),
        sa.Column("error_summary", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "file_sha256", name="uq_tax_import_file_per_tenant"))
    op.create_index("ix_tax_import_jobs_tenant_id", "tax_import_jobs", ["tenant_id"])
    op.create_table("tax_categories", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(48), nullable=False), sa.Column("label", sa.String(120), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_tax_category_code"))
    op.create_index("ix_tax_categories_tenant_id", "tax_categories", ["tenant_id"])
    op.create_table("tax_transactions", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("tax_financial_accounts.id", ondelete="SET NULL")),
        sa.Column("import_job_id", sa.String(36), sa.ForeignKey("tax_import_jobs.id", ondelete="SET NULL")),
        sa.Column("transaction_date", sa.Date(), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2, asdecimal=True), nullable=False), sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("source_row_number", sa.Integer()), sa.Column("source_fingerprint", sa.String(64)),
        sa.Column("review_status", sa.String(24), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(currency) = 3", name="ck_tax_transaction_currency"))
    op.create_index("ix_tax_transactions_tenant_id", "tax_transactions", ["tenant_id"])
    op.create_index("ix_tax_transactions_import_job_id", "tax_transactions", ["import_job_id"])
    op.create_index("ix_tax_transaction_tenant_date", "tax_transactions", ["tenant_id", "transaction_date"])
    op.create_index("ix_tax_transaction_import_row", "tax_transactions", ["import_job_id", "source_row_number"])
    op.create_table("tax_transaction_splits", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("transaction_id", sa.String(36), sa.ForeignKey("tax_transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("tax_categories.id", ondelete="SET NULL")),
        sa.Column("amount", sa.Numeric(18, 2, asdecimal=True), nullable=False), sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("note", sa.Text()), sa.CheckConstraint("length(currency) = 3", name="ck_tax_split_currency"))
    op.create_index("ix_tax_transaction_splits_transaction_id", "tax_transaction_splits", ["transaction_id"])
    op.create_table("tax_classification_suggestions", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("transaction_id", sa.String(36), sa.ForeignKey("tax_transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("tax_categories.id", ondelete="SET NULL")),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False), sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("engine_version", sa.String(40), nullable=False), sa.Column("reviewed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_tax_classification_suggestions_transaction_id", "tax_classification_suggestions", ["transaction_id"])
    op.create_table("tax_audit_events", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", sa.String(128)), sa.Column("action", sa.String(48), nullable=False),
        sa.Column("entity_type", sa.String(48), nullable=False), sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("change_reference", sa.String(128)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_tax_audit_events_tenant_id", "tax_audit_events", ["tenant_id"])
    op.create_index("ix_tax_audit_tenant_created", "tax_audit_events", ["tenant_id", "created_at"])

def downgrade():
    for table in ("tax_audit_events", "tax_classification_suggestions", "tax_transaction_splits",
                  "tax_transactions", "tax_categories", "tax_import_jobs", "tax_financial_accounts",
                  "tax_jurisdiction_profiles", "tax_tenants"):
        op.drop_table(table)
