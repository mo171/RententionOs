"""
Twilio stub — WhatsApp/SMS not tested in this milestone.
"""


def send_whatsapp_stub(to_phone: str, body: str) -> dict:
    print(f"[Twilio stub] Would send WhatsApp to {to_phone}: {body[:80]}...")
    return {"status": "stub", "to": to_phone}
