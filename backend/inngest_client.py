import os
# pyrefly: ignore [missing-import]
from inngest import Inngest

inngest_client = Inngest(
    app_id="retentionos-gatekeeper",
    is_production=os.environ.get("ENVIRONMENT") == "production"
)
