import unittest
from unittest.mock import Mock, patch
import jwt
from tax_records.oidc import verify_oidc_access_token

class OidcVerificationTests(unittest.TestCase):
    def test_valid_verified_claims_create_principal(self):
        key_client = Mock()
        key_client.get_signing_key_from_jwt.return_value.key = "public-key"
        with patch("tax_records.oidc.jwt.decode", return_value={
            "sub": "provider|subject-1", "iss": "https://id.example/",
            "aud": "odevi-api", "exp": 2000000000, "iat": 1900000000,
        }) as decode:
            principal = verify_oidc_access_token("signed-token", issuer="https://id.example/",
                audience="odevi-api", jwks_url="https://id.example/.well-known/jwks.json",
                jwks_client=key_client)
        self.assertEqual(principal.subject, "provider|subject-1")
        self.assertEqual(principal.issuer, "https://id.example/")
        decode.assert_called_once()
        self.assertEqual(decode.call_args.kwargs["algorithms"], ["RS256", "ES256"])
        self.assertEqual(decode.call_args.kwargs["audience"], "odevi-api")

    def test_missing_subject_rejected(self):
        key_client = Mock()
        key_client.get_signing_key_from_jwt.return_value.key = "public-key"
        with patch("tax_records.oidc.jwt.decode", return_value={"iss": "https://id.example/"}):
            with self.assertRaises(jwt.InvalidTokenError):
                verify_oidc_access_token("signed-token", issuer="https://id.example/",
                    audience="odevi-api", jwks_url="https://id.example/jwks", jwks_client=key_client)

    def test_missing_configuration_rejected(self):
        with self.assertRaisesRegex(ValueError, "required"):
            verify_oidc_access_token("token", issuer="", audience="api",
                jwks_url="https://id.example/jwks", jwks_client=Mock())

    def test_invalid_signature_or_claims_propagate_as_invalid_token(self):
        key_client = Mock()
        key_client.get_signing_key_from_jwt.return_value.key = "public-key"
        with patch("tax_records.oidc.jwt.decode", side_effect=jwt.InvalidAudienceError("wrong audience")):
            with self.assertRaises(jwt.InvalidAudienceError):
                verify_oidc_access_token("signed-token", issuer="https://id.example/",
                    audience="odevi-api", jwks_url="https://id.example/jwks", jwks_client=key_client)

if __name__ == "__main__":
    unittest.main()
