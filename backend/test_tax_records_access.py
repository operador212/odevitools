import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tax_records.access import VerifiedPrincipal, require_tenant_access
from tax_records.models import Base, Tenant, TenantMembership

class TenantAccessTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            tenant = Tenant(name="Private workspace")
            session.add(tenant); session.flush()
            session.add(TenantMembership(tenant_id=tenant.id, user_subject="auth0|user-1",
                identity_issuer="https://identity.example/", role="contributor", is_active=True))
            session.commit()
            self.tenant_id = tenant.id

    def tearDown(self):
        self.engine.dispose()

    def test_verified_member_gets_workspace_access(self):
        with Session(self.engine) as session:
            access = require_tenant_access(session, principal=VerifiedPrincipal(
                subject="auth0|user-1", issuer="https://identity.example/"), tenant_id=self.tenant_id,
                minimum_role="contributor")
            self.assertEqual(access.role, "contributor")

    def test_wrong_issuer_or_subject_is_denied(self):
        with Session(self.engine) as session:
            for principal in (VerifiedPrincipal("auth0|user-1", "https://other.example/"),
                              VerifiedPrincipal("auth0|user-2", "https://identity.example/")):
                with self.assertRaises(PermissionError):
                    require_tenant_access(session, principal=principal, tenant_id=self.tenant_id)

    def test_viewer_cannot_perform_contributor_action(self):
        with Session(self.engine) as session:
            membership = session.query(TenantMembership).one()
            membership.role = "viewer"; session.commit()
            with self.assertRaises(PermissionError):
                require_tenant_access(session, principal=VerifiedPrincipal(
                    "auth0|user-1", "https://identity.example/"), tenant_id=self.tenant_id,
                    minimum_role="contributor")

    def test_invalid_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            VerifiedPrincipal("", "https://identity.example/")

if __name__ == "__main__":
    unittest.main()
