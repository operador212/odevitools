import unittest
from unittest.mock import patch
from document_intelligence import analyze_document, MAX_DOCUMENT_BYTES, MAX_EXTRACTED_CHARS

class DocumentIntelligenceTests(unittest.TestCase):
    def test_classifies_invoice_and_sanitizes_filename(self):
        result = analyze_document("../../invoice.txt", b"Invoice number INV-100\nTotal GBP 120.00")
        self.assertEqual(result.document_type, "invoice")
        self.assertEqual(result.filename, "invoice.txt")
        self.assertEqual(len(result.sha256), 64)

    def test_classifies_bank_statement(self):
        result = analyze_document("statement.csv", b"Date,Description,Amount\nStatement period,June")
        self.assertEqual(result.document_type, "bank_statement")

    def test_rejects_empty_oversized_and_unsupported_files(self):
        for name, data in (("empty.txt", b""), ("large.txt", b"x" * (MAX_DOCUMENT_BYTES + 1)), ("image.png", b"no")):
            with self.subTest(name=name), self.assertRaises(ValueError):
                analyze_document(name, data)

    def test_rejects_non_utf8_text(self):
        with self.assertRaises(ValueError):
            analyze_document("bad.txt", b"\xff\xfe")

    def test_scanned_pdf_is_flagged_for_ocr(self):
        with patch("document_intelligence._extract_pdf", return_value=("", [])):
            result = analyze_document("scan.pdf", b"%PDF-fake")
        self.assertTrue(result.needs_ocr)
        self.assertTrue(any("OCR" in warning for warning in result.warnings))

    def test_truncates_long_text(self):
        result = analyze_document("long.txt", ("a" * (MAX_EXTRACTED_CHARS + 50)).encode())
        self.assertEqual(result.characters_extracted, MAX_EXTRACTED_CHARS)
        self.assertTrue(result.warnings)

if __name__ == "__main__":
    unittest.main()
