# ODEVI Tax Records 2.0 — Architecture Decision Record

Status: Proposed for implementation
Date: 2026-11-06
Repository: operador212/odevitools

## Decision

Build an ODEVI-owned, modular bookkeeping and tax-records core on the existing Python/FastAPI stack. Do not embed or fork Akaunting, ERPNext, or Frappe Books in production at this stage. Use Akaunting as a product/UX reference only, pending written commercial licensing clarification. Reassess an ERPNext deployment only as a separate, isolated candidate if the product later needs full double-entry accounting and the GPLv3 compliance model is accepted.

This decision minimizes migration risk, preserves the existing ODEVI frontend/backend investment, and avoids importing a large PHP/Laravel or Frappe stack before the requirements are proven.

## Why not embed Akaunting now?

Akaunting 3.3.0's upstream LICENSE.txt is Business Source License 1.1. Its Additional Use Grant permits production use only within stated limits (no more than two users, one company, or one thousand invoices) and expressly excludes use as an “Accounting Service” where third parties access the accounting/invoicing functionality for their benefit. That definition directly conflicts with ODEVI's intended hosted multi-tenant bookkeeping service. The licence also restricts white-labelling; the Change License is GPLv3 four years after the version's publication (or the stated first-distribution anniversary, whichever comes first). Therefore, do not embed or fork this release for ODEVI's hosted product unless Akaunting grants a suitable commercial licence in writing. Re-check the exact LICENSE.txt for the specific version before any future use.

## Why not ERPNext now?

ERPNext is GPLv3 and is a much broader ERP than the first ODEVI product requires. A hosted deployment can be operated, but distributing modified/combined software and customer-specific deployments create compliance obligations that need a deliberate legal review. It also adds a separate Frappe/MariaDB deployment and operations burden. Keep it as a separately hosted evaluation candidate, not a production dependency.

## Product boundary

ODEVI Tax Records 2.0 is initially a bookkeeping preparation tool, not a tax return engine, tax adviser, or officially approved MTD product. It imports financial records, normalizes transactions, helps users categorize and review them, and produces traceable exports. Jurisdiction-specific tax calculations and government submissions are separate later modules, each requiring validated rules and compliance review.

## Target architecture

- Frontend: retain the current ODEVI+ static portal initially; add an authenticated app surface when identity is ready.
- API: retain FastAPI and split code into versioned routers/services.
- Database: PostgreSQL, with migrations (Alembic) and SQLAlchemy; no financial records in process memory or browser-only state.
- File storage: private object storage for uploaded statements and generated reports; random object keys, encryption, retention policy, deletion workflow, and signed short-lived download URLs.
- Background processing: queue-backed import jobs for large files; status and retry semantics.
- Authentication: verified user identity; all business records scoped to tenant and user; deny-by-default authorization.
- Auditability: append-only event history for imports, edits, category changes, exports, and deletions.
- Financial arithmetic: Decimal only; currency is explicit on every amount; never aggregate unlike currencies without a dated FX conversion record.
- Idempotency: source-file fingerprint plus transaction fingerprints; duplicate candidates are reviewable, not silently discarded when ambiguity exists.
- Export: CSV first, then PDF; exports must contain the user's imported/edited records, not sample data.
- AI: suggestions only, with confidence and explanation; no autonomous posting, value changes, or tax determinations.

## Core data model (initial)

- Tenant: legal/business workspace, default country, base currency, timezone.
- User and TenantMembership: identity and role (owner, accountant, reviewer, read-only).
- JurisdictionProfile: country, tax year calendar, locale, tax currency, rule-pack version.
- FinancialAccount: institution/provider, account identifier token, currency.
- ImportJob: tenant, source, file fingerprint, status, errors, parser version, timestamps.
- SourceDocument: private object key, MIME type, hash, retention and deletion state.
- Transaction: account, date, description, signed Decimal amount, currency, counterparty, source row, status.
- TransactionSplit: one transaction split into categorized portions.
- Category: tenant category mapped optionally to a jurisdiction-specific tax treatment.
- ClassificationSuggestion: category, confidence, rule/model version, rationale, reviewed state.
- ReconciliationMatch: linked statement and platform records, match method, confidence.
- AuditEvent: actor, action, entity, before/after references, timestamp.
- ExportJob: filter snapshot, format, status, output object key, expiry.

## Country strategy

Keep the global ledger country-neutral. Country packs must be versioned and must not alter the underlying source transaction:
- UK: tax-year calendar and HMRC-related categories/reports; MTD/API work only after separate official requirements and testing.
- Portugal: calendar-year and local reporting concepts; validate against official Portuguese requirements before implementing tax calculations.
- Other countries: add only through independent country packs with test fixtures and a maintained rules owner.

Never infer tax residence or filing obligations from a user's location. The user selects and confirms their jurisdiction profile.

## Security and privacy baseline

- No bank statement contents, credentials, API keys, or secrets in Git.
- Private storage only; no public buckets or predictable file paths.
- Encryption in transit and at rest; managed secrets; least-privilege service access.
- Strict upload limits, MIME/content validation, malware scanning where supported, CSV formula-injection neutralization on exports, and safe PDF parsing.
- Tenant isolation tests on every read/write endpoint.
- Data export and deletion workflows; retention periods disclosed before upload.
- Do not use customer financial data to train models.
- Paid features remain disabled until durable fulfilment, idempotency, access control, retention/deletion, and end-to-end tests pass.

## Migration approach

1. Keep existing tax-assistant-demo as a clearly labelled legacy prototype; do not silently repurpose or delete it.
2. Add a new /tax-records/ app behind a feature flag and test environment.
3. Build schema and importer first; migrate only synthetic fixtures initially.
4. Validate export against imported source rows and user edits.
5. Run tenant isolation, backup/restore, and deletion tests.
6. Pilot with explicit opt-in and synthetic or consented test data.
7. Replace the old entry point only after acceptance criteria pass.

## Definition of done for first usable release

- User can create a workspace and choose a jurisdiction profile.
- User can import supported CSV files and see a preview before committing.
- Every accepted transaction preserves original source row, amount, date, currency, and provenance.
- Duplicates are flagged with an explanation and can be resolved by the user.
- User can edit categories and splits; every edit is auditable and reversible.
- Reloading or signing in on another device preserves the records.
- CSV export reproduces the selected real records and edits; PDF export is tested separately.
- Two tenants cannot read, modify, or export one another's data.
- User can delete uploaded source documents and request deletion of workspace data.
- Tests cover UK/Portugal fixtures, decimal/currency edge cases, malformed files, and security boundaries.
- No claim of tax calculation, MTD compatibility, or tax filing until separately validated.

## Immediate next technical milestone

Create a proof-of-concept branch that introduces PostgreSQL schema/migrations, tenant-scoped models, and a CSV import preview/commit API behind a feature flag. Do not deploy it to production or enable Stripe until security and end-to-end acceptance tests pass.
