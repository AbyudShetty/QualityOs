"""Fresh real HTTP process, committed-response retry after abrupt restart."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "var/restart-checks" / uuid4().hex
out.mkdir(parents=True)
environment = {
    **os.environ,
    "PYTHONPATH": str(ROOT / "backend"),
    "QUALITYOS_DB": str(out / "recovery.sqlite"),
}
client = httpx.Client(base_url="http://127.0.0.1:8109", trust_env=False, timeout=10)
process = None
log = (out / "server.log").open("w", encoding="utf-8")


def start():
    global process
    process = subprocess.Popen(
        [sys.executable, "-m", "qualityos", "serve", "--port", "8109"],
        cwd=ROOT,
        env=environment,
        stdout=log,
        stderr=log,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError("Dedicated recovery server exited; inspect its private local log")
        try:
            if client.get("/api/v1/health").status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.15)
    raise RuntimeError("Dedicated recovery server did not become healthy")


def ok(response):
    if response.status_code != 200:
        raise RuntimeError("Recovery request failed: " + str(response.status_code))
    return response.json()


try:
    start()
    credentials = json.loads((out / "local-credentials.json").read_text())
    session = ok(
        client.post(
            "/api/v1/auth/session",
            json={"username": "qa", "password": credentials["qa"]["password"]},
        )
    )
    client.headers["X-CSRF-Token"] = session["csrf_token"]
    wid = ok(client.post("/api/v1/demo/workspaces", json={"name": "Fresh process recovery"}))[
        "workspace_id"
    ]
    url = f"/api/v1/workspaces/{wid}"
    s = ok(client.get(url + "/snapshot"))
    permit = {
        "expected_context_revision": s["workspace"]["revision"],
        "reason": "Review current synthetic scope",
        "payload": {
            "run_id": s["run"]["id"],
            "decision_id": s["decision"]["id"],
            "fingerprint": s["decision"]["applicability_fingerprint"],
        },
    }
    ok(
        client.post(
            url + "/commands/authorize", json=permit, headers={"Idempotency-Key": uuid4().hex}
        )
    )
    s = ok(client.get(url + "/snapshot"))
    body = {
        "expected_context_revision": s["workspace"]["revision"],
        "reason": "Actual process restart recovery",
        "payload": {"run_id": s["run"]["id"], "units": 3},
    }
    key = uuid4().hex
    original = ok(
        client.post(url + "/commands/produce", json=body, headers={"Idempotency-Key": key})
    )
    original_digest = ok(client.get(url + "/export"))["semantic_digest"]
    if "QualityOS" not in client.get("/line").text:
        raise RuntimeError("Built SPA not served")
    process.terminate()
    process.wait(timeout=10)
    process = None
    start()
    retry = ok(client.post(url + "/commands/produce", json=body, headers={"Idempotency-Key": key}))
    restored = ok(client.get(url + "/snapshot"))
    restored_digest = ok(client.get(url + "/export"))["semantic_digest"]
    units = [x for x in restored["records"].values() if x["kind"] == "unit"]
    if (
        len(units) != 3
        or not retry.get("replayed")
        or retry["event_id"] != original["event_id"]
        or original_digest != restored_digest
    ):
        raise RuntimeError("Durability/idempotency mismatch")
    report = {
        "provenance": "SYNTHETIC",
        "completed_at": __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat(),
        "checks": [
            "Fresh schema and random accounts",
            "Real HTTP authentication",
            "Built SPA served",
            "QA permission and three committed units",
            "Dedicated process terminated after commit",
            "Same store restarted in a new process",
            "Persisted session and receipt replayed",
            "Exactly three units and matching semantic digest",
        ],
        "passed": True,
        "semantic_digest": restored_digest,
        "limits": "One process failure after a completed transaction; before-commit rollback is tested separately. Not a power-loss or filesystem fault trial.",
    }
    (ROOT / "docs/validation/recovery.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        "PASS: fresh launch and actual process restart; same three units, receipt and semantic digest."
    )
finally:
    if process is not None:
        process.terminate()
        process.wait(timeout=10)
    client.close()
    log.close()
