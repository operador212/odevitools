# Tax Records 2.0 — data lifecycle and privacy baseline

## Current implementation boundary

- Bank CSV content is parsed in memory. The import service stores normalized transaction fields, parser metadata, a SHA-256 file fingerprint, classification suggestions and an audit event; it does not store the original CSV bytes.
- A filename is retained as import metadata. Treat it as potentially personal data.
- No public API route, user authentication, customer workspace creation flow, production database, private object storage, or customer-facing deletion/export workflow is enabled by this branch.
- The current SHA-256 fingerprint is an idempotency aid, not encryption, anonymisation, or proof of ownership.

## Required before real customer onboarding

1. Establish a verified identity provider and server-side tenant membership. Never accept a tenant identifier from a browser request as proof of access.
2. Define a documented retention schedule for imports, transactions, audit events, backups and support records, with a lawful basis and clear user-facing privacy notice.
3. Implement authenticated export and deletion workflows, including dependent records, backups and legal retention exceptions. Deletion must be tested and auditable without retaining unnecessary financial details in audit metadata.
4. Encrypt traffic and managed database/storage at rest; keep credentials in the hosting provider's secret manager; restrict staff access and log privileged access.
5. Add rate limits, upload size/type limits, malware controls where relevant, CSRF protections for browser sessions, and operational alerting.
6. Complete a UK GDPR / Data Protection Act review and, where relevant, assess international transfers and Portugal/EU GDPR obligations before launch.

## Classification and tax safety

Bank descriptions and credits/debits are evidence, not tax conclusions. A bank credit must not automatically be treated as taxable income and a debit must not automatically be treated as a deductible expense. Users must be able to inspect, correct and retain source context for classifications. Jurisdiction packs in this branch contain metadata only; they do not calculate tax, VAT, National Insurance, Portuguese social security or withholding.

## Release gate

Do not enable public routes, connect a paid database, import real financial statements, or enable paid checkout until authentication, tenant isolation, retention/deletion, backup/restore, security testing and end-to-end fulfilment have been reviewed and approved.
