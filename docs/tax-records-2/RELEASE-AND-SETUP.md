# Tax Records v2 — release and environment setup

This branch contains the application code. It is not production-enabled until the external prerequisites below are completed.

## 1. Identity provider (OIDC)

Choose an OIDC provider and create a **single-page application / public client** with Authorization Code + PKCE (S256). Configure the exact redirect URI:

- `https://odevitools.com/tax-records.html`

Allow the origin:

- `https://odevitools.com`

The SPA uses public values only: issuer URL, client ID and API audience. Do not create a client secret for the browser and never put a secret in `tax-records-config.js`.

Set these server-side Render environment variables on the ODEVI API service:

- `OIDC_ISSUER`: exact issuer from provider discovery metadata.
- `OIDC_AUDIENCE`: API audience configured at the provider.
- `OIDC_JWKS_URL`: provider's signing-key endpoint from discovery metadata.
- `TAX_RECORDS_DATABASE_URL`: private PostgreSQL connection URL (secret).

Then fill `tax-records-config.js` with the public `issuer`, `clientId`, `audience`, `apiBase` and exact `redirectUri`. The provider must allow the SPA's origin and redirect URI. The browser never receives the database URL or a client secret.

## 2. PostgreSQL

Provision a persistent PostgreSQL instance in Frankfurt (same region as the existing API). Use a paid persistent plan for production; free/trial database plans may expire and are not a safe permanent home for customer financial records. Do not migrate customer data until backups, access controls and retention policy have been reviewed.

Set `TAX_RECORDS_DATABASE_URL` using Render's **internal** connection string, not the external/public URL. Run migrations from the backend release environment:

```bash
cd backend
alembic -c alembic.ini upgrade head
```

The app's database engine is lazy; importing the API does not connect or run migrations automatically.

## 3. Frontend

Publish `tax-records.html` and `tax-records-config.js` on the same static origin. Configure the OIDC provider with the redirect URI above. The browser stores the short-lived access token in sessionStorage for the current tab session; protect the static site against XSS and keep third-party scripts to a minimum.

## 4. API routes

- `GET /tax-records/workspaces`: lists only the authenticated subject's active workspaces.
- `POST /tax-records/workspaces`: creates an owner workspace and a UK/PT jurisdiction profile for the verified subject.
- `GET /tax-records/{tenant_id}/transactions`: tenant-scoped, paginated read.
- `POST /tax-records/{tenant_id}/imports/csv?jurisdiction=UK|PT`: tenant-scoped CSV import (5 MB limit).
- `PATCH /tax-records/{tenant_id}/transactions/{transaction_id}/review`: tenant-scoped review status.

Every route requires a valid bearer access token and active membership. The server derives the user identity from verified token claims; it does not trust a browser-supplied user ID. The client-supplied tenant ID is checked against the verified issuer/subject membership before records are read or changed.

## 5. Tax calculations — intentionally not enabled

The UK and Portugal packs currently validate country and tax-year metadata only. The app can organize bank movements and record review decisions; it does not calculate taxable profit, Income Tax, National Insurance, VAT, Portuguese IRS, Social Security, withholding or a final return.

This separation is deliberate. A bank credit is not automatically business turnover, and a debit is not automatically a deductible expense. UK allowable expenses depend on business use, accounting method, capital allowances and special rules. Portugal Category B simplified-regime coefficients depend on the legal activity and applicable conditions; they cannot safely be selected from a bank description alone.

Before implementing calculations, each jurisdiction needs versioned rules with effective dates, activity/regime inputs, source citations, worked test vectors, independent accountant review and regression tests for each tax year. Until then, present categorized records as preparation data only and keep paid tax-report checkout disabled.

Official starting points:
- HMRC self-employment return guidance: https://www.gov.uk/guidance/help-with-self-employment-on-your-self-assessment-tax-return
- HMRC allowable expenses: https://www.gov.uk/expenses-if-youre-self-employed
- Portugal AT — trabalho por conta própria: https://info.portaldasfinancas.gov.pt/pt/apoio_ao_contribuinte/Cidadaos/Rendimentos/Trabalho_por_conta_propria/Paginas/default.aspx
- Portugal CIRS Article 31: https://diariodarepublica.pt/dr/legislacao-consolidada/lei/2014-70048167-70051805

## 6. Production release gates

Do not enable paid reports until all of these are true:

- OIDC provider configured and verified with real tokens.
- PostgreSQL provisioned with persistent backups and migrations applied.
- Membership bootstrap and cross-tenant isolation tests pass.
- Upload size, content validation, rate limits and abuse protection reviewed.
- Privacy notice, retention/deletion process and data-subject export tested.
- Tax rules reviewed by qualified professionals and tied to tax-year versions.
- End-to-end tests pass against staging and the deployed service is verified healthy.
