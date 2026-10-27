import unittest

from transaction_classifier import classify_transaction


class TransactionClassifierTests(unittest.TestCase):
    def test_known_delivery_platform_is_detected(self):
        result = classify_transaction("UBER EATS PAYOUT", 125.00)
        self.assertEqual(result.category, "platform_income")
        self.assertEqual(result.counterparty, "Uber Eats")
        self.assertFalse(result.needs_review)

    def test_platform_charge_is_not_called_income(self):
        result = classify_transaction("DELIVEROO SERVICE FEE", -12.50)
        self.assertEqual(result.category, "business_expense_or_charge")
        self.assertEqual(result.counterparty, "Deliveroo")

    def test_ambiguous_bank_transfer_requires_review(self):
        result = classify_transaction("BANK TRANSFER", 300.00)
        self.assertEqual(result.category, "other_income_candidate")
        self.assertTrue(result.needs_review)

    def test_unrecognized_description_is_flagged(self):
        result = classify_transaction("XYZ 00123", -5.00)
        self.assertEqual(result.category, "unknown")
        self.assertTrue(result.needs_review)

    def test_empty_description_is_flagged(self):
        result = classify_transaction("", 10.00)
        self.assertEqual(result.category, "unknown")
        self.assertTrue(result.needs_review)


if __name__ == "__main__":
    unittest.main()

    def test_own_account_transfer_is_separate_from_income(self):
        result = classify_transaction("TRANSFER BETWEEN ACCOUNTS", 500)
        self.assertEqual(result.category, "own_account_transfer")

    def test_fuel_is_only_an_expense_candidate(self):
        result = classify_transaction("PETROL STATION", -45.10)
        self.assertEqual(result.category, "business_expense_candidate")
        self.assertTrue(result.needs_review)

    def test_refund_is_flagged_for_reconciliation(self):
        result = classify_transaction("CARD REFUND", 19.99)
        self.assertEqual(result.category, "refund_or_reversal")
        self.assertTrue(result.needs_review)
