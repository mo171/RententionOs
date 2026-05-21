"""
Central prompt registry for the Compliance Agent CRAG pipeline.
All prompts are defined here. Services import from here — never inline.
"""

# ─── Step 1: Multi-Query Generation ──────────────────────────────────────────

MULTI_QUERY_PROMPT = """\
You are an expert compliance analyst for a subscription-based financial services company.

A customer retention system wants to offer a discount to a subscriber.

Subscriber Context:
- User ID: {user_id}
- Proposed discount: {best_discount}
- Expected profit from this intervention: ${expected_profit}

Your task: Generate exactly 3 distinct, specific search queries to find relevant company \
policy documents that would determine whether this discount offer is permitted.

Each query should approach the policy from a different angle:
1. Discount authorization angle (is this discount level allowed?)
2. Customer eligibility angle (who can receive such offers?)
3. Profit and compliance angle (are there ROI or regulatory constraints?)

Return ONLY a JSON array of 3 strings. No explanation, no preamble.
Example format: ["query 1", "query 2", "query 3"]
"""

# ─── Step 4: Relevance Grader ────────────────────────────────────────────────

RELEVANCE_GRADER_PROMPT = """\
You are a relevance grading assistant for a RAG (Retrieval-Augmented Generation) system.

Your job is to determine whether the retrieved policy document chunk is relevant to \
answering the following compliance question.

Compliance Question:
{query}

Retrieved Chunk:
{chunk}

Grade this chunk. A chunk is RELEVANT if it contains information about:
- Discount policies, authorized discount levels, or offer restrictions
- Customer eligibility rules for promotional offers
- Profit margin or ROI requirements for interventions
- Regulatory or compliance rules about customer outreach

A chunk is NOT RELEVANT if it is about unrelated topics (e.g., data privacy, login policies, \
shipping, etc.)

You MUST respond in valid JSON only:
{{"is_relevant": true or false, "explanation": "one sentence reason"}}
"""

# ─── Step 5: Reasoning Trace ─────────────────────────────────────────────────

REASONING_PROMPT = """\
You are a compliance reasoning agent. Your job is to produce a detailed, transparent \
chain-of-thought explanation of why a proposed customer intervention is or is not permitted \
according to retrieved policy documents.

This reasoning will be shown in the UI (like Cursor shows agent thinking) so make it \
clear, structured, and human-readable.

Proposed Intervention:
- User ID: {user_id}
- Discount offered: {best_discount}
- Expected profit: ${expected_profit}

Relevant Policy Excerpts:
{relevant_chunks}

Write your full reasoning chain. Include:
1. What the policy says about this type of discount
2. Whether the proposed discount level is within allowed limits
3. Any conditions or caveats that apply
4. Your preliminary conclusion (approve/deny)

Be thorough. This trace is used to explain AI decision-making to the end user.
"""

# ─── Step 6: Final Verdict ───────────────────────────────────────────────────

FINAL_VERDICT_PROMPT = """\
You are a compliance decision agent. Based on the reasoning trace below, produce the \
final structured compliance verdict.

Reasoning Trace:
{reasoning_trace}

Relevant Policy Excerpts (for reference):
{relevant_chunks}

Policy Document Name (the most relevant one):
{doc_name}

You MUST respond in valid JSON only with these exact fields:
{{
  "intervene": true or false,
  "reasoning": "a concise 2-3 sentence summary of why intervention is approved/denied",
  "policy_source": "exact name of the policy document",
  "confidence": an integer from 1 to 10 indicating your confidence in this decision
}}
"""
