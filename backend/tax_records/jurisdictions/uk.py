"""UK jurisdiction metadata only; no HMRC liability or deduction logic."""
from .base import JurisdictionPack

UK_PACK = JurisdictionPack(
    code="UK",
    name="United Kingdom",
    currency="GBP",
    tax_year_pattern=r"\\d{4}-\\d{2}",
    version="uk-metadata-v1",
)
