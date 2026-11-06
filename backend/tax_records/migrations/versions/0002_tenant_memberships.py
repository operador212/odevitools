"""Add tenant membership and role records; identity subjects come from a verified IdP."""
from alembic import op
import sqlalchemy as sa
revision = "0002_tenant_memberships"
down_revision = "0001_tax_records"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "tax_tenant_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tax_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("identity_issuer", sa.String(255), nullable=False),
        sa.Column("user_subject", sa.String(255), nullable=False),
        sa.Column("role", sa.String(24), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "identity_issuer", "user_subject", name="uq_tax_tenant_identity"),
        sa.CheckConstraint("role IN ('viewer', 'contributor', 'owner')", name="ck_tax_membership_role"),
    )
    op.create_index("ix_tax_tenant_memberships_tenant_id", "tax_tenant_memberships", ["tenant_id"])
    op.create_index("ix_tax_tenant_memberships_identity", "tax_tenant_memberships", ["identity_issuer", "user_subject"])

def downgrade():
    op.drop_table("tax_tenant_memberships")
