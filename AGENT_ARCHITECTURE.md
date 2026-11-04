# ODEVI+ Autonomous Agent Architecture (v1)

## Operating model

The system is split into independent agents. Every agent emits structured evidence; the coordinator combines results and enforces release policy.

| Agent | Responsibility | Authority |
|---|---|---|
| Coordinator | Schedules jobs, gathers evidence, applies release gates | Read-only orchestration |
| Site/API Auditor | Static links, backend unit tests, API contracts | Read-only |
| Browser QA | Mobile/desktop journeys, file upload and result rendering | Read-only |
| Payment Guardian | Stripe test-mode checkout, payment-status and entitlement checks | Test mode only; no live charges |
| Document Guardian | CSV/PDF fixtures, parser coverage, OCR readiness and malformed-file handling | Read-only |
| Production Sentinel | Public site/API health and error-budget checks | Read-only |
| Repair Agent | Diagnoses failures and proposes isolated patches | Branch + pull request only |
| Release Agent | Verifies all required checks and deploys | Protected main only; rollback required |

## High-autonomy safety policy

1. Agents may diagnose, edit an isolated branch, run tests and open/update a pull request.
2. Low-risk changes may be auto-merged only after all required checks pass, the change is classified as low risk, and branch protection/repository settings permit it.
3. Payment, authentication, privacy, data-retention, tax logic, database migrations, dependency upgrades and production secrets are always high-risk and require human approval.
4. No agent may access live Stripe secret keys or customer documents.
5. Pull-request workflows run with read-only permissions and no production secrets. Never use `pull_request_target` to execute pull-request code.
6. Production deployment must be gated by green browser, backend, document and payment tests. Failed checks block release.
7. Every automated change must include a diff, test evidence, risk classification and rollback plan.

## Current implementation status

- Existing deterministic auditor, browser QA, API tests, production sentinel and incident reporter are active.
- This v1 adds a machine-readable coordinator report and a scheduled orchestration workflow.
- Autonomous AI code repair is not enabled yet. It requires an approved model API credential stored as a GitHub Actions secret (never committed to the repository), a strict patch sandbox, and a pull-request-only worker.
- The paid tax flow is currently CSV-only. PDF/OCR, durable report storage and guaranteed report delivery are not yet implemented. The payment/product must not be advertised as supporting those capabilities until end-to-end tests prove them.

## Required repository configuration

- Protect `main`; require the agent-core, backend, browser and document checks.
- Keep default workflow token permissions read-only; elevate permissions only in the incident/PR job that needs them.
- Enable automatic security updates and pin third-party Actions to verified full commit SHAs.
- Add the model API credential only after selecting the provider/model and monthly spending limit.
- Configure test-mode Stripe credentials in a dedicated GitHub Environment. Never expose them to fork pull requests.

## Budget guardrails

Start with GitHub-hosted runners and existing Render hosting. Add a model API only for repair tasks, cap requests and output tokens, and stop the worker when the monthly budget threshold is reached. Do not add a dedicated server until measured workload requires one.
