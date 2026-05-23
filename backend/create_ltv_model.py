from __future__ import annotations

import json

from services.ltv.ltv_service import (
    HIGH_VALUE_CSV_PATH,
    METADATA_ARTIFACT_PATH,
    METRICS_JSON_PATH,
    METRICS_REPORT_PATH,
    MODEL_ARTIFACT_PATH,
    save_artifacts,
    train_ltv_model,
)


def main() -> None:
    artifacts = train_ltv_model()
    save_artifacts(artifacts)
    print(
        json.dumps(
            {
                "model_artifact": MODEL_ARTIFACT_PATH,
                "metadata": METADATA_ARTIFACT_PATH,
                "metrics_json": METRICS_JSON_PATH,
                "metrics_report": METRICS_REPORT_PATH,
                "high_value_customers": HIGH_VALUE_CSV_PATH,
                "rows": len(artifacts.rows),
                "train_rows": len(artifacts.train_indices),
                "test_rows": len(artifacts.test_indices),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

