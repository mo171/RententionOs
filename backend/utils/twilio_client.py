import os
from twilio.rest import Client

def send_whatsapp(to_phone: str, body: str) -> dict:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "+12394885237")
    
    if not account_sid or not auth_token:
        # Fallback to stub if credentials missing
        print(f"[Twilio Stub] Sending WhatsApp to {to_phone}...")
        print(f"Body: {body[:100]}...")
        return {"sid": "stub_wa_999", "status": "sent"}
        
    client = Client(account_sid, auth_token)
    
    # Twilio sandbox requires numbers to be prefixed with 'whatsapp:'
    from_str = f"whatsapp:{from_whatsapp_number}"
    
    # Ensure to_phone has whatsapp: prefix
    to_str = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"
    
    message = client.messages.create(
        body=body,
        from_=from_str,
        to=to_str
    )
    
    return {"sid": message.sid, "status": message.status}
