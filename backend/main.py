from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from urllib.parse import urlparse
import os
import uuid
import stripe
import yt_dlp
from bank_csv_importer import parse_bank_csv
from tax_report_builder import build_tax_report

app = FastAPI(title="ODEVI+ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://odevitools.com",
        "https://www.odevitools.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe secrets must be configured as environment variables in Render.
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


DOWNLOAD_DIR = "/tmp/odevi_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class DownloadRequest(BaseModel):
    url: str
    format: str = "mp4"


class TaxCheckoutRequest(BaseModel):
    jurisdiction: str
    # Replace with a persisted server-side report/job ID when report processing is implemented.
    report_id: str | None = None


def validate_tax_checkout_session(session):
    """Reject sessions that are not the exact paid ODEVI one-time product."""
    metadata = session.metadata or {}
    if metadata.get("product") != "odevi_tax_report":
        raise HTTPException(status_code=400, detail="Sessão não pertence ao ODEVI Tax Report.")
    if getattr(session, "mode", None) != "payment":
        raise HTTPException(status_code=400, detail="Tipo de pagamento inválido.")
    if getattr(session, "currency", None) != "gbp" or getattr(session, "amount_total", None) != 599:
        raise HTTPException(status_code=400, detail="Valor ou moeda do pagamento inválidos.")
    if metadata.get("jurisdiction", "").upper() not in {"UK", "PT"}:
        raise HTTPException(status_code=400, detail="Jurisdição inválida na sessão de pagamento.")
    if not metadata.get("report_id"):
        raise HTTPException(status_code=400, detail="Identificador do relatório em falta.")
    return metadata


def require_stripe_config():
    if not stripe.api_key:
        raise HTTPException(
            status_code=503,
            detail="O checkout fiscal ainda não está configurado.",
        )


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "ODEVI+",
        "downloads": "enabled",
        "tax_checkout": "configured" if stripe.api_key else "not_configured",
    }


def validate_download_url(url: str):
    """Allow only explicitly supported public media hosts."""
    parsed_url = urlparse(url)
    allowed_hosts = {
        "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
        "youtu.be", "www.youtube-nocookie.com", "tiktok.com", "www.tiktok.com",
        "vm.tiktok.com", "vt.tiktok.com",
        "instagram.com", "www.instagram.com",
    }
    if (parsed_url.scheme not in {"http", "https"} or parsed_url.hostname not in allowed_hosts
            or parsed_url.username or parsed_url.password or parsed_url.port not in (None, 80, 443)):
        raise HTTPException(
            status_code=400,
            detail="Usa um link público válido do YouTube, TikTok ou Instagram.",
        )
    return parsed_url


@app.post("/download")
def download_media(request: DownloadRequest):
    """Download supported public media URLs as MP4 or MP3."""
    validate_download_url(request.url)
    if request.format not in {"mp4", "mp3"}:
        raise HTTPException(status_code=400, detail="Formato deve ser mp4 ou mp3.")

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    extractor_args = {
        "youtubepot-bgutilhttp": {"base_url": "http://127.0.0.1:4416"}
    }
    if request.format == "mp3":
        options = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "extractor_args": extractor_args,
            "js_runtimes": {"deno": {}},
            "sleep_interval_requests": 1,
            "retries": 3,
            "fragment_retries": 3,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        options = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "extractor_args": extractor_args,
        }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(request.url, download=True)
        filename = f"{file_id}.{request.format}"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if not os.path.isfile(filepath):
            raise HTTPException(status_code=500, detail="O ficheiro não foi criado.")
        title = info.get("title", "ODEVI Download")
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        return FileResponse(
            filepath,
            media_type="audio/mpeg" if request.format == "mp3" else "video/mp4",
            filename=f"{safe_title or 'ODEVI Download'}.{request.format}",
        )
    except HTTPException:
        raise
    except Exception as exc:
        error_text = str(exc).lower()
        if any(marker in error_text for marker in (
            "http error 429",
            "too many requests",
            "sign in to confirm",
            "not a bot",
        )):
            raise HTTPException(
                status_code=503,
                detail=(
                    "A plataforma está a limitar temporariamente os pedidos deste servidor. "
                    "Tenta novamente mais tarde. Não é necessário alterar o link."
                ),
            ) from exc
        raise HTTPException(
            status_code=502,
            detail="A plataforma não permitiu processar este conteúdo. Confirma se é público e tenta novamente.",
        ) from exc


@app.post("/tax/checkout")
def create_tax_checkout(request: TaxCheckoutRequest):
    """Paid report checkout is intentionally unavailable until fulfilment is production-ready."""
    raise HTTPException(status_code=503, detail="O relatório pago está temporariamente indisponível. Usa o organizador gratuito enquanto concluímos a entrega segura do relatório.")

    jurisdiction = request.jurisdiction.upper().strip()
    if jurisdiction not in {"UK", "PT"}:
        raise HTTPException(
            status_code=400,
            detail="Escolhe Reino Unido (UK) ou Portugal (PT).",
        )

    report_id = request.report_id or str(uuid.uuid4())
    if len(report_id) > 100:
        raise HTTPException(status_code=400, detail="ID de relatório inválido.")

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": 599,
                    "product_data": {
                        "name": "ODEVI Tax Report",
                        "description": (
                            "Relatório de apoio fiscal para trabalhadores "
                            "independentes. Jurisdição: " + jurisdiction
                        ),
                    },
                },
                "quantity": 1,
            }],
            metadata={
                "product": "odevi_tax_report",
                "jurisdiction": jurisdiction,
                "report_id": report_id,
            },
            client_reference_id=report_id,
            success_url=(
                "https://odevitools.com/tax-assistant.html"
                "?payment=success&session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=(
                "https://odevitools.com/tax-assistant.html?payment=cancelled"
            ),
            idempotency_key=f"odevi-tax-{report_id}",
        )
    except stripe.error.StripeError:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível iniciar o checkout. Tenta novamente.",
        )

    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "report_id": report_id,
    }


@app.get("/tax/payment-status/{session_id}")
def tax_payment_status(session_id: str):
    """Paid report delivery is disabled until durable fulfilment is implemented."""
    raise HTTPException(status_code=503, detail="A confirmação e entrega de relatórios pagos ainda não está disponível.")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        raise HTTPException(
            status_code=404,
            detail="Sessão de pagamento não encontrada.",
        )

    metadata = validate_tax_checkout_session(session)

    return {
        "paid": session.payment_status == "paid" and session.status == "complete",
        "payment_status": session.payment_status,
        "report_id": metadata.get("report_id"),
        "jurisdiction": metadata.get("jurisdiction"),
        # Delivery remains disabled until secure storage and report fulfilment exist.
        "report_ready": False,
    }


@app.post("/tax/stripe-webhook")
async def stripe_webhook(request: Request):
    """Validate Stripe webhook signatures before handling payment events."""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise HTTPException(
            status_code=503,
            detail="Webhook ainda não está configurado.",
        )

    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Assinatura Stripe em falta.")

    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido.")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Assinatura do webhook inválida.",
        )

    # Payment events are verified here, but are not fulfilled yet. Implement
    # durable jobs, idempotency and secure report delivery before launch.
    if event["type"] in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        session = event["data"]["object"]
        if (
            session.get("metadata", {}).get("product") == "odevi_tax_report"
            and session.get("payment_status") == "paid"
        ):
            print(
                "ODEVI tax payment verified",
                session.get("id"),
                session.get("metadata", {}).get("report_id"),
            )

    return {"received": True}


MAX_CSV_FILES = 10
MAX_CSV_FILE_BYTES = 5 * 1024 * 1024


@app.post("/tax/process-csv")
async def process_paid_csv_report(
    session_id: str,
    files: list[UploadFile] = File(...),
):
    """Paid processing is disabled until secure storage and delivery are ready."""
    raise HTTPException(status_code=503, detail="O processamento pago está temporariamente indisponível. Usa o organizador gratuito local.")
    if not files or len(files) > MAX_CSV_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Envia entre 1 e {MAX_CSV_FILES} ficheiros CSV.",
        )

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        raise HTTPException(status_code=404, detail="Sessão de pagamento não encontrada.")

    metadata = validate_tax_checkout_session(session)
    if session.payment_status != "paid" or session.status != "complete":
        raise HTTPException(status_code=402, detail="O pagamento ainda não foi confirmado.")

    jurisdiction = str(metadata["jurisdiction"]).upper()

    parsed_statements = []
    for upload in files:
        filename = (upload.filename or "").strip()
        if not filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=415,
                detail="Nesta versão, só são aceites ficheiros CSV de extratos bancários.",
            )
        raw = await upload.read(MAX_CSV_FILE_BYTES + 1)
        if len(raw) > MAX_CSV_FILE_BYTES:
            raise HTTPException(status_code=413, detail="Cada ficheiro deve ter no máximo 5 MB.")
        try:
            csv_text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                csv_text = raw.decode("cp1252")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail=f"Não foi possível ler o CSV: {filename}")
        try:
            parsed = parse_bank_csv(csv_text, jurisdiction)
        except (ValueError, UnicodeError) as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Não foi possível interpretar o ficheiro {filename}: {str(exc)}",
            )
        parsed_statements.append(parsed)

    report = build_tax_report(parsed_statements)
    report["processing_status"] = "prototype_report_generated"
    report["delivery"] = "returned_in_response_only"
    report["important_note"] = (
        "Guarda o resultado antes de fechares a página. Esta versão não guarda "
        "os documentos nem envia o relatório por email."
    )
    return report


# ODEVI AI document intelligence — in-memory extraction; no upload persistence.
from document_intelligence import analyze_document, MAX_DOCUMENT_BYTES
from tax_records.oidc import get_current_principal

@app.post("/documents/analyze")
async def analyze_uploaded_document(
    file: UploadFile = File(...),
    principal = Depends(get_current_principal),
):
    """Extract a document for an authenticated OIDC user; bytes are not persisted."""
    _ = principal  # Identity is verified server-side; this endpoint is intentionally stateless.
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome do ficheiro em falta.")
    try:
        raw = await file.read(MAX_DOCUMENT_BYTES + 1)
        result = analyze_document(file.filename, raw, perform_ocr=os.getenv("ODEVI_OCR_ENABLED", "").lower() == "true")
        return result.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Do not expose parser internals or document contents in API errors.
        if exc.__class__.__module__.startswith(("pypdf", "docx")):
            raise HTTPException(status_code=422, detail="Não foi possível ler este documento.") from None
        raise
    finally:
        await file.close()
