# ODEVI Tax Records 2.0 — Delivery Plan

## Workstream 0 — License and product decision
- [ ] Review exact Akaunting 3.3.0 LICENSE.txt, Additional Use Grant, and Change Date.
- [ ] Ask Akaunting for written clarification/commercial SaaS licence terms.
- [ ] Record ERPNext GPLv3 distribution/compliance implications.
- [ ] Decision gate: no third-party accounting core in production without a documented licence review.

## Workstream 1 — Data foundation
- [ ] Add PostgreSQL service and environment-specific configuration.
- [ ] Add SQLAlchemy models and Alembic migrations.
- [ ] Implement Tenant, Membership, JurisdictionProfile, FinancialAccount, SourceDocument, ImportJob, Transaction, Category, AuditEvent and ExportJob.
- [ ] Add tenant-scoped repository/service layer and authorization tests.
- [ ] Add backup/restore and deletion tests.

## Workstream 2 — Import pipeline
- [ ] Define canonical transaction schema using Decimal and explicit ISO currency.
- [ ] Build parser adapter interface; keep current CSV parser as first adapter.
- [ ] Add Wise, Revolut, Barclays, generic bank CSV fixtures only from synthetic or consented files.
- [ ] Add CSV encoding/delimiter/date/decimal detection with preview and explicit ambiguity warnings.
- [ ] Add idempotent import commit, duplicate candidate review, and audit events.
- [ ] Add CSV formula-injection protections to exports.

## Workstream 3 — Review and reporting
- [ ] Build transaction list, filters, category editing and splits.
- [ ] Add income/expense/cashflow reports without calling bank credits taxable income or debits deductible.
- [ ] Add real-data CSV export; ensure sample file is clearly separate.
- [ ] Add PDF export with test snapshots and downloadable output.
- [ ] Add import history and export history.

## Workstream 4 — International packs
- [ ] Keep ledger country-neutral.
- [ ] Implement UK profile and tax-year boundaries as a versioned pack.
- [ ] Implement Portugal profile and calendar-year conventions as a versioned pack.
- [ ] Add country-specific rules only with official sources and independent tests.
- [ ] Treat MTD and tax filing integrations as separate compliance projects.

## Workstream 5 — Operations and release
- [ ] Move production data to managed PostgreSQL and private object storage.
- [ ] Configure secrets, monitoring, rate limits, retention and incident response.
- [ ] Add end-to-end tests on mobile and desktop.
- [ ] Run tenant-isolation and security review.
- [ ] Pilot behind feature flag with explicit consent.
- [ ] Keep Stripe disabled until durable report fulfilment and all release gates pass.

## Non-goals for the first release
- No automated tax return calculation.
- No automatic HMRC/AT submission.
- No bank credential collection or screen scraping.
- No AI making unreviewed financial or tax changes.
- No multi-country tax calculations in a single first release.
