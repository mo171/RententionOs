"""
Resend email client for intervention delivery.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Resend requires FROM on a verified domain — cannot use @gmail.com as sender.
RESEND_SANDBOX_FROM = "onboarding@resend.dev"


def _resolve_from_email() -> str:
    from_email = os.getenv("RESEND_FROM_EMAIL", "").strip()
    if not from_email or from_email.startswith("your_"):
        print(f"[Resend] Using sandbox sender: {RESEND_SANDBOX_FROM}")
        return RESEND_SANDBOX_FROM
    lower = from_email.lower()
    if any(x in lower for x in ("@gmail.com", "@yahoo.", "@hotmail.", "@outlook.")):
        print(
            f"[Resend] RESEND_FROM_EMAIL cannot be a personal inbox ({from_email}). "
            f"Using {RESEND_SANDBOX_FROM}. Verify your own domain at resend.com/domains for production."
        )
        return RESEND_SANDBOX_FROM
    return from_email


def send_email(
    to: str,
    subject: str,
    html: str,
    text: str,
) -> dict:
    api_key = os.getenv("RESEND_API_KEY", "")
    from_email = _resolve_from_email()

    if not api_key or api_key.startswith("your_"):
        raise ValueError("RESEND_API_KEY is not configured in .env")

    import resend

    resend.api_key = api_key
    params = {
        "from": from_email,
        "to": [to],
        "subject": subject,
        "html": html,
        "text": text,
    }
    result = resend.Emails.send(params)
    return {"id": result.get("id") if isinstance(result, dict) else getattr(result, "id", str(result))}
