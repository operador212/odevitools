"""Server-side tenant authorization primitives; no token parsing or public routes here.

The future authentication adapter must validate identity tokens before creating
VerifiedPrincipal. Never construct it from browser-supplied user or tenant IDs.
"""
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session
from tax_records.models import TenantMembership

ROLE_LEVEL = {"viewer": 1, "contributor": 2, "owner": 3}

@dataclass(frozen=True)
class VerifiedPrincipal:
    """Identity established by a trusted adapter, not request input."""
    subject: str
    issuer: str

    def __post_init__(self):
        if not self.subject.strip() or not self.issuer.strip():
            raise ValueError("Verified identity subject and issuer are required")

@dataclass(frozen=True)
class TenantAccess:
    tenant_id: str
    user_subject: str
    role: str

def require_tenant_access(session: Session, *, principal: VerifiedPrincipal,
                          tenant_id: str, minimum_role: str = "viewer") -> TenantAccess:
    """Resolve active membership server-side; fail closed without revealing membership."""
    if minimum_role not in ROLE_LEVEL:
        raise ValueError("Unsupported minimum role")
    membership = session.scalar(select(TenantMembership).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.user_subject == principal.subject,
        TenantMembership.identity_issuer == principal.issuer,
        TenantMembership.is_active.is_(True),
    ))
    if membership is None or ROLE_LEVEL.get(membership.role, 0) < ROLE_LEVEL[minimum_role]:
        raise PermissionError("Access denied")
    return TenantAccess(tenant_id=tenant_id, user_subject=principal.subject, role=membership.role)
