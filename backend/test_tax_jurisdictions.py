import unittest
from tax_records.jurisdictions import get_jurisdiction_pack, validate_tax_year

class JurisdictionPackTests(unittest.TestCase):
    def test_uk_metadata_and_valid_tax_year(self):
        pack = get_jurisdiction_pack("uk")
        self.assertEqual(pack.currency, "GBP")
        self.assertEqual(validate_tax_year("UK", "2025-26"), "2025-26")

    def test_rejects_non_consecutive_uk_year(self):
        with self.assertRaisesRegex(ValueError, "consecutive"):
            validate_tax_year("UK", "2025-27")

    def test_portugal_year(self):
        self.assertEqual(get_jurisdiction_pack("PT").currency, "EUR")
        self.assertEqual(validate_tax_year("PT", "2025"), "2025")

    def test_rejects_unknown_jurisdiction(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            get_jurisdiction_pack("ES")

    def test_rejects_bad_year_format(self):
        with self.assertRaisesRegex(ValueError, "Invalid tax-year"):
            validate_tax_year("PT", "FY2025")

if __name__ == "__main__":
    unittest.main()
