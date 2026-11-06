import unittest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from tax_records.models import Base, AuditEvent, FinancialTransaction, Tenant
from tax_records.review_service import list_transactions, update_transaction_review


class TaxRecordsReviewServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            a, b = Tenant(name="A"), Tenant(name="B")
            session.add_all([a, b])
            session.flush()
            tx = FinancialTransaction(
                tenant_id=a.id, transaction_date=__import__("datetime").date(2026, 4, 1),
                description="Payout", amount="100.00", currency="GBP", review_status="unreviewed"
            )
            session.add(tx)
            session.commit()
            self.a_id, self.b_id, self.tx_id = a.id, b.id, tx.id

    def tearDown(self):
        self.engine.dispose()

    def test_list_is_tenant_scoped_and_bounded(self):
        with Session(self.engine) as session:
            self.assertEqual([x.id for x in list_transactions(session, tenant_id=self.a_id)], [self.tx_id])
            self.assertEqual(list_transactions(session, tenant_id=self.b_id), [])
            self.assertEqual(list_transactions(session, tenant_id=self.a_id, limit=999), [session.get(FinancialTransaction, self.tx_id)])

    def test_cross_tenant_update_is_not_found_and_changes_nothing(self):
        with Session(self.engine) as session:
            with self.assertRaisesRegex(ValueError, "not found"):
                update_transaction_review(session, tenant_id=self.b_id, transaction_id=self.tx_id, review_status="confirmed")
            self.assertEqual(session.get(FinancialTransaction, self.tx_id).review_status, "unreviewed")
            self.assertEqual(session.scalars(select(AuditEvent)).all(), [])

    def test_update_changes_status_and_writes_audit(self):
        with Session(self.engine) as session:
            update_transaction_review(session, tenant_id=self.a_id, transaction_id=self.tx_id,
                review_status="confirmed", actor_user_id="verified-user-123")
            session.commit()
            event = session.scalar(select(AuditEvent))
            self.assertEqual(session.get(FinancialTransaction, self.tx_id).review_status, "confirmed")
            self.assertEqual(event.action, "transaction_review_status_changed")
            self.assertEqual(event.change_reference, "unreviewed->confirmed")
            self.assertEqual(event.actor_user_id, "verified-user-123")

    def test_invalid_status_rejected(self):
        with Session(self.engine) as session:
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                update_transaction_review(session, tenant_id=self.a_id, transaction_id=self.tx_id, review_status="tax_deductible")


if __name__ == "__main__":
    unittest.main()
