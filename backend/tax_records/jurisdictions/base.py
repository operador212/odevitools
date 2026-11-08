"""Shared jurisdiction pack contract; intentionally metadata-only."""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class JurisdictionPack:
    code: str
    name: str
    currency: str
    tax_year_pattern: str
    version: str

    def validate_tax_year(self, tax_year: str) -> str:
        value = (tax_year or "").strip()
        if not re.fullmatch(self.tax_year_pattern, value):
            raise ValueError(f"Invalid tax-year format for {self.code}: {value!r}")
        if self.code == "UK":
            start, end = value.split("-")
            if int(end) != (int(start) + 1) % 100:
                raise ValueError("UK tax year must span consecutive calendar years")
        return value

def get_jurisdiction_pack(code: str) -> JurisdictionPack:
    from . import _PACKS
    normalized = (code or "").strip().upper()
    try:
        return _PACKS[normalized]
    except KeyError as exc:
        raise ValueError("Unsupported jurisdiction; choose UK or PT") from exc
