import json
from pathlib import Path

from pw_sdk.models import CustomerRecord, OutcomeEvent
from pw_sdk.version import SCHEMA_VERSION

MODELS = {"customer_record": CustomerRecord, "outcome_event": OutcomeEvent}


def json_schemas() -> dict[str, dict]:
    return {f"{name}.v{SCHEMA_VERSION}.json": model.model_json_schema() for name, model in MODELS.items()}


def write_schemas(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for filename, schema in json_schemas().items():
        path = directory / filename
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
        written.append(path)
    return written
