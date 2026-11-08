"""OIDC authentication for stateless document analysis.

The API validates a signed access token on every request. No shared secret is
placed in browser code. Configure OIDC_ISSUER, OIDC_AUDIENCE and OIDC_JWKS_URL.
"""
from __future__ import annotations
import os
from functools import lru_cache
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import InvalidTokenError, PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError

_bearer = HTTPBearer(auto_error=False)

@lru_cache(maxsize=4)
def _client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_jwk_set=True, lifespan=300, timeout=5)

async def get_document_principal(request: Request) -> dict[str, str]:
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
        key = _client(jwks_url).get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(credentials.credentials, key.key,
                            algorithms=["RS256", "ES256"], audience=audience,
                            issuer=issuer,
                            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
                            leeway=30)
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise InvalidTokenError("Missing subject")
        return {"issuer": issuer, "subject": subject}
    except PyJWKClientConnectionError as exc:
        raise HTTPException(status_code=503, detail="Serviço de autenticação temporariamente indisponível") from exc
    except (PyJWKClientError, InvalidTokenError) as exc:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado",
                            headers={"WWW-Authenticate": "Bearer"}) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Não foi possível validar a autenticação") from exc
