"""
Message Writer service (Node 3).
"""
import json
import re
from langchain_core.messages import HumanMessage

from prompts.writer_prompts import WRITER_PROMPT, FALLBACK_EMAIL_BODY
from models.message_models import MessageDraft
from models.compliance_models import ComplianceResult, InterventionPayload
from models.strategy_models import StrategyResult
from utils.llm import get_llm

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def trim_review_history(review_history: list[dict], max_pairs: int = 2) -> str:
    if not review_history:
        return "(none — first draft)"
    recent = review_history[-max_pairs:]
    lines = []
    for i, r in enumerate(recent, start=1):
        lines.append(
            f"Revision {i}: score={r.get('score')} approved={r.get('approved')} "
            f"feedback={r.get('feedback', '')}"
        )
    return "\n".join(lines)


def build_email_html(
    body_content: str,
    cta_text: str,
    cta_url: str,
    discount: str,
    subscriber_name: str,
) -> str:
    """Decorative HTML email with styled CTA button — no emojis."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f5f0;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f0;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">
        <tr>
          <td style="background:#1a4d2e;padding:24px 32px;">
            <p style="margin:0;color:#ffffff;font-size:14px;letter-spacing:1px;">RETENTIONOS</p>
            <h1 style="margin:8px 0 0;color:#ffffff;font-size:22px;font-weight:normal;">
              Your {discount} retention offer
            </h1>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;color:#2c2c2c;font-size:16px;line-height:1.6;">
            <p style="margin:0 0 16px;">Dear {subscriber_name},</p>
            {body_content.replace(chr(10), '<br>')}
            <table cellpadding="0" cellspacing="0" style="margin:28px 0 8px;">
              <tr>
                <td style="background:#2d6a4f;border-radius:6px;">
                  <a href="{cta_url}" style="display:inline-block;padding:14px 28px;color:#ffffff;
                     text-decoration:none;font-size:16px;font-weight:bold;">{cta_text}</a>
                </td>
              </tr>
            </table>
            <p style="margin:16px 0 0;font-size:13px;color:#666;">
              This offer is subject to company retention policy terms.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px;background:#f9f9f7;font-size:12px;color:#888;">
            RetentionOS | Customer Success
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def validate_draft(draft: MessageDraft, best_discount: str) -> MessageDraft:
    combined = f"{draft.subject or ''} {draft.body_plain} {draft.body_html or ''}"
    if EMOJI_PATTERN.search(combined):
        raise ValueError("Draft contains emojis — not allowed in intervention messages.")
    if best_discount not in draft.body_plain and best_discount not in (draft.body_html or ""):
        raise ValueError(f"Draft must mention discount {best_discount}")
    if not draft.cta_text or not draft.cta_url:
        raise ValueError("Draft must include cta_text and cta_url")
    return draft


def build_fallback_draft(
    channel: str,
    payload: InterventionPayload,
    profile: dict,
) -> MessageDraft:
    name = profile.get("full_name", "Valued Customer")
    discount = payload.best_discount
    cta_url = f"https://app.retentionos.example/claim?user_id={payload.user_id}"
    body = FALLBACK_EMAIL_BODY.format(discount=discount)
    body_html = build_email_html(body, "Get this discount", cta_url, discount, name)
    return MessageDraft(
        channel=channel,
        subject=f"Your exclusive {discount} retention offer",
        body_plain=body.replace("{discount}", discount),
        body_html=body_html,
        cta_text="Get this discount",
        cta_url=cta_url,
    )


def generate_draft(state: dict) -> MessageDraft:
    payload = state["payload"]
    if isinstance(payload, dict):
        payload = InterventionPayload(**payload)

    strategy = state.get("strategy_result")
    if isinstance(strategy, dict):
        strategy = StrategyResult(**strategy)

    compliance = state.get("compliance_result")
    if isinstance(compliance, dict):
        compliance = ComplianceResult(**compliance)

    profile = state.get("subscriber_profile") or {}
    channel = strategy.channel if strategy else "Email"
    revision_count = state.get("revision_count", 0)

    last_review = state.get("last_review")
    feedback = "(none — first draft)"
    if last_review:
        if isinstance(last_review, dict):
            feedback = last_review.get("feedback", feedback)
        else:
            feedback = last_review.feedback

    prompt = WRITER_PROMPT.format(
        channel=channel,
        revision_count=revision_count,
        subscriber_name=profile.get("full_name", "Valued Customer"),
        user_id=payload.user_id,
        best_discount=payload.best_discount,
        compliance_summary=compliance.reasoning[:400] if compliance else "",
        strategy_summary=strategy.reasoning[:300] if strategy else "",
        reviewer_feedback=(
            trim_review_history(state.get("review_history", []))
            if revision_count > 0
            else feedback
        ),
    )

    model = "gpt-4o" if channel == "Email" else "gpt-4o-mini"
    llm = get_llm(model_name=model, temperature=0.3)
    print(f"[Writer] Generating draft (channel={channel}, revision={revision_count})...")
    response = llm.invoke([HumanMessage(content=prompt)])
    data = _parse_json(response.content)

    body_content = data.get("body_content") or data.get("body_plain", "")
    body_plain = data.get("body_plain", body_content)
    cta_text = data.get("cta_text", "Get this discount")
    cta_url = data.get("cta_url", f"https://app.retentionos.example/claim?user_id={payload.user_id}")

    body_html = None
    if channel == "Email":
        paragraphs = "".join(
            f'<p style="margin:0 0 16px;">{p.strip()}</p>'
            for p in body_content.split("\n\n")
            if p.strip()
        )
        body_html = build_email_html(
            paragraphs,
            cta_text,
            cta_url,
            payload.best_discount,
            profile.get("full_name", "Valued Customer"),
        )

    draft = MessageDraft(
        channel=channel,
        subject=data.get("subject"),
        body_plain=body_plain,
        body_html=body_html,
        cta_text=cta_text,
        cta_url=cta_url,
    )
    return validate_draft(draft, payload.best_discount)
