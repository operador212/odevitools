from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import stripe

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

DOWNLOAD_DIR = "/tmp/odevi_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Stripe secrets must be configured as environment variables in Render.
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class DownloadRequest(BaseModel):
    url: str
    format: str = "mp4"


class TaxCheckoutRequest(BaseModel):
    jurisdiction: str
    # A server-generated report/job ID should be added when report persistence is implemented.
    report_id: str | None = None


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
        "tax_checkout": "configured" if stripe.api_key else "not_configured",
    }


@app.post("/tax/checkout")
def create_tax_checkout(request: TaxCheckoutRequest):
    """Create a one-time Stripe Checkout Session for the ODEVI tax report."""
    require_stripe_config()

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
    """Verify payment directly with Stripe; never trust browser redirect alone."""
    require_stripe_config()

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        raise HTTPException(status_code=404, detail="Sessão de pagamento não encontrada.")

    if session.metadata.get("product") != "odevi_tax_report":
        raise HTTPException(status_code=400, detail="Sessão não pertence ao ODEVI Tax Report.")

    paid = session.payment_status == "paid"
    return {
        "paid": paid,
        "payment_status": session.payment_status,
        "report_id": session.metadata.get("report_id"),
        "jurisdiction": session.metadata.get("jurisdiction"),
        # Report delivery is deliberately not enabled until secure report storage,
        # job persistence, and fulfilment are implemented and tested.
        "report_ready": False,
    }


@app.post("/tax/stripe-webhook")
async def stripe_webhook(request: Request):
    """Validate Stripe webhook signatures before handling payment events."""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook ainda não está configurado.")

    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Assinatura Stripe em falta.")

    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido.")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Assinatura do webhook inválida.")

    # Fulfilment is intentionally not performed here yet. The next stage must
    # persist paid report jobs and process this event idempotently before delivery.
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


@app.post("/download")
def download_media(request: DownloadRequest):
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL inválida.")

    if request.format not in ["mp4", "mp3"]:
        raise HTTPException(
            status_code=400,
            detail="Formato deve ser mp4 ou mp3."
        )

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    allowed_hosts = (
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "www.youtube-nocookie.com",
        "tiktok.com",
        "www.tiktok.com",
        "vm.tiktok.com",
        "vt.tiktok.com",
    )
    if not any(host in request.url.lower() for host in allowed_hosts):
        raise HTTPException(
            status_code=400,
            detail="Nesta primeira versão, use um link do YouTube."
        )

    if request.format == "mp3":
        options = {
            "extractor_args": {
                "youtubepot-bgutilhttp": {
                    "base_url": "http://127.0.0.1:4416"
                }
            },
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
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
            "extractor_args": {
                "youtubepot-bgutilhttp": {
                    "base_url": "http://127.0.0.1:4416"
                }
            },
        }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(request.url, download=True)

        title = info.get("title", "ODEVI Download")
        if request.format == "mp3":
            filename = f"{file_id}.mp3"
            media_type = "audio/mpeg"
        else:
            filename = f"{file_id}.mp4"
            media_type = "video/mp4"

        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="O arquivo não foi criado.")

        safe_title = "".join(
            c for c in title if c.isalnum() or c in " -_"
        ).strip()

        return FileResponse(
            filepath,
            media_type=media_type,
            filename=f"{safe_title}.{request.format}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no processamento: {str(e)}"
        )
