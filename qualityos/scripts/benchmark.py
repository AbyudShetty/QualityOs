"""Declared 10k archived-event fixture; never writes to the user's demo store."""
import json
import os
import platform
import statistics
import time
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from qualityos.api import create_app
from qualityos.domain import canonical, digest
from qualityos.security import utcnow


ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "var/benchmarks" / uuid4().hex
out.mkdir(parents=True)
app = create_app(out / "benchmark.sqlite", out / "private.json")
client = TestClient(app)
credentials = json.loads((out / "private.json").read_text())
session = client.post(
    "/api/v1/auth/session", json={"username": "qa", "password": credentials["qa"]["password"]}
).json()
client.headers["X-CSRF-Token"] = session["csrf_token"]
wid = client.post("/api/v1/demo/workspaces", json={"name": "Declared 10k event benchmark"}).json()[
    "workspace_id"
]
store = app.state.store
with store.transaction() as c:
    clock = c.execute(text("SELECT clock FROM workspaces WHERE id=:w"), {"w": wid}).scalar()
    rows = []
    # Archived source receipts add no observations, units, permits or oracle labels.
    for n in range(9999):
        payload = {
            "changes": {},
            "detail": {"benchmark_archive_ordinal": n},
            "provenance": "SYNTHETIC",
            "time_basis": "SCENARIO_UTC",
            "schema_version": 1,
        }
        rows.append(
            {
                "id": "archive-" + uuid4().hex,
                "w": wid,
                "key": str(n),
                "clock": clock,
                "system": utcnow(),
                "payload": canonical(payload),
                "hash": digest(payload),
            }
        )
    c.execute(
        text(
            "INSERT INTO events(id,workspace_id,source_id,source_event_id,type,occurred_at,available_at,recorded_at,received_at_system_utc,actor_id,payload,payload_sha256) VALUES (:id,:w,'benchmark-archive',:key,'ARCHIVED_SOURCE_RECEIPT',:clock,:clock,:clock,:system,'qa',:payload,:hash)"
        ),
        rows,
    )
    cursor = c.execute(
        text("SELECT max(seq) FROM events WHERE workspace_id=:w"), {"w": wid}
    ).scalar()
    c.execute(
        text("UPDATE workspaces SET cursor=:cursor WHERE id=:w"), {"cursor": cursor, "w": wid}
    )
    entities = c.execute(
        text("SELECT count(*) FROM entities WHERE workspace_id=:w"), {"w": wid}
    ).scalar()


def sample(operation, n=40):
    values = []
    for i in range(n + 5):
        begin = time.perf_counter()
        response = operation(i)
        elapsed = (time.perf_counter() - begin) * 1000
        if response.status_code != 200:
            raise RuntimeError("Benchmark request failed: " + str(response.status_code))
        if i >= 5:
            values.append(elapsed)
    ranked = sorted(values)
    return {
        "samples": n,
        "warmup": 5,
        "p50_ms": round(statistics.median(values), 3),
        "p95_ms": round(ranked[int(0.95 * (len(ranked) - 1))], 3),
        "max_ms": round(max(values), 3),
    }


snapshot_url = f"/api/v1/workspaces/{wid}/snapshot"
read = sample(lambda _: client.get(snapshot_url))
rid = client.get(snapshot_url).json()["run"]["id"]


def write(i):
    snapshot = client.get(snapshot_url).json()  # Outside the timed command? See next function.
    return client.post(
        f"/api/v1/workspaces/{wid}/commands/comment",
        json={
            "expected_context_revision": snapshot["workspace"]["revision"],
            "reason": "Benchmark harmless review note",
            "payload": {"run_id": rid, "text": f"Declared benchmark review note {i}"},
        },
        headers={"Idempotency-Key": uuid4().hex},
    )


# Include read + command as an intentionally conservative user action round trip.
command = sample(write)
report = {
    "schema_version": 1,
    "created_at": utcnow(),
    "provenance": "SYNTHETIC",
    "basis": "In-process ASGI HTTP requests with authentication, serialization and SQLite; excludes TCP/browser rendering",
    "fixture": {
        "initial_events": 10000,
        "initial_entities": entities,
        "archive_events": 9999,
        "archive_changes_per_event": 0,
        "runs": 2,
        "command": "comment; includes preceding authenticated snapshot read",
        "history_query_limit": 100,
    },
    "environment": {
        "os": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
    },
    "snapshot": read,
    "read_and_comment": command,
    "under_500ms_p95": read["p95_ms"] < 500 and command["p95_ms"] < 500,
    "replay_matches": store.semantic_digest(wid) == store.replay_digest(wid),
    "limits": [
        "10k event rows, not 10k entities, units or stored decision snapshots",
        "No throughput, factory responsiveness, network, multiuser load or equipment guarantee",
        "Full JSON snapshots grow with the entity population; retention/pagination must be engineered before scaling",
    ],
}
(out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
(ROOT / "docs/validation/performance.json").parent.mkdir(parents=True, exist_ok=True)
(ROOT / "docs/validation/performance.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(json.dumps(report, indent=2))
