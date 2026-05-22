"""
Unified send_message tool — single delivery abstraction for dispatch.
Routes internally to Resend (email) or stubs (Twilio, push, SMS).
"""
import os
from dotenv import load_dotenv

from models.message_models import MessageDraft, SendMessageResult
from utils.resend_client import send_email
from utils.twilio_client import send_whatsapp_stub

load_dotenv()

MAX_REVISIONS = 3


def send_message(
    draft: MessageDraft,
    to_email: str | None = None,
    to_phone: str | None = None,
    test_mode: bool = False,
) -> SendMessageResult:
    """
    Send intervention via the appropriate provider for the draft channel.
    In test_mode, email goes to TEST_RECIPIENT_EMAIL.
    """
    channel = draft.channel

    if channel == "Email":
        recipient = os.getenv("TEST_RECIPIENT_EMAIL") if test_mode else to_email
        if not recipient:
            return SendMessageResult(
                success=False,
                channel=channel,
                provider="resend",
                error="No recipient email",
            )
        try:
            html = draft.body_html or draft.body_plain
            result = send_email(
                to=recipient,
                subject=draft.subject or "Your retention offer",
                html=html,
                text=draft.body_plain,
            )
            print(f"[send_message] Email sent to {recipient} id={result.get('id')}")
            return SendMessageResult(
                success=True,
                channel=channel,
                provider="resend",
                message_id=str(result.get("id")),
            )
        except Exception as e:
            print(f"[send_message] Email failed: {e}")
            return SendMessageResult(
                success=False,
                channel=channel,
                provider="resend",
                error=str(e),
            )

    if channel == "Push Notification":
        print("[send_message] Push not implemented — skipping send.")
        return SendMessageResult(
            success=True,
            channel=channel,
            provider="skipped",
            message_id="push_not_implemented",
        )

    if channel == "SMS":
        print("[send_message] SMS skipped per project spec.")
        return SendMessageResult(
            success=True,
            channel=channel,
            provider="skipped",
            message_id="sms_skipped",
        )

    if channel in ("WhatsApp", "Twilio"):
        if to_phone:
            send_whatsapp_stub(to_phone, draft.body_plain)
        return SendMessageResult(
            success=True,
            channel=channel,
            provider="twilio_stub",
            message_id="whatsapp_stub",
        )

    return SendMessageResult(
        success=False,
        channel=channel,
        provider="unknown",
        error=f"Unknown channel: {channel}",
    )
