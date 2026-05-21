"""
Grader: Uses LLM to assess relevance of each retrieved chunk.
Returns only the chunks that pass the relevance threshold.
"""
import json
from langchain_core.messages import HumanMessage
from prompts.compliance_prompts import RELEVANCE_GRADER_PROMPT
from models.compliance_models import RelevanceGrade
from utils.llm import get_llm


def grade_chunks(
    primary_query: str,
    chunks: list[dict],
) -> list[dict]:
    """
    For each chunk, asks the LLM to grade it as relevant or not.
    Returns only the chunks graded as relevant.

    Uses a fast/cheap model (gpt-4o-mini) for this classification task.
    """
    llm = get_llm(model_name="gpt-4o-mini", temperature=0.0)
    relevant_chunks = []

    for i, chunk in enumerate(chunks):
        prompt = RELEVANCE_GRADER_PROMPT.format(
            query=primary_query,
            chunk=chunk["chunk_text"],
        )
        print(f"[Grader] Grading chunk {i+1}/{len(chunks)}...")

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            raw = response.content.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            grade_data = json.loads(raw)
            grade = RelevanceGrade(**grade_data)

            if grade.is_relevant:
                chunk["relevance_explanation"] = grade.explanation
                relevant_chunks.append(chunk)
                print(f"[Grader]   -> RELEVANT: {grade.explanation}")
            else:
                print(f"[Grader]   -> NOT RELEVANT: {grade.explanation}")

        except Exception as e:
            print(f"[Grader] Grading failed for chunk {i+1}: {e}. Skipping chunk.")

    print(f"[Grader] {len(relevant_chunks)}/{len(chunks)} chunks passed relevance filter.")
    return relevant_chunks
