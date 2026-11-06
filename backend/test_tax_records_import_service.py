import unittest
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from tax_records.models import Base, AuditEvent, FinancialAccount, FinancialTransaction, ImportJob, Tenant
from tax_records.import_service import import_bank_csv


CSV = """Date,Description,Amount
01/04/2026,UBER EATS PAYOUT,120.50
02/04/2026,PETROL STATION,-20.00
"""


class TaxRecordsImportServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            self.a = Tenant(name="Workspace A")
            self.b = Tenant(name="Workspace B")
            session.add_all([self.a, self.b])
            session.flush()
            self.account = FinancialAccount(tenant_id=self.a.id, display_name="Bank", currency="GBP")
            session.add(self.account)
            session.commit()
            self.tenant_a_id = self.a.id
            self.tenant_b_id = self.b.id
            self.account_a_id = self.account.id

    def tearDown(self):
        self.engine.dispose()

    def test_import_persists_transactions_and_audit(self):
        with Session(self.engine) as session:
            result = import_bank_csv(session, tenant_id=self.tenant_a_id, filename="bank.csv",
                csv_text=CSV, jurisdiction="UK", account_id=self.account_a_id)
            session.commit()
            self.assertEqual(result["transactions_added"], 2)
            rows = session.scalars(select(FinancialTransaction).where(
                FinancialTransaction.tenant_id == self.tenant_a_id)).all()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0].amount, Decimal("120.50"))
            self.assertEqual(len(session.scalars(select(AuditEvent).where(
                AuditEvent.tenant_id == self.tenant_a_id)).all()), 1)

    def test_replaying_same_file_is_idempotent(self):
        with Session(self.engine) as session:
            first = import_bank_csv(session, tenant_id=self.tenant_a_id, filename="bank.csv",
                csv_text=CSV, jurisdiction="UK")
            session.commit()
            second = import_bank_csv(session, tenant_id=self.tenant_a_id, filename="bank.csv",
                csv_text=CSV, jurisdiction="UK")
            session.commit()
            self.assertFalse(first["idempotent_replay"])
            self.assertTrue(second["idempotent_replay"])
            self.assertEqual(second["transactions_added"], 0)
            self.assertEqual(len(session.scalars(select(FinancialTransaction)).all()), 2)

    def test_exact_transaction_duplicate_is_flagged_not_deleted(self):
        with Session(self.engine) as session:
            import_bank_csv(session, tenant_id=self.tenant_a_id, filename="one.csv",
                csv_text=CSV, jurisdiction="UK")
            session.commit()
            result = import_bank_csv(session, tenant_id=self.tenant_a_id, filename="two.csv",
                csv_text=CSV + "\n", jurisdiction="UK")
            session.commit()
            self.assertEqual(result["possible_duplicates"], 2)
            statuses = session.scalars(select(FinancialTransaction.review_status).where(
                FinancialTransaction.tenant_id == self.tenant_a_id).order_by(FinancialTransaction.id)).all()
            self.assertEqual(statuses.count("possible_duplicate"), 2)

    def test_cannot_attach_another_tenants_account(self):
        with Session(self.engine) as session:
            with self.assertRaisesRegex(ValueError, "does not belong"):
                import_bank_csv(session, tenant_id=self.tenant_b_id, filename="bank.csv",
                    csv_text=CSV, jurisdiction="UK", account_id=self.account_a_id)

    def test_unknown_tenant_is_rejected(self):
        with Session(self.engine) as session:
            with self.assertRaisesRegex(ValueError, "does not exist"):
                import_bank_csv(session, tenant_id="not-a-tenant", filename="bank.csv",
                    csv_text=CSV, jurisdiction="UK")


if __name__ == "__main__":
    unittest.main()
