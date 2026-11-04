# ODEVI+ Agent Core

The ODEVI+ agents run automatically on pushes, pull requests, and once daily. The first release uses deterministic checks and does not need an external AI API key.

## Agent responsibilities

- **Site Auditor:** checks required public pages and local HTML links/assets.
- **API Guardian:** installs backend dependencies and runs the backend regression suite.
- **Browser QA:** opens the main public pages in Chromium at mobile (390px) and desktop (1365px) widths; checks HTTP status, JavaScript exceptions, horizontal overflow, and UK/Portugal tax-jurisdiction selector interactions.
- **Production Sentinel:** checks that https://odevitools.com/ serves HTML and that https://odevi-backend.onrender.com/ returns HTTP 200 with the ODEVI+ service identity. Runs on main pushes and daily/manual checks.
- **Incident Reporter:** when browser QA fails, creates or updates one deduplicated GitHub issue with the test evidence and a concrete repair checklist.
- **Coordinator:** GitHub Actions schedules the agents, fails the run when a quality gate fails, and retains audit artifacts.

## What happens when something breaks

1. The failing agent records the exact page/check and evidence in a workflow artifact.
2. The Incident Reporter opens or updates the single active QA incident.
3. A correction must be made on an isolated branch, reviewed, and tested through a pull request.
4. Production changes are deployed only after the checks pass and the pull request is merged.

## Safety boundary

The current agents monitor, test, and report; they do not yet autonomously rewrite application code, merge pull requests, or change Stripe/Render configuration. This is intentional: an unreviewed code-writing agent could damage the public site, expose customer data, or affect payments. The agents do not read payment secrets. Never add unrestricted auto-merge or production credentials to a repair workflow.

## Schedule

Daily at 06:17 UTC, plus push, pull request, and manual dispatch.

## Next stages

1. Expand browser tests to each interactive tool and complete end-to-end workflows.
2. Add backend endpoint contract tests and authenticated Stripe test-mode checkout.
3. Add a constrained AI repair worker only after an approved model/provider credential is configured as a GitHub Actions secret. It must work on isolated branches, open pull requests, and never write directly to main.
