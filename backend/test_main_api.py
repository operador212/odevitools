import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from main import validate_download_url, validate_tax_checkout_session


class DownloadUrlValidationTests(unittest.TestCase):
    def test_accepts_supported_youtube_and_tiktok_hosts(self):
        for url in (
            "https://www.youtube.com/watch?v=example",
            "https://youtu.be/example",
            "https://m.youtube.com/watch?v=example",
            "https://www.tiktok.com/@creator/video/123",
            "https://vm.tiktok.com/example",
        ):
            with self.subTest(url=url):
                self.assertIn(validate_download_url(url).scheme, {"http", "https"})

    def test_rejects_lookalike_hosts_and_non_http_schemes(self):
        for url in (
            "https://youtube.com.evil.example/watch?v=1",
            "https://notyoutube.com/",
            "file://youtube.com/video.mp4",
            "javascript://youtube.com/",
        ):
            with self.subTest(url=url):
                with self.assertRaises(HTTPException):
                    validate_download_url(url)


class TaxCheckoutSessionValidationTests(unittest.TestCase):
    def make_session(self, **overrides):
        values = {
            "metadata": {
                "product": "odevi_tax_report",
                "jurisdiction": "UK",
                "report_id": "report-test-123",
            },
            "mode": "payment",
            "currency": "gbp",
            "amount_total": 599,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_accepts_exact_odevi_payment_session(self):
        metadata = validate_tax_checkout_session(self.make_session())
        self.assertEqual(metadata["report_id"], "report-test-123")

    def test_rejects_wrong_product_currency_or_amount(self):
        cases = (
            {"metadata": {"product": "other", "jurisdiction": "UK", "report_id": "r"}},
            {"currency": "eur"},
            {"amount_total": 600},
            {"mode": "subscription"},
        )
        for override in cases:
            with self.subTest(override=override):
                with self.assertRaises(HTTPException):
                    validate_tax_checkout_session(self.make_session(**override))

    def test_rejects_missing_report_id_or_invalid_jurisdiction(self):
        cases = (
            {"metadata": {"product": "odevi_tax_report", "jurisdiction": "UK"}},
            {"metadata": {"product": "odevi_tax_report", "jurisdiction": "US", "report_id": "r"}},
        )
        for override in cases:
            with self.subTest(override=override):
                with self.assertRaises(HTTPException):
                    validate_tax_checkout_session(self.make_session(**override))


if __name__ == "__main__":
    unittest.main()
