"""
Placeholder for future TRIBE v2 integration.
https://huggingface.co/facebook/tribev2
"""


def score_hook_stimulus(text: str, image_path: str | None = None) -> dict:
    raise NotImplementedError(
        "TRIBE v2 hook scoring not yet integrated. "
        "Use meta_tribe_service.review_draft (LLM) for now. "
        "See backend/docs/FUTURE_TRIBE_V2.md"
    )
