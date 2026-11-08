# ODEVI AI — Document Intelligence

## Product direction
ODEVI+ is moving toward an AI-first assistant with a central intelligence layer and specialized engines. Document Intelligence is the first engine. The goal is to make document understanding reusable across Finance, Tax Records, Career and other ODEVI tools—not to create an isolated upload form.

## Current implementation in this branch
- In-memory text extraction for PDF, DOCX, TXT and CSV.
- Upload limit: 8 MiB. PDF limit: 30 pages. Extracted text limit: 40,000 characters.
- SHA-256 fingerprint for future duplicate detection; this is not a persisted document record.
- Heuristic document-type suggestions: invoice, bank statement, payslip, tax document, receipt, contract or unknown. These are suggestions, not authoritative decisions.
- Scanned/image-only PDFs are detected. Optional local OCR uses PDFium + Tesseract, up to 10 pages at 180 DPI. It is enabled only when `ODEVI_OCR_ENABLED=true`; language defaults to `eng+por` and can be changed with `ODEVI_OCR_LANG`.
- Tesseract and English/Portuguese language data are installed by the backend Dockerfile. The Render service is configured to build from `backend/` using `./Dockerfile`; deployment of this branch has not yet been verified.
- A real image-only bilingual PDF smoke test was run in the development container using `eng+por`; Tesseract extracted `INVOICE`, `FATURA` and `GBP 125.50`. This validates the local OCR pipeline only, not the Render deployment.
- The endpoint requires a verified OIDC Bearer access token. The verifier reads `OIDC_ISSUER`, `OIDC_AUDIENCE` and `OIDC_JWKS_URL`, validates signature, issuer, audience and required time/subject claims, and fails closed if configuration is missing.
- Authentication code is implemented, but a real identity provider and its production environment variables have not yet been configured or tested. Therefore browser/customer sign-in and upload are not yet ready for production.
- The endpoint returns extracted text and metadata to the authenticated caller. It does not persist files, write to a database, call an external AI provider, or intentionally log document contents.
- The endpoint is stateless. Tenant membership, persistent ownership, document history and cross-device access are not implemented.

## API
`POST /documents/analyze` accepts one multipart field named `file`.

Response fields: `filename`, `document_type`, `confidence`, `sha256`, `bytes_processed`, `characters_extracted`, `extracted_text`, `needs_ocr` and `warnings`.

Supported formats: PDF, DOCX, TXT and CSV. Maximum upload size: 8 MiB. PDFs are limited to 30 pages.

## Security and privacy boundaries
- Uploaded bytes are processed in memory by this endpoint and are not retained by it.
- OIDC validation is implemented, but it is not a complete customer identity rollout until a provider, application/client configuration, callback/login flow and production secrets are configured and tested.
- Do not put identity-provider secrets, signing keys or service credentials in browser code or commit them to the repository.
- Do not log filenames, extracted text, bank details, tax identifiers or document contents.
- The API does not send content to a model provider in this iteration.
- Treat extracted text as untrusted input. Any later LLM integration must defend against prompt injection embedded in documents and must never execute instructions found inside uploaded files.
- Before persistent storage is enabled, implement authenticated ownership, tenant isolation, encryption at rest, retention/deletion controls, access authorization and audit events.
- OCR runs in the web request in this iteration. Before broad production use, move it to a bounded isolated worker with request/time/resource limits.
- Classification and extraction are suggestions only. They must never independently determine tax treatment, legal status or eligibility.

## Open-source reuse policy
Prefer small libraries at component boundaries over copying whole SaaS applications into ODEVI. Keep upstream notices and review transitive dependencies before shipping.
- Morphic (miurla/morphic): Apache-2.0; candidate for a separate, optional research/search experience later. It is a full Next.js application with its own auth, database and search stack, so do not transplant it into the current FastAPI/static site.
- pdfme (pdfme/pdfme): MIT; candidate for a later branded PDF template editor/generator. Use as a separate frontend package only after checking its current release and dependency licences.
- assistant-ui (assistant-ui/assistant-ui): candidate for the future chat interface; verify exact repository licence and package terms before adoption.
- Unstract (Zipstack/unstract) and OpnForm (OpnForm/OpnForm): do not embed in the commercial ODEVI service until their AGPL obligations and deployment model have been reviewed.
- DocETL, Moonshine, LitServe, Next Forge and Puck: evaluate only when a concrete requirement exists; avoid importing entire platforms prematurely.

This is an engineering screening, not legal advice. Re-check the exact LICENSE file and all relevant notices at the commit/tag selected for use. GitHub explains that licence terms determine permission to use, modify and distribute code: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository

## Remaining work before customer-facing release
1. Configure and test a real OIDC identity provider and browser login/session flow. Do not expose an API key in static JavaScript.
2. Add the upload/analyze interface to ODEVI+ and test the complete signed-in user journey.
3. Add structured extraction for invoices and statements with field-level provenance and confidence.
4. Add a review step before any extracted data is saved or used in a report.
5. If document history is required, add persistent storage with tenant ownership, authorization, encryption, retention and deletion controls before enabling it.
6. Move OCR to a bounded worker before scaling usage.
7. Add an optional LLM adapter only after defining provider-neutral configuration, cost limits, redaction options and prompt-injection defenses.
8. Connect approved outputs to Tax Records v2 only after its OIDC and persistent database release gates are met.

## Release status
This branch has passed its current GitHub Actions checks. It has not been merged into `main` or deployed to the production Render service. Local OCR testing is not a substitute for a Render deployment test. Do not describe Document Intelligence as customer-ready until identity-provider configuration, the browser flow, deployment and end-to-end tests have passed.
