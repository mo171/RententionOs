"""Isolated test for Node 3 Message Writer."""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from models.compliance_models import InterventionPayload, ComplianceResult
from models.strategy_models import StrategyResult
from services.writer.writer_service import generate_draft

EMOJI_PATTERN = re.compile(
    "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]+",
    flags=re.UNICODE,
)


def main():
    load_dotenv()
    state = {
        "payload": InterventionPayload(user_id=99, best_discount="15%", expected_profit=800.0),
        "compliance_result": ComplianceResult(
            intervene=True,
            reasoning="15% discount approved per policy.",
            policy_source="company_retention_policy",
            confidence=9,
        ),
        "strategy_result": StrategyResult(
            channel="Email",
            scheduled_time="2026-12-01T18:00:00Z",
            reasoning="Email preferred.",
            confidence=8,
        ),
        "subscriber_profile": {"full_name": "Alex Rivera", "user_id": 99},
        "revision_count": 0,
        "review_history": [],
        "last_review": None,
    }
    draft = generate_draft(state)
    assert draft.subject, "Email must have subject"
    assert draft.body_html, "Email must have HTML"
    assert draft.cta_text
    assert "15%" in draft.body_plain
    assert not EMOJI_PATTERN.search(draft.body_plain)
    print("[PASS] Writer produced valid Email draft.")
    print(f"  subject: {draft.subject}")
    print(f"  cta: {draft.cta_text}")


if __name__ == "__main__":
    main()
