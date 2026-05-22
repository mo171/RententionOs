"""
Meta Tribe reviewer (Node 4) — LLM-based hook/engagement review.

Future: integrate TRIBE v2 (facebook/tribev2) for neural salience on text + visual creative.
See backend/docs/FUTURE_TRIBE_V2.md
"""
import json
from langchain_core.messages import HumanMessage

from prompts.reviewer_prompts import META_TRIBE_REVIEW_PROMPT
from models.message_models import MessageDraft, ReviewResult
from models.compliance_models import InterventionPayload
from utils.llm import get_llm

APPROVAL_SCORE_THRESHOLD = 6


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def review_draft(draft: MessageDraft, state: dict) -> ReviewResult:
    payload = state["payload"]
    if isinstance(payload, dict):
        payload = InterventionPayload(**payload)

    prompt = META_TRIBE_REVIEW_PROMPT.format(
        channel=draft.channel,
        best_discount=payload.best_discount,
        subject=draft.subject or "(none)",
        body_plain=draft.body_plain,
        cta_text=draft.cta_text,
        cta_url=draft.cta_url,
    )

    llm = get_llm(model_name="gpt-4o-mini", temperature=0.0)
    print("[Reviewer] Meta Tribe LLM reviewing draft...")
    response = llm.invoke([HumanMessage(content=prompt)])
    data = _parse_json(response.content)

    result = ReviewResult(**data)
    if result.approved and result.score >= 5:
        pass
    elif result.score >= APPROVAL_SCORE_THRESHOLD:
        result = result.model_copy(update={"approved": True})
    else:
        result = result.model_copy(update={"approved": False})

    print(f"[Reviewer] score={result.score} approved={result.approved}")
    if not result.approved:
        print(f"[Reviewer] feedback: {result.feedback}")
    return result
