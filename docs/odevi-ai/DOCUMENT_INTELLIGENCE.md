# ODEVI AI — Document Intelligence

## Product direction
ODEVI+ is moving toward an AI-first assistant. The first capability is a reusable document-intelligence service, not a collection of unrelated upload forms.

## Iteration 1 (implemented in this branch)
- In-memory extraction for PDF, DOCX, TXT and CSV.
- File-size and PDF-page limits.
- SHA-256 fingerprint for future duplicate detection.
- Document-type suggestion: invoice, bank statement, payslip, tax document, receipt, contract or unknown.
- Scanned/image-only PDF detection flag (needs_ocr).
- Optional local OCR uses PDFium + Tesseract; the Render Docker image installs Tesseract with English and Portuguese language packs. OCR is enabled only with `ODEVI_OCR_ENABLED=true` and is limited to 10 pages at 180 DPI.
- A real image-only bilingual PDF smoke test was run in the development container using `eng+por`; Tesseract extracted `INVOICE`, `FATURA` and `GBP 125.50`. This validates the local OCR pipeline, not the Render deployment.
- Text output capped at 40,000 characters.
- No file storage, database writes, external AI calls or logging of extracted content.
- Suggestions are not authoritative classifications.

## API
POST /documents/analyze accepts one multipart field named file.
Response: filename, document_type, confidence, sha256, bytes_processed, characters_extracted, extracted_text, needs_ocr and warnings.
Supported formats: PDF, DOCX, TXT and CSV. Maximum upload size: 8 MiB. PDFs are limited to 30 pages.

## Security and privacy boundaries
- Uploaded bytes are processed in memory and are not retained by this endpoint.
- The current endpoint is guarded by `ODEVI_DOCUMENT_API_KEY`; without the server-side key it returns 503, and invalid/missing keys return 401. This is a temporary server-to-server gate, not customer authentication. Never expose this key in browser code.
- Do not log filenames, extracted text, bank details, tax identifiers or document contents.
- The API does not send content to a model provider in this iteration.
- Treat extracted text as untrusted input. Any later LLM integration must defend against prompt injection embedded in documents and must not execute instructions found inside uploaded files.
- A future persistence feature must add authenticated ownership, tenant isolation, retention/deletion controls, encryption at rest and audit events before storing documents.
- OCR is not included yet. Image-only PDFs are flagged rather than silently treated as empty valid documents.
- Classification is a suggestion only. It must never determine tax treatment or legal status.

## Open-source reuse policy
Prefer small libraries at a component boundary over copying whole SaaS applications into ODEVI. Keep upstream notices and review transitive dependencies before shipping.
- Morphic (miurla/morphic): Apache-2.0; candidate for a separate, optional research/search experience later. It is a full Next.js application with its own auth, database and search stack, so do not transplant it into the current FastAPI/static site.
- pdfme (pdfme/pdfme): MIT; candidate for a later branded PDF template editor/generator. Use as a separate frontend package only after checking its current release and dependency licences.
- assistant-ui (assistant-ui/assistant-ui): candidate for the future chat interface; verify exact repository licence and package terms before adoption.
- Unstract (Zipstack/unstract) and OpnForm (OpnForm/OpnForm): do not embed in the commercial ODEVI service until their AGPL obligations and deployment model have been reviewed.
- DocETL, Moonshine, LitServe, Next Forge and Puck: evaluate only when a concrete requirement exists; avoid importing entire platforms prematurely.

This is an engineering screening, not legal advice. Re-check the exact LICENSE file and all relevant notices at the commit/tag selected for use. GitHub explains that licence terms determine permission to use, modify and distribute code: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository

## Next iterations
1. Add OCR behind a bounded, isolated worker (not inside the web request).
2. Add schema-based extraction for invoices and statements with field-level provenance and confidence.
3. Add human review before any extracted data is saved or used in a report.
4. Add authenticated storage and retention/deletion controls.
5. Replace the temporary shared-key gate with verified per-user OIDC authentication and tenant authorization before enabling browser uploads. Do not store a shared API key in static JavaScript.
6. Add an optional LLM adapter with provider-neutral configuration, cost limits, redaction options and prompt-injection defenses.
6. Connect approved outputs to Tax Records v2 only after its OIDC and persistent database release gates are met.
