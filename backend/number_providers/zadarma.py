"""Read-only Zadarma API adapter for Portugal pilot validation.

No number can be purchased or renewed through this module. It only reads account
country/direction/availability metadata after credentials are configured.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ZadarmaConfigurationError(RuntimeError):
    """Raised when the Zadarma API credentials are not configured."""


class ZadarmaAPIError(RuntimeError):
    """Raised when Zadarma returns an error or the API cannot be reached."""


class ZadarmaReadOnlyClient:
    BASE_URL = "https://api.zadarma.com"
    TIMEOUT_SECONDS = 10

    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        self.api_key = api_key or os.getenv("ZADARMA_API_KEY", "")
        self.api_secret = api_secret or os.getenv("ZADARMA_API_SECRET", "")

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    @staticmethod
    def signature(method_path: str, params: dict[str, str], secret: str) -> str:
        """Build the HMAC-SHA1 signature required by Zadarma's documented API."""
        params_string = urlencode(sorted(params.items()))
        payload = (
            method_path
            + params_string
            + hashlib.md5(params_string.encode("utf-8")).hexdigest()
        )
        digest = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(digest).decode("ascii")

    def _get(self, method_path: str, params: dict[str, str] | None = None) -> dict:
        if not self.configured:
            raise ZadarmaConfigurationError(
                "Zadarma API is not configured; no provider request was made."
            )
        clean_params = {str(k): str(v) for k, v in (params or {}).items()}
        query = urlencode(sorted(clean_params.items()))
        url = f"{self.BASE_URL}{method_path}"
        if query:
            url = f"{url}?{query}"
        signature = self.signature(method_path, clean_params, self.api_secret)
        request = Request(
            url,
            headers={
                "Authorization": f"{self.api_key}:{signature}",
                "Accept": "application/json",
                "User-Agent": "ODEVI-Numbers/0.1",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.TIMEOUT_SECONDS) as response:
                payload = response.read(1_000_001)
            if len(payload) > 1_000_000:
                raise ZadarmaAPIError("Zadarma response exceeded the safety limit.")
            result = json.loads(payload.decode("utf-8"))
        except HTTPError as exc:
            raise ZadarmaAPIError(f"Zadarma API returned HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ZadarmaAPIError("Could not reach Zadarma API.") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ZadarmaAPIError("Zadarma returned an invalid JSON response.") from exc

        if not isinstance(result, dict) or result.get("status") != "success":
            raise ZadarmaAPIError("Zadarma did not confirm a successful API response.")
        return result

    def list_countries(self) -> dict:
        """Read countries for which the account can connect virtual numbers."""
        return self._get("/v1/direct_numbers/countries/")

    def list_country_directions(self, country_iso2: str = "PT") -> dict:
        """Read Portuguese number destinations, requirements, fees and SMS flags."""
        country = country_iso2.strip().upper()
        if len(country) != 2 or not country.isalpha():
            raise ValueError("country_iso2 must be a two-letter ISO country code.")
        return self._get("/v1/direct_numbers/country/", {"country": country})

    def list_available_numbers(self, direction_id: str, mask: str | None = None) -> dict:
        """Read available numbers; this method never places an order."""
        direction = str(direction_id).strip()
        if not direction.isdigit():
            raise ValueError("direction_id must contain digits only.")
        params = {"mask": mask.strip()} if mask and mask.strip() else {}
        return self._get(f"/v1/direct_numbers/available/{direction}/", params)
