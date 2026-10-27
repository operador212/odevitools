# ODEVI+ — Download. Convert. Create.

## Tax report prototype (development branch)

The tax-report backend is under active development on `feature/odevi-tax-stripe-test`.
Do not treat it as production-ready and do not enable live Stripe payments yet.

### Current prototype capabilities
- Rule-based first-pass classification of common delivery-platform bank descriptions.
- CSV bank-statement parsing for UK and Portugal, including common amount/date formats.
- Multi-statement summary with exact duplicate removal and review flags.
- One-time Stripe Checkout foundation for £5.99.
- A paid CSV processing endpoint: `POST /tax/process-csv?session_id=...`, multipart field name `files`.
- Upload endpoint limits: maximum 10 CSV files, 5 MB per file; files are processed in memory and are not stored.

### Run automated tests
From the `backend` directory, run:

```sh
python -m unittest discover -v
```

### Important limitations
- The upload endpoint accepts CSV bank exports only; it does not parse PDF, scans, invoices or platform statements yet.
- The report is an accounting-preparation summary, not a tax return or tax calculation.
- Bank credits are not automatically taxable income and bank debits are not automatically deductible expenses.
- Duplicate detection currently removes exact matching date/description/amount/currency signatures only.
- The frontend checkout/upload flow is not connected yet.
- The report is returned as JSON in the HTTP response; it is not saved, rendered as a PDF, or emailed.
- A durable database, one-time fulfilment/idempotency, private report retrieval, retention/deletion controls, and end-to-end tests are required before production.
- Keep Stripe in test mode until the complete workflow and privacy/security review have passed.

### Required environment variables
- `STRIPE_SECRET_KEY` — Stripe test secret key during development.
- `STRIPE_WEBHOOK_SECRET` — webhook signing secret for the configured Stripe endpoint.

Never commit API keys, bank statements, customer documents, or personal financial data.
