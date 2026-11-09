import unittest
from unittest.mock import patch

from number_providers.zadarma import (
    ZadarmaConfigurationError,
    ZadarmaReadOnlyClient,
)


class ZadarmaReadOnlyClientTests(unittest.TestCase):
    def test_signature_is_deterministic(self):
        signature = ZadarmaReadOnlyClient.signature(
            "/v1/direct_numbers/countries/",
            {"language": "en"},
            "test-secret",
        )
        self.assertEqual(
            signature,
            ZadarmaReadOnlyClient.signature(
                "/v1/direct_numbers/countries/",
                {"language": "en"},
                "test-secret",
            ),
        )
        self.assertTrue(signature)

    def test_unconfigured_client_fails_closed_without_network(self):
        client = ZadarmaReadOnlyClient(api_key="", api_secret="")
        with patch("number_providers.zadarma.urlopen") as urlopen:
            with self.assertRaises(ZadarmaConfigurationError):
                client.list_countries()
            urlopen.assert_not_called()

    def test_country_code_validation(self):
        client = ZadarmaReadOnlyClient(api_key="key", api_secret="secret")
        with self.assertRaises(ValueError):
            client.list_country_directions("Portugal")

    def test_direction_id_validation(self):
        client = ZadarmaReadOnlyClient(api_key="key", api_secret="secret")
        with self.assertRaises(ValueError):
            client.list_available_numbers("pt-mobile")


if __name__ == "__main__":
    unittest.main()
