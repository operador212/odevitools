"""Portugal jurisdiction metadata only; no AT liability or deduction logic."""
from .base import JurisdictionPack

PT_PACK = JurisdictionPack(
    code="PT",
    name="Portugal",
    currency="EUR",
    tax_year_pattern=r"\d{4}",
    version="pt-metadata-v1",
)
