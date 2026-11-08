import unittest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from tax_records.models import Base, Tenant, FinancialAccount, FinancialTransaction, Category, TransactionSplit

class TaxRecordsModelTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
    def tearDown(self):
        self.engine.dispose()
    def test_decimal_transaction_is_persisted(self):
        with Session(self.engine) as session:
            tenant = Tenant(name="Workspace")
            session.add(tenant); session.flush()
            account = FinancialAccount(tenant_id=tenant.id, display_name="Bank", currency="GBP")
            tx = FinancialTransaction(tenant_id=tenant.id, account=account, transaction_date=date(2026, 4, 6),
                description="Delivery payout", amount=Decimal("125.45"), currency="GBP")
            session.add(tx); session.commit()
            stored = session.scalar(select(FinancialTransaction).where(FinancialTransaction.tenant_id == tenant.id))
            self.assertEqual(stored.amount, Decimal("125.45"))
    def test_tenant_filter_isolates_workspaces(self):
        with Session(self.engine) as session:
            a, b = Tenant(name="A"), Tenant(name="B")
            session.add_all([a, b]); session.flush()
            session.add(FinancialTransaction(tenant_id=a.id, transaction_date=date(2026, 5, 1),
                description="Income", amount=Decimal("1.00"), currency="GBP"))
            session.commit()
            self.assertEqual(session.scalars(select(FinancialTransaction).where(FinancialTransaction.tenant_id == b.id)).all(), [])
    def test_splits_preserve_decimal(self):
        with Session(self.engine) as session:
            tenant = Tenant(name="Workspace"); session.add(tenant); session.flush()
            category = Category(tenant_id=tenant.id, code="fuel", label="Fuel")
            tx = FinancialTransaction(tenant_id=tenant.id, transaction_date=date(2026, 5, 1),
                description="Fuel", amount=Decimal("-20.00"), currency="GBP")
            session.add_all([category, tx]); session.flush()
            split = TransactionSplit(transaction_id=tx.id, category_id=category.id,
                amount=Decimal("-20.00"), currency="GBP")
            session.add(split); session.commit()
            self.assertEqual(session.get(TransactionSplit, split.id).amount, Decimal("-20.00"))

if __name__ == "__main__":
    unittest.main()
