"""Generate reviewed API artifacts without changing the active runtime store."""
import json
from pathlib import Path
from uuid import uuid4

from qualityos.api import PAYLOADS, create_app

root = Path(__file__).resolve().parents[1]
scratch = root / "var/contract-builds" / uuid4().hex
app = create_app(scratch / "contracts.sqlite", scratch / "private.json")
output = root / "docs/contracts"
output.mkdir(parents=True, exist_ok=True)
(output / "openapi.json").write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
(output / "commands.json").write_text(
    json.dumps({k: v.model_json_schema() for k, v in PAYLOADS.items()}, indent=2), encoding="utf-8"
)
print("Generated OpenAPI and typed command schemas; no credentials included.")
