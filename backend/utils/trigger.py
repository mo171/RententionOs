import os
from dotenv import load_dotenv
# We are creating a mock/wrapper for Trigger.dev as the Python SDK evolves.
# Currently, it is recommended to use the standard webhooks or the newer triggerdotdev package if applicable.

load_dotenv()

TRIGGER_API_KEY = os.getenv("TRIGGER_API_KEY")

class TriggerClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def send_event(self, name: str, payload: dict):
        """
        Mock sending an event to Trigger.dev.
        In a real application, you'd use their SDK or hit their HTTP API directly.
        """
        print(f"[Trigger.dev] Mock sending event '{name}' with payload: {payload}")
        return {"status": "queued", "id": "mock_task_id_123"}

def get_trigger_client() -> TriggerClient:
    """
    Initializes and returns a Trigger.dev client wrapper.
    """
    if not TRIGGER_API_KEY:
        print("Warning: TRIGGER_API_KEY is not set.")
    return TriggerClient(api_key=TRIGGER_API_KEY)
