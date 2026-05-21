"""
Dispatch node — sends approved message via send_message tool.
"""
import os
from dotenv import load_dotenv

from models.message_models import MessageDraft
from models.strategy_models import InterventionGraphState
from services.tools.send_message import send_message

load_dotenv()


def dispatch_node(state: InterventionGraphState) -> InterventionGraphState:
    draft = state.get("current_draft")
    if draft is None:
        raise ValueError("dispatch_node requires current_draft")

    if isinstance(draft, dict):
        draft = MessageDraft(**draft)

    profile = state.get("subscriber_profile") or {}
    test_mode = os.getenv("TEST_MODE", "true").lower() in ("1", "true", "yes")

    result = send_message(
        draft=draft,
        to_email=profile.get("email"),
        to_phone=profile.get("phone"),
        test_mode=test_mode,
    )

    return {
        **state,
        "send_result": result,
    }
