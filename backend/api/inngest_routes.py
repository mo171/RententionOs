from fastapi import APIRouter
from inngest.fast_api import serve
import inngest

from inngest_client import inngest_client
from services.agents.intervention_graph import compile_intervention_graph

router = APIRouter()

@inngest_client.create_function(
    fn_id="process-retention-workflow",
    trigger=inngest.TriggerEvent(event="gatekeeper/process.retention"),
)
async def process_retention_workflow(ctx: inngest.Context, step: inngest.Step):
    """
    Background workflow that processes a retention evaluation and runs the agent graph.
    """
    event_data = ctx.event.data
    
    # 1. Start execution
    def _run_graph():
        graph = compile_intervention_graph()
        initial_state = {
            "payload": event_data,
            "should_intervene": True
        }
        return graph.invoke(initial_state)

    # 2. Wrap LangGraph execution in a step to trace it in Inngest
    result = await step.run("run-langgraph-agent", _run_graph)
    
    return {"status": "completed", "result": result}

# Expose the Inngest handler to FastAPI
serve_app = serve(inngest_client, [process_retention_workflow])

# The path here must match where Inngest looks for your app
router.add_route("/api/inngest", serve_app, methods=["GET", "POST", "PUT"])
