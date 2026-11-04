import unittest

from tax_report_builder import build_tax_report


def tx(date, description, amount, category, counterparty, currency="GBP", review=False):
    return {
        "date": date,
        "description": description,
        "amount": amount,
        "category": category,
        "counterparty": counterparty,
        "currency": currency,
        "needs_review": review,
        "matched_rule": "test_rule" if review else None,
    }


class TaxReportBuilderTests(unittest.TestCase):
    def test_combines_statements_and_removes_exact_duplicates(self):
        statement_a = {
            "jurisdiction": "UK",
            "skipped_rows": 0,
            "transactions": [
                tx("2026-04-01", "UBER EATS PAYOUT", "100.00", "platform_income", "Uber Eats"),
                tx("2026-04-02", "PETROL", "-20.00", "business_expense_candidate", "Unidentified", review=True),
            ],
        }
        statement_b = {
            "jurisdiction": "UK",
            "skipped_rows": 1,
            "transactions": [
                tx("2026-04-01", "UBER EATS PAYOUT", "100.00", "platform_income", "Uber Eats"),
                tx("2026-05-03", "DELIVEROO PAYOUT", "80.00", "platform_income", "Deliveroo"),
            ],
        }
        result = build_tax_report([statement_a, statement_b])
        self.assertEqual(result["source_statements_count"], 2)
        self.assertEqual(result["transactions_imported"], 4)
        self.assertEqual(result["exact_duplicates_removed"], 1)
        self.assertEqual(result["transactions_after_exact_deduplication"], 3)
        self.assertEqual(result["income_candidates_not_tax_confirmed"]["GBP:platform_income"], "180.00")
        self.assertEqual(result["net_bank_movement_by_month"]["GBP:2026-04"], "80.00")
        self.assertEqual(result["review_items_count"], 1)

    def test_mixed_jurisdictions_are_rejected(self):
        with self.assertRaises(ValueError):
            build_tax_report([
                {"jurisdiction": "UK", "transactions": []},
                {"jurisdiction": "PT", "transactions": []},
            ])

    def test_empty_input_is_rejected(self):
        with self.assertRaises(ValueError):
            build_tax_report([])

    def test_review_items_include_reason_and_unknowns_are_not_income(self):
        result = build_tax_report([{
            "jurisdiction": "UK",
            "transactions": [
                tx("2026-02-01", "Unidentified transfer", "500.00", "unknown", "Unidentified", "GBP", True),
            ],
        }])
        self.assertEqual(result["review_items_count"], 1)
        self.assertEqual(result["review_items"][0]["reason"], "test_rule")
        self.assertEqual(result["income_candidates_not_tax_confirmed"], {})
        self.assertEqual(result["expense_candidates_not_deductibility_confirmed"], {})

    def test_same_amount_with_different_descriptions_is_not_deduplicated(self):
        result = build_tax_report([{
            "jurisdiction": "UK",
            "transactions": [
                tx("2026-04-01", "UBER EATS PAYOUT", "100.00", "platform_income", "Uber Eats"),
                tx("2026-04-01", "DELIVEROO PAYOUT", "100.00", "platform_income", "Deliveroo"),
            ],
        }])
        self.assertEqual(result["transactions_after_exact_deduplication"], 2)
        self.assertEqual(result["exact_duplicates_removed"], 0)
        self.assertEqual(result["income_candidates_not_tax_confirmed"]["GBP:platform_income"], "200.00")

    def test_different_currencies_are_kept_separate(self):
        result = build_tax_report([
            {
                "jurisdiction": "UK",
                "transactions": [
                    tx("2026-01-01", "Credit", "100.00", "other_income_candidate", "Unidentified", "GBP", True),
                    tx("2026-01-02", "Credit", "100.00", "other_income_candidate", "Unidentified", "EUR", True),
                ],
            }
        ])
        self.assertEqual(result["income_candidates_not_tax_confirmed"]["GBP:other_income_candidate"], "100.00")
        self.assertEqual(result["income_candidates_not_tax_confirmed"]["EUR:other_income_candidate"], "100.00")


if __name__ == "__main__":
    unittest.main()
