"""OIDC JWT verification adapter for a standards-compliant identity provider.

No provider is hard-coded. Configure issuer, audience and JWKS URL in the server
environment. This module does not implement passwords or issue tokens.
"""
from __future__ import annotations
import os
from functools import lru_cache
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import InvalidTokenError
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError
from tax_records.access import VerifiedPrincipal

_bearer = HTTPBearer(auto_error=False)

@lru_cache(maxsize=4)
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_jwk_set=True, lifespan=300, timeout=5)

def verify_oidc_access_token(token: str, *, issuer: str, audience: str, jwks_url: str,
                             jwks_client: PyJWKClient | None = None) -> VerifiedPrincipal:
    """Verify signature and standard claims; return only a verified issuer/subject pair."""
    if not all(value and value.strip() for value in (issuer, audience, jwks_url, token)):
        raise ValueError("OIDC issuer, audience, JWKS URL and token are required")
    client = jwks_client or _jwks_client(jwks_url)
    signing_key = client.get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "ES256"],
        audience=audience,
        issuer=issuer,
        options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        leeway=30,
    )
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise InvalidTokenError("Token subject is missing")
    return VerifiedPrincipal(subject=subject, issuer=issuer)

async def get_current_principal(request: Request) -> VerifiedPrincipal:
    """FastAPI dependency. Tokens are accepted only from the Authorization header."""
    credentials: HTTPAuthorizationCredentials | None = await _bearer(request)
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticação necessária",
                            headers={"WWW-Authenticate": "Bearer"})
    issuer = os.getenv("OIDC_ISSUER", "").strip()
    audience = os.getenv("OIDC_AUDIENCE", "").strip()
    jwks_url = os.getenv("OIDC_JWKS_URL", "").strip()
    if not all((issuer, audience, jwks_url)):
        raise HTTPException(status_code=503, detail="Autenticação OIDC ainda não está configurada")
    try:
        return verify_oidc_access_token(credentials.credentials, issuer=issuer,
                                        audience=audience, jwks_url=jwks_url)
    except PyJWKClientConnectionError as exc:
        raise HTTPException(status_code=503, detail="Serviço de autenticação temporariamente indisponível") from exc
    except PyJWKClientError as exc:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado",
                            headers={"WWW-Authenticate": "Bearer"}) from exc
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado",
                            headers={"WWW-Authenticate": "Bearer"}) from exc
    except Exception as exc:
        # Fail closed; distinguish unexpected infrastructure faults from bad credentials.
        raise HTTPException(status_code=503, detail="Não foi possível validar a autenticação") from exc
