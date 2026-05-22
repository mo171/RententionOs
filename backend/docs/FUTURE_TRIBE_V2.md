# TRIBE v2 — Future Hook / Engagement Integration

## Current (Node 4)

- **LLM Meta Tribe reviewer** in `services/meta_tribe/meta_tribe_service.py`
- Evaluates hook strength, CTA, urgency, channel fit
- Outputs: `approved`, `score`, `feedback`

## Future (TRIBE v2)

Model: [facebook/tribev2](https://huggingface.co/facebook/tribev2)

TRIBE v2 predicts fMRI brain responses to multimodal stimuli (text, video, audio). For RetentionOS we plan to use it as a **hook and user-engagement proxy**:

1. Render the email HTML (or push copy) to a preview image
2. Pass text + visual to TRIBE text/video encoders
3. Map predicted cortical salience to a 1-10 engagement score
4. Combine with LLM feedback for approve/revise decisions

## Requirements

- GPU recommended
- Large model download from HuggingFace
- Stub interface: `services/meta_tribe/tribe_v2_placeholder.py`

## Do not remove

The LLM reviewer is intentional for MVP; TRIBE v2 is not a drop-in replacement without the rendering + scoring pipeline above.
