"""Composable FastAPI dependencies for authenticated, tenant-scoped routes.

Import these dependencies into a route only after OIDC configuration and a real
identity provider are provisioned. No route is mounted by this module.
"""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from tax_records.access import TenantAccess, VerifiedPrincipal, require_tenant_access
from tax_records.oidc import get_current_principal
from tax_records.sessions import get_db_session

def tenant_access_dependency(minimum_role: str = "viewer"):
    """Return a route dependency that resolves membership for its tenant_id parameter."""
    if minimum_role not in {"viewer", "contributor", "owner"}:
        raise ValueError("Unsupported minimum role")

    def dependency(
        tenant_id: str,
        principal: VerifiedPrincipal = Depends(get_current_principal),
        session: Session = Depends(get_db_session),
    ) -> TenantAccess:
        try:
            return require_tenant_access(session, principal=principal,
                                         tenant_id=tenant_id, minimum_role=minimum_role)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Acesso negado") from exc

    return dependency
