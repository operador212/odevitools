# Authentication and tenant authorization boundary

## Implemented in this branch

- TenantMembership stores an identity-provider issuer and opaque provider subject, tenant, role and active flag. Email addresses are not used as identity keys.
- VerifiedPrincipal is an immutable value object representing a subject only after a trusted identity adapter has validated its token.
- require_tenant_access resolves active membership server-side and enforces viewer/contributor/owner role levels. Missing membership, wrong issuer, wrong subject and insufficient role fail closed.
- Alembic migration 0002_tenant_memberships creates the membership table and role constraint.

## Not implemented / release blockers

- No identity provider has been selected or connected. No login, logout, MFA, password reset, token verification, session cookie, CSRF handling or account recovery is implemented.
- VerifiedPrincipal must only be constructed by a future server-side adapter after signature, issuer, audience, expiry and nonce/session checks. It must never be populated from request JSON, query parameters, arbitrary user-ID headers, or browser local storage.
- Existing import/review services are internal functions and are not yet wrapped by authenticated API dependencies. Do not mount routes until every service call requires a verified principal and an authorized tenant access result.
- Tenant membership provisioning, invitation acceptance, ownership transfer, support access and account deletion still need explicit workflows and tests.

## Roles

- viewer: read-only access.
- contributor: import and review financial records.
- owner: manage workspace membership and settings.

Role policy is a starting boundary and must be reviewed before customer launch. No default or anonymous membership is granted.
