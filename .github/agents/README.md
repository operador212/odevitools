# ODEVI+ Agent Core

The first release uses deterministic checks and does not require an external AI API key.

## Agents
- **Auditor:** checks required public pages and local HTML links/assets.
- **QA Tester:** runs the backend unittest regression suite on pushes, pull requests and scheduled runs.
- **Production smoke checker:** checks the public site and backend root response on daily scheduled/manual runs.
- **Coordinator:** GitHub Actions combines the checks and stores an audit report artifact.

## Safety boundary
This release is read-only. It does not edit files, merge pull requests, deploy code, touch Stripe, or access secrets. A failed check is reported by a failed workflow and its artifact. Repairs should be made on isolated branches and proposed through pull requests. Do not add unrestricted auto-merge or production write credentials.

## Schedule
Daily at 06:17 UTC, plus push, pull request and manual dispatch.

## Next stages
1. Add browser-based journeys for each public tool.
2. Add backend endpoint contract tests and authenticated test-mode Stripe checkout.
3. Add issue deduplication and structured repair proposals.
4. Add an AI repair worker only after a provider/API secret is configured in GitHub Actions Secrets; it must open PRs, never write directly to main.
