"""
Strategy Service: Channel and timing decisions for Node 2.
"""
import json
from datetime import datetime, timezone, timedelta
from langchain_core.messages import HumanMessage

from prompts.strategy_prompts import STRATEGY_DECISION_PROMPT
from models.compliance_models import InterventionPayload, ComplianceResult
from models.strategy_models import (
    SubscriberProfile,
    InteractionEvent,
    StrategyResult,
)
from utils.llm import get_llm

ALLOWED_CHANNELS = {"Email", "SMS", "Push Notification"}

CHANNEL_ALIASES = {
    "email": "Email",
    "sms": "SMS",
    "push": "Push Notification",
    "push notification": "Push Notification",
}


def _parse_json_response(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def fetch_subscriber(user_id: int, supabase_client) -> SubscriberProfile:
    response = (
        supabase_client.table("subscribers")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise ValueError(
            f"No subscriber found for user_id={user_id}. "
            "Run migrations/003_subscribers_and_interactions.sql on Supabase."
        )
    return SubscriberProfile(**rows[0])


def fetch_interactions(user_id: int, supabase_client, limit: int = 20) -> list[InteractionEvent]:
    response = (
        supabase_client.table("interaction_events")
        .select("*")
        .eq("user_id", user_id)
        .order("sent_at", desc=True)
        .limit(limit)
        .execute()
    )
    events = []
    for row in response.data or []:
        events.append(
            InteractionEvent(
                id=str(row["id"]),
                user_id=row["user_id"],
                channel=row["channel"],
                event_type=row["event_type"],
                sent_at=row["sent_at"],
                metadata=row.get("metadata") or {},
            )
        )
    return events


def _format_profile(profile: SubscriberProfile) -> str:
    return (
        f"Name: {profile.full_name}\n"
        f"Email: {profile.email or 'N/A'}\n"
        f"Phone: {profile.phone or 'N/A'}\n"
        f"Timezone: {profile.timezone}\n"
        f"Preferred channel: {profile.preferred_channel}\n"
        f"Opt-outs: sms={profile.opt_out_sms}, email={profile.opt_out_email}, push={profile.opt_out_push}\n"
        f"Segment: {profile.segment or 'N/A'}, LTV tier: {profile.ltv_tier or 'N/A'}"
    )


def _format_history(events: list[InteractionEvent]) -> str:
    if not events:
        return "(no interaction history)"
    lines = []
    for e in events:
        lines.append(
            f"- {e.sent_at} | {e.channel} | {e.event_type} | meta={e.metadata}"
        )
    return "\n".join(lines)


def _normalize_channel(raw: str) -> str:
    key = raw.strip().lower()
    if key in CHANNEL_ALIASES:
        return CHANNEL_ALIASES[key]
    if raw in ALLOWED_CHANNELS:
        return raw
    raise ValueError(f"Invalid channel: {raw}. Must be one of {ALLOWED_CHANNELS}")


def validate_strategy_result(
    result: StrategyResult,
    profile: SubscriberProfile,
) -> StrategyResult:
    channel = _normalize_channel(result.channel)
    result = result.model_copy(update={"channel": channel})

    if channel not in ALLOWED_CHANNELS:
        raise ValueError(f"Channel must be one of {ALLOWED_CHANNELS}")

    if channel == "Email" and profile.opt_out_email:
        raise ValueError("Cannot use Email: subscriber opted out")
    if channel == "SMS" and profile.opt_out_sms:
        raise ValueError("Cannot use SMS: subscriber opted out")
    if channel == "Push Notification" and profile.opt_out_push:
        raise ValueError("Cannot use Push: subscriber opted out")

    try:
        scheduled = datetime.fromisoformat(
            result.scheduled_time.replace("Z", "+00:00")
        )
    except ValueError as e:
        raise ValueError(f"Invalid scheduled_time ISO format: {result.scheduled_time}") from e

    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)

    min_time = datetime.now(timezone.utc) + timedelta(hours=1)
    if scheduled < min_time:
        scheduled = min_time + timedelta(minutes=5)
        print(
            f"[Strategy] Adjusted scheduled_time forward to "
            f"{scheduled.strftime('%Y-%m-%dT%H:%M:%SZ')} (LLM time was too soon)."
        )
        result = result.model_copy(
            update={"scheduled_time": scheduled.strftime("%Y-%m-%dT%H:%M:%SZ")}
        )

    return result


def run_strategy(
    payload: InterventionPayload,
    compliance_result: ComplianceResult,
    reasoning_trace: str,
    supabase_client,
) -> tuple[StrategyResult, dict]:
    """
    Fetches subscriber data and decides channel + scheduled_time.
    Returns (StrategyResult, trace_dict).
    """
    trace: dict = {}

    print("[Strategy] Fetching subscriber profile...")
    profile = fetch_subscriber(payload.user_id, supabase_client)
    trace["subscriber_profile"] = profile.model_dump()

    print("[Strategy] Fetching interaction history...")
    history = fetch_interactions(payload.user_id, supabase_client)
    trace["interaction_history"] = [e.model_dump() for e in history]

    current_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    llm = get_llm(model_name="gpt-4o-mini", temperature=0.0)
    prompt = STRATEGY_DECISION_PROMPT.format(
        user_id=payload.user_id,
        best_discount=payload.best_discount,
        expected_profit=payload.expected_profit,
        intervene=compliance_result.intervene,
        policy_source=compliance_result.policy_source,
        compliance_summary=compliance_result.reasoning[:500],
        current_utc_time=current_utc,
        subscriber_profile=_format_profile(profile),
        interaction_history=_format_history(history),
        timezone=profile.timezone,
    )

    print("[Strategy] LLM deciding channel and send time...")
    response = llm.invoke([HumanMessage(content=prompt)])
    data = _parse_json_response(response.content)
    result = StrategyResult(**data)
    result = validate_strategy_result(result, profile)
    trace["strategy_result"] = result.model_dump()

    print("[Strategy] Decision:")
    print(f"  channel: {result.channel}")
    print(f"  scheduled_time: {result.scheduled_time}")
    print(f"  confidence: {result.confidence}")
    print(f"  reasoning: {result.reasoning}")

    return result, trace
