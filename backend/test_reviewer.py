"""Isolated test for Node 4 Meta Tribe LLM reviewer."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from models.compliance_models import InterventionPayload
from models.message_models import MessageDraft
from services.meta_tribe.meta_tribe_service import review_draft

WEAK_DRAFT = MessageDraft(
    channel="Email",
    subject="Hello",
    body_plain="Hi. We have a discount. Thanks.",
    body_html=None,
    cta_text="click here",
    cta_url="https://example.com",
)

STRONG_DRAFT = MessageDraft(
    channel="Email",
    subject="Act now: your exclusive 15% retention offer ends this week",
    body_plain=(
        "What if your next renewal cost 15% less than you expected? "
        "We analyzed your account and unlocked an exclusive 15% discount "
        "reserved only for subscribers like you. "
        "This limited-time 15% rate expires soon and will not be extended. "
        "Tap below to claim your savings before the deadline passes."
    ),
    cta_text="Get this discount",
    cta_url="https://app.retentionos.example/claim?user_id=99",
)


def main():
    load_dotenv()
    state = {
        "payload": InterventionPayload(user_id=99, best_discount="15%", expected_profit=800.0),
    }

    weak = review_draft(WEAK_DRAFT, state)
    assert not weak.approved, "Weak draft should not be approved"
    assert weak.score < 6
    print(f"[PASS] Weak draft rejected (score={weak.score}): {weak.feedback[:80]}...")

    strong = review_draft(STRONG_DRAFT, state)
    assert strong.approved, f"Strong draft should be approved (score={strong.score})"
    assert strong.score >= 6
    print(f"[PASS] Strong draft approved (score={strong.score}).")


if __name__ == "__main__":
    main()
