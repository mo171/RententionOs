from __future__ import annotations

import json

from services.churn.churn_service import (
    METADATA_ARTIFACT_PATH,
    METRICS_JSON_PATH,
    METRICS_REPORT_PATH,
    MODEL_ARTIFACT_PATH,
    HIGH_RISK_CSV_PATH,
    save_artifacts,
    train_churn_model,
)


def main() -> None:
    artifacts = train_churn_model()
    save_artifacts(artifacts)
    print(
        json.dumps(
            {
                "model_artifact": MODEL_ARTIFACT_PATH,
                "metadata": METADATA_ARTIFACT_PATH,
                "metrics_json": METRICS_JSON_PATH,
                "metrics_report": METRICS_REPORT_PATH,
                "high_risk_customers": HIGH_RISK_CSV_PATH,
                "rows": len(artifacts.rows),
                "train_rows": len(artifacts.train_indices),
                "test_rows": len(artifacts.test_indices),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

