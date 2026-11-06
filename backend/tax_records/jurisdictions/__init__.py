"""Jurisdiction metadata registry. No tax calculations are performed here."""
from .base import JurisdictionPack
from .uk import UK_PACK
from .pt import PT_PACK

_PACKS = {UK_PACK.code: UK_PACK, PT_PACK.code: PT_PACK}

def get_jurisdiction_pack(code: str) -> JurisdictionPack:
    normalized = (code or "").strip().upper()
    try:
        return _PACKS[normalized]
    except KeyError as exc:
        raise ValueError("Unsupported jurisdiction; choose UK or PT") from exc

def validate_tax_year(code: str, tax_year: str) -> str:
    return get_jurisdiction_pack(code).validate_tax_year(tax_year)
