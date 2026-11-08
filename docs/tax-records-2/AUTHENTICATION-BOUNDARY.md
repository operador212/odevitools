# Authentication and tenant authorization boundary

## Implemented in this branch

- TenantMembership stores identity-provider issuer and opaque provider subject, tenant, role and active flag. Email addresses are not identity keys.
- VerifiedPrincipal is created only after the server validates a signed access token.
- OIDC JWT validation uses provider JWKS, fixed RS256/ES256 algorithms, issuer, audience, expiry, issued-at and required claims.
- FastAPI dependencies enforce active membership and Viewer / Contributor / Owner role levels.
- The API exposes workspace listing and first-workspace creation for the authenticated identity. The server creates the owner membership using the verified issuer and subject.
- Transaction list, CSV import and review routes use tenant access dependencies. The browser cannot select another user's identity; tenant IDs are checked against membership.
- The static dashboard implements provider-neutral Authorization Code + PKCE and uses only public client configuration. It never contains a client secret or database URL.
- Automated tests cover workspace creation, listing, duplicate workspace prevention, invalid tax year and isolation by identity.

## External configuration still required

- No OIDC provider has been selected or configured for production. The public `tax-records-config.js` values `issuer`, `clientId` and `audience` are intentionally blank.
- Render must be configured with `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL` and `TAX_RECORDS_DATABASE_URL`.
- The provider must allow `https://odevitools.com/tax-records.html` as a redirect URI and `https://odevitools.com` as an origin.
- Login, logout and access-token session handling are implemented in the SPA, but real provider sign-in cannot be verified until provider configuration and real test credentials exist.
- No invitation, team-management or membership-recovery flow exists yet. Workspace creation is owner-only bootstrap for the authenticated subject.

## Security requirements

- Never construct VerifiedPrincipal from request JSON, query parameters, arbitrary user-ID headers or browser-supplied identity fields.
- Never expose provider client secrets, PostgreSQL URLs or signing private keys in static frontend files.
- All tenant-scoped queries must include tenant_id and must be reached only after tenant_access_dependency succeeds.
- Keep token lifetime short. The SPA stores the access token in sessionStorage for the current tab; protect the frontend against XSS and do not add untrusted scripts.
- Configure provider MFA / account recovery policies in the identity provider according to the business risk.
- Do not enable production customer data until a staging OIDC configuration, persistent database, backup/restore drill and cross-tenant security tests have passed.

See RELEASE-AND-SETUP.md for exact deployment steps and release gates.
