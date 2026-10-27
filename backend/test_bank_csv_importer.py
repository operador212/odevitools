import unittest

from bank_csv_importer import parse_bank_csv


class BankCsvImporterTests(unittest.TestCase):
    def test_groups_platform_income_and_monthly_movement(self):
        csv_text = """Date,Description,Amount
01/04/2026,UBER EATS PAYOUT,120.50
05/04/2026,DELIVEROO PAYOUT,80.00
06/04/2026,PETROL STATION,-20.00
"""
        result = parse_bank_csv(csv_text, "UK")
        self.assertEqual(result["transactions_count"], 3)
        self.assertEqual(result["totals_by_counterparty"]["Uber Eats"], "120.50")
        self.assertEqual(result["totals_by_counterparty"]["Deliveroo"], "80.00")
        self.assertEqual(result["net_movement_by_month"]["2026-04"], "180.50")

    def test_supports_credit_and_debit_columns(self):
        csv_text = """Data,Descricao,Credit,Debit
01/05/2026,JUST EAT PAYOUT,"150,00",
02/05/2026,Petrol,,25.50
"""
        result = parse_bank_csv(csv_text, "PT")
        self.assertEqual(result["transactions_count"], 2)
        self.assertEqual(result["transactions"][0]["amount"], "150.00")
        self.assertEqual(result["transactions"][1]["amount"], "-25.50")
        self.assertEqual(result["jurisdiction"], "PT")

    def test_currency_column_overrides_jurisdiction_default(self):
        csv_text = """Date,Description,Amount,Currency
01/06/2026,UBER EATS PAYOUT,120.50,EUR
"""
        result = parse_bank_csv(csv_text, "UK")
        self.assertEqual(result["transactions"][0]["currency"], "EUR")

    def test_portugal_defaults_to_eur_when_currency_is_not_in_export(self):
        csv_text = """Data;Descricao;Valor
01/06/2026;Transferencia bancaria;120,50
"""
        result = parse_bank_csv(csv_text, "PT")
        self.assertEqual(result["transactions"][0]["currency"], "EUR")

    def test_invalid_headers_fail_clearly(self):
        with self.assertRaises(ValueError):
            parse_bank_csv("foo,bar\na,b\n", "UK")


if __name__ == "__main__":
    unittest.main()
