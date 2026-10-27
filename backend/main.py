from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# Stripe secrets must be configured as environment variables in Render.
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class TaxCheckoutRequest(BaseModel):
    jurisdiction: str
    # Replace with a persisted server-side report/job ID when report processing is implemented.
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
        raise HTTPException(
            status_code=404,
            detail="Sessão de pagamento não encontrada.",
        )

    if session.metadata.get("product") != "odevi_tax_report":
        raise HTTPException(
            status_code=400,
            detail="Sessão não pertence ao ODEVI Tax Report.",
        )

    return {
        "paid": session.payment_status == "paid",
        "payment_status": session.payment_status,
        "report_id": session.metadata.get("report_id"),
        "jurisdiction": session.metadata.get("jurisdiction"),
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
