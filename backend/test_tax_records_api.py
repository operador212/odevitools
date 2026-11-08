import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from tax_records.api import get_current_principal, get_db_session
from tax_records.access import VerifiedPrincipal
from tax_records.models import Base, TenantMembership, JurisdictionProfile


class TaxRecordsWorkspaceApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.principal = VerifiedPrincipal(issuer="https://issuer.example/", subject="user-123")

        def db_session():
            with self.factory() as session:
                yield session

        app.dependency_overrides[get_db_session] = db_session
        app.dependency_overrides[get_current_principal] = lambda: self.principal
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_user_can_create_and_list_own_uk_workspace(self):
        response = self.client.post("/tax-records/workspaces", json={
            "name": "My UK business", "country_code": "UK", "tax_year": "2026-27"
        })
        self.assertEqual(response.status_code, 201, response.text)
        workspace = response.json()
        self.assertEqual(workspace["currency"], "GBP")
        self.assertEqual(workspace["role"], "owner")
        listed = self.client.get("/tax-records/workspaces")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["items"][0]["id"], workspace["id"])

    def test_duplicate_country_tax_year_workspace_is_rejected(self):
        payload = {"name": "Portugal", "country_code": "PT", "tax_year": "2026"}
        self.assertEqual(self.client.post("/tax-records/workspaces", json=payload).status_code, 201)
        response = self.client.post("/tax-records/workspaces", json=payload)
        self.assertEqual(response.status_code, 409)

    def test_invalid_tax_year_is_rejected(self):
        response = self.client.post("/tax-records/workspaces", json={
            "name": "Bad year", "country_code": "UK", "tax_year": "2026-28"
        })
        self.assertEqual(response.status_code, 400)

    def test_other_identity_cannot_list_workspace(self):
        self.client.post("/tax-records/workspaces", json={
            "name": "My UK business", "country_code": "UK", "tax_year": "2026-27"
        })
        app.dependency_overrides[get_current_principal] = lambda: VerifiedPrincipal(
            issuer="https://issuer.example/", subject="different-user"
        )
        response = self.client.get("/tax-records/workspaces")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])


if __name__ == "__main__":
    unittest.main()
