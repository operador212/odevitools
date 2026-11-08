import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

class DocumentEndpointAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_document_endpoint_fails_closed_without_oidc_configuration(self):
        with patch.dict(os.environ, {"OIDC_ISSUER": "", "OIDC_AUDIENCE": "", "OIDC_JWKS_URL": ""}, clear=False):
            response = self.client.post("/documents/analyze", files={"file": ("test.txt", b"invoice")})
        self.assertEqual(response.status_code, 401)

    def test_document_endpoint_requires_bearer_token(self):
        with patch.dict(os.environ, {"OIDC_ISSUER": "https://identity.example", "OIDC_AUDIENCE": "odevi", "OIDC_JWKS_URL": "https://identity.example/.well-known/jwks.json"}, clear=False):
            response = self.client.post("/documents/analyze", files={"file": ("test.txt", b"invoice")})
        self.assertEqual(response.status_code, 401)

if __name__ == "__main__":
    unittest.main()
