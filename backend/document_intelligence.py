"""Privacy-first document intake and text extraction for ODEVI AI.

This first iteration processes files in memory only. It does not persist uploads,
send content to an external model, or make legal/financial determinations.
"""
from __future__ import annotations
import hashlib
import io
import re
import zipfile
from dataclasses import asdict, dataclass
from typing import Any

MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_EXTRACTED_CHARS = 40_000
MAX_PDF_PAGES = 30
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}

@dataclass(frozen=True)
class DocumentAnalysis:
    filename: str
    document_type: str
    confidence: float
    sha256: str
    bytes_processed: int
    characters_extracted: int
    extracted_text: str
    needs_ocr: bool
    warnings: list[str]
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _classify(text: str) -> tuple[str, float]:
    sample = text.lower()
    patterns = {
        "invoice": (r"\binvoice\b|\bfatura\b|\binv\s*[-#:]?\s*\d+", 0.78),
        "bank_statement": (r"bank statement|account statement|statement period|saldo anterior|extrato bancário|extrato bancario", 0.82),
        "payslip": (r"payslip|pay slip|salary statement|recibo de vencimento|holerite", 0.82),
        "tax_document": (r"hm revenue|hmrc|self assessment|utr\b|irs\b|finanças|financas|declaração de rendimentos|declaracao de rendimentos", 0.72),
        "receipt": (r"\breceipt\b|\brecibo\b|proof of purchase", 0.72),
        "contract": (r"\bcontract\b|\bagreement\b|\bcontrato\b|terms and conditions", 0.70),
    }
    matches = [(kind, confidence) for kind, (pattern, confidence) in patterns.items() if re.search(pattern, sample)]
    return max(matches, key=lambda item: item[1]) if matches else ("unknown", 0.0)

def _extract_pdf(raw: bytes) -> tuple[str, list[str]]:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted:
        raise ValueError("PDF protegido por palavra-passe não pode ser analisado.")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError(f"O PDF excede o limite de {MAX_PDF_PAGES} páginas.")
    return "\n".join(page.extract_text() or "" for page in reader.pages), []

def _extract_docx(raw: bytes) -> tuple[str, list[str]]:
    # DOCX is a ZIP container: reject suspicious expansion before parsing XML.
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            expanded_size = sum(entry.file_size for entry in entries)
            if len(entries) > 200 or expanded_size > 32 * 1024 * 1024:
                raise ValueError("O documento DOCX excede os limites de segurança.")
            if any(entry.file_size > 0 and entry.compress_size == 0 for entry in entries):
                raise ValueError("O documento DOCX contém uma entrada inválida.")
            if any(entry.compress_size and entry.file_size / entry.compress_size > 1000 for entry in entries):
                raise ValueError("O documento DOCX tem uma taxa de compressão não permitida.")
    except zipfile.BadZipFile as exc:
        raise ValueError("O ficheiro DOCX está danificado ou não é válido.") from exc
    from docx import Document
    document = Document(io.BytesIO(raw))
    chunks = [p.text for p in document.paragraphs if p.text]
    for table in document.tables:
        for row in table.rows:
            chunks.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(chunks), []

def analyze_document(filename: str, raw: bytes) -> DocumentAnalysis:
    """Extract text and suggest a document category without retaining file bytes."""
    if not isinstance(raw, bytes) or not raw:
        raise ValueError("O ficheiro está vazio.")
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ValueError("O ficheiro excede o limite de 8 MB.")
    safe_name = (filename or "").replace("\\", "/").split("/")[-1].strip()
    extension = "." + safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Formato não suportado. Envia PDF, DOCX, TXT ou CSV.")
    warnings: list[str] = []
    if extension == ".pdf":
        text, warnings = _extract_pdf(raw)
        needs_ocr = not text.strip()
        if needs_ocr:
            warnings.append("Não foi possível extrair texto; este PDF pode ser digitalizado e precisar de OCR.")
    elif extension == ".docx":
        text, warnings = _extract_docx(raw)
        needs_ocr = False
    else:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("O ficheiro deve estar codificado em UTF-8.") from exc
        needs_ocr = False
    text = text.replace("\x00", "").strip()
    if len(text) > MAX_EXTRACTED_CHARS:
        text = text[:MAX_EXTRACTED_CHARS]
        warnings.append(f"Texto limitado aos primeiros {MAX_EXTRACTED_CHARS} caracteres.")
    document_type, confidence = _classify(text)
    if not text:
        warnings.append("Nenhum texto legível foi encontrado.")
    return DocumentAnalysis(
        filename=safe_name, document_type=document_type, confidence=confidence,
        sha256=hashlib.sha256(raw).hexdigest(), bytes_processed=len(raw),
        characters_extracted=len(text), extracted_text=text, needs_ocr=needs_ocr,
        warnings=warnings,
    )
