from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .domain import instant
from .security import initialise_accounts, new_session, token_hash, utcnow
from .service import OPERATIONS, Problem, Service
from .store import Store


ROOT = Path(__file__).resolve().parents[2]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Model):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=200)


class CreateWorkspace(Model):
    name: str = Field(default="Packaging qualification", min_length=1, max_length=100)
    scenario: Literal["S1", "S2", "S3"] = "S1"


class Command(Model):
    expected_context_revision: int = Field(ge=0)
    reason: str = Field(default="", max_length=2000)
    payload: dict


class Run(Model):
    run_id: str


class Context(Run):
    field: Literal["closure_lot_id", "bottle_lot_id", "config_id", "lineage"]
    value: str


class Study(Run):
    action_id: str | None = None


class Refresh(Run):
    complete: bool = True


class Advance(Model):
    hours: int = Field(ge=1, le=48)


class Calibrate(Model):
    instrument_id: str
    method_id: str = Field(min_length=3, max_length=100)
    basis: str = Field(min_length=10, max_length=1000)


class Revoke(Model):
    calibration_id: str
    effective_from: str
    effective_until: str


class Measure(Model):
    study_id: str
    calibration_id: str
    value: str = Field(max_length=40)
    unit: Literal["N_m"] = "N_m"
    half_width: str = Field(default="0.02", max_length=40)
    uncertainty_kind: Literal[
        "ENGINEERING_BOUND", "EXPANDED_UNCERTAINTY", "UNKNOWN"
    ] = "ENGINEERING_BOUND"
    basis: str = Field(
        default="Assumed engineering bound for synthetic software demonstration",
        min_length=10,
        max_length=500,
    )
    count: int = Field(default=3, ge=1, le=12)
    occurred_at: str | None = None


class Functional(Model):
    study_id: str
    outcome: Literal["PASS", "FAIL", "INCONCLUSIVE"]


class Note(Run):
    text: str = Field(min_length=1, max_length=2000)


class Investigate(Run):
    title: str = Field(min_length=3, max_length=150)
    problem_definition: str = Field(min_length=10, max_length=2000)


class Hypothesis(Model):
    investigation_id: str
    statement: str = Field(min_length=5, max_length=500)
    mechanism: str = Field(min_length=5, max_length=1000)
    supporting_ids: list[str] = Field(default_factory=list, max_length=30)
    refuting_ids: list[str] = Field(default_factory=list, max_length=30)


class Propose(Model):
    investigation_id: str
    config_id: str
    verification_plan: str = Field(min_length=10, max_length=1000)


class Action(Model):
    action_id: str


class Review(Run):
    decision_id: str
    fingerprint: str = Field(min_length=64, max_length=64)


class Authorize(Review):
    max_units: int = Field(default=20, ge=1, le=100)
    minutes: int = Field(default=15, ge=1, le=60)


class Produce(Run):
    units: int = Field(default=5, ge=1, le=100)


class Disposition(Model):
    unit_ids: list[str] = Field(min_length=1, max_length=100)
    disposition: Literal["HELD", "ACCEPTED", "REJECTED"]


class Correction(Model):
    evidence_id: str
    outcome: Literal["PASS", "FAIL", "INCONCLUSIVE"]


PAYLOADS = {
    "change_context": Context,
    "open_study": Study,
    "refresh_source": Refresh,
    "advance": Advance,
    "calibrate": Calibrate,
    "revoke_calibration": Revoke,
    "measure": Measure,
    "functional": Functional,
    "comment": Note,
    "investigate": Investigate,
    "hypothesis": Hypothesis,
    "propose_action": Propose,
    "approve_action": Action,
    "execute_action": Action,
    "assess_action": Action,
    "resolve_hold": Review,
    "authorize": Authorize,
    "produce": Produce,
    "disposition": Disposition,
    "correct_evidence": Correction,
    "complete_run": Run,
}


def create_app(db_path=None, credentials_path=None):
    path = Path(db_path or os.environ.get("QUALITYOS_DB", str(ROOT / "var/qualityos.sqlite")))
    store = Store(path)
    credentials = Path(credentials_path or path.parent / "local-credentials.json")
    initialise_accounts(store, credentials)
    service = Service(store)
    app = FastAPI(
        title="QualityOS",
        version="0.1.0",
        description="Synthetic evidence-to-decision workflow. Not commercial release or equipment control.",
    )
    app.state.store = store
    app.state.service = service

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        request_id = uuid4().hex[:12]
        request.state.request_id = request_id
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse(
                {"code": "INVALID_LENGTH", "message": "Invalid request length"}, 400
            )
        if length < 0:
            return JSONResponse(
                {"code": "INVALID_LENGTH", "message": "Invalid request length"}, 400
            )
        if length > 65536:
            return JSONResponse(
                {"code": "PAYLOAD_TOO_LARGE", "message": "Request exceeds 64 KiB"}, 413
            )
        host = request.headers.get("host", "").split(":")[0]
        if host not in {"127.0.0.1", "localhost", "testserver"}:
            return JSONResponse(
                {
                    "code": "HOST_FORBIDDEN",
                    "message": "This local application does not accept that host",
                },
                403,
            )
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin and origin not in {
                str(request.base_url).rstrip("/"),
                "http://127.0.0.1:8107",
                "http://127.0.0.1:5177",
                "http://localhost:8107",
                "http://localhost:5177",
                "http://testserver",
            }:
                return JSONResponse(
                    {"code": "ORIGIN_FORBIDDEN", "message": "Cross-origin writes are disabled"}, 403
                )
            chunks = []
            received = 0
            async for chunk in request.stream():
                received += len(chunk)
                if received > 65536:
                    return JSONResponse(
                        {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": "Request exceeds 64 KiB",
                            "request_id": request_id,
                        },
                        413,
                    )
                chunks.append(chunk)
            # Starlette's cached middleware request replays this bounded body
            # to the typed endpoint, including for chunked requests.
            request._body = b"".join(chunks)
        try:
            response = await call_next(request)
        except SQLAlchemyError:
            response = JSONResponse(
                {
                    "code": "STORE_UNAVAILABLE",
                    "message": "The store is unavailable; no permission was granted",
                    "request_id": request_id,
                },
                503,
            )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(Problem)
    async def problem_handler(request, exc):
        return JSONResponse(
            {
                "code": exc.code,
                "message": exc.message,
                "reason_codes": [exc.code],
                "evidence_refs": exc.refs,
                "request_id": request.state.request_id,
            },
            exc.status,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request, exc):
        return JSONResponse(
            {
                "code": "INVALID_REQUEST",
                "message": "Request fields do not match the API contract",
                "request_id": request.state.request_id,
                "fields": [
                    {"path": list(e["loc"]), "message": e["msg"]} for e in exc.errors()[:20]
                ],
            },
            422,
        )

    def actor(request, write=False):
        token = request.cookies.get("qualityos_session", "")
        with store.engine.connect() as c:
            row = (
                c.execute(
                    text(
                        "SELECT a.id,a.username,a.display_name,a.role,s.csrf_hash,s.expires_at FROM sessions s JOIN actors a ON a.id=s.actor_id WHERE s.token_hash=:t"
                    ),
                    {"t": token_hash(token)},
                )
                .mappings()
                .first()
            )
        if not row or instant(row["expires_at"]) <= instant(utcnow()):
            raise Problem("AUTH_REQUIRED", "Sign in to the local workspace", 401)
        if write and token_hash(request.headers.get("X-CSRF-Token", "")) != row["csrf_hash"]:
            raise Problem("CSRF_REQUIRED", "Refresh your authenticated session before writing", 403)
        return {k: row[k] for k in ["id", "username", "display_name", "role"]}

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "schema_version": 1, "mode": "LOCAL_SYNTHETIC", "version": "0.1.0"}

    @app.post("/api/v1/auth/session")
    def login(body: Login):
        value = new_session(store, body.username, body.password)
        if not value:
            raise Problem("INVALID_CREDENTIALS", "Username or password did not match", 401)
        token, csrf, user = value
        response = JSONResponse({"actor": user, "csrf_token": csrf})
        response.set_cookie(
            "qualityos_session", token, httponly=True, samesite="strict", max_age=8 * 3600, path="/"
        )
        response.set_cookie(
            "qualityos_csrf", csrf, httponly=False, samesite="strict", max_age=8 * 3600, path="/"
        )
        return response

    @app.get("/api/v1/auth/me")
    def me(request: Request):
        return {"actor": actor(request)}

    @app.delete("/api/v1/auth/session")
    def logout(request: Request):
        actor(request, True)
        with store.transaction() as c:
            c.execute(
                text("DELETE FROM sessions WHERE token_hash=:t"),
                {"t": token_hash(request.cookies.get("qualityos_session", ""))},
            )
        response = JSONResponse({"signed_out": True})
        response.delete_cookie("qualityos_session")
        response.delete_cookie("qualityos_csrf")
        return response

    @app.get("/api/v1/workspaces")
    def workspaces(request: Request):
        actor(request)
        with store.engine.connect() as c:
            return [
                dict(x)
                for x in c.execute(text("SELECT * FROM workspaces ORDER BY rowid DESC")).mappings()
            ]

    @app.post("/api/v1/demo/workspaces")
    def create_workspace(body: CreateWorkspace, request: Request):
        return service.create_workspace(actor(request, True), body.name, body.scenario)

    @app.get("/api/v1/workspaces/{wid}/snapshot")
    def snapshot(
        wid: str, request: Request, run_id: str | None = None, decision_id: str | None = None
    ):
        user = actor(request)
        result = service.snapshot(wid, run_id, decision_id)
        service.audit_read(wid, user, "SNAPSHOT_READ", result["decision"]["id"])
        return result

    @app.get("/api/v1/workspaces/{wid}/changes")
    def changes(wid: str, request: Request, after_seq: int = 0):
        actor(request)
        with store.engine.connect() as c:
            ws = service._workspace(c, wid)
            return {
                "domain_cursor": ws["cursor"],
                "changed": ws["cursor"] > after_seq,
                "context_revision": ws["revision"],
            }

    @app.post("/api/v1/workspaces/{wid}/commands/{operation}")
    def command(wid: str, operation: str, body: Command, request: Request):
        user = actor(request, True)
        if operation not in PAYLOADS:
            raise Problem("UNKNOWN_COMMAND", "Unsupported command", 422)
        key = request.headers.get("Idempotency-Key", "")
        if not 8 <= len(key) <= 200:
            raise Problem(
                "IDEMPOTENCY_KEY_REQUIRED", "An 8–200 character command key is required", 422
            )
        try:
            payload = PAYLOADS[operation].model_validate(body.payload).model_dump()
            for k in ["effective_from", "effective_until", "occurred_at"]:
                if payload.get(k):
                    instant(payload[k])
        except (ValidationError, ValueError) as exc:
            raise Problem("INVALID_COMMAND", str(exc)[:1000], 422)
        if (
            operation
            in {
                "resolve_hold",
                "authorize",
                "calibrate",
                "revoke_calibration",
                "propose_action",
                "approve_action",
                "execute_action",
                "assess_action",
                "correct_evidence",
                "disposition",
            }
            and len(body.reason.strip()) < 5
        ):
            raise Problem(
                "REASON_REQUIRED", "Provide a review reason of at least five characters", 422
            )
        try:
            return service.command(
                wid, user, operation, {**body.model_dump(), "payload": payload}, key
            )
        except (ValueError, KeyError) as exc:
            raise Problem("INVALID_COMMAND", str(exc)[:500], 422)

    @app.get("/api/v1/contracts")
    def contracts():
        return {key: model.model_json_schema() for key, model in PAYLOADS.items()}

    @app.get("/api/v1/workspaces/{wid}/export")
    def export(wid: str, request: Request):
        user = actor(request)
        snapshot = service.snapshot(wid)
        service.audit_read(wid, user, "EXPORT_READ", str(snapshot["workspace"]["cursor"]))
        with store.engine.connect() as c:
            cut = snapshot["workspace"]["cursor"]
            params = {"w": wid, "cut": cut}
            events = [
                dict(x)
                for x in c.execute(
                    text("SELECT * FROM events WHERE workspace_id=:w AND seq<=:cut ORDER BY seq"),
                    params,
                ).mappings()
            ]
            decisions = [
                dict(x)
                for x in c.execute(
                    text(
                        "SELECT * FROM decisions WHERE workspace_id=:w AND cut<=:cut ORDER BY cut,id"
                    ),
                    params,
                ).mappings()
            ]
            audit = [
                dict(x)
                for x in c.execute(
                    text("SELECT * FROM audit WHERE workspace_id=:w ORDER BY id"), {"w": wid}
                ).mappings()
            ]
        from .domain import digest

        return {
            "schema_version": 1,
            "provenance": "SYNTHETIC",
            "time_basis": "SCENARIO_UTC",
            "snapshot": snapshot,
            "events": events,
            "decisions": decisions,
            "audit_system_time": audit,
            "semantic_digest": digest(snapshot["records"]),
            "limits": "Software replay only; held is not defective or scrapped. No factory validation.",
        }

    @app.get("/api/v1/validation")
    def validation(request: Request):
        actor(request)
        with store.engine.connect() as c:
            row = c.execute(
                text("SELECT payload FROM reports ORDER BY created_at DESC LIMIT 1")
            ).first()
            return (
                json.loads(row.payload)
                if row
                else {
                    "status": "NOT_RUN",
                    "message": "Independent evaluation has not run for this store",
                }
            )

    @app.post("/api/v1/validation/run")
    def run_validation(request: Request):
        user = actor(request, True)
        if user["role"] not in {"QUALITY_ENGINEER", "ADMIN"}:
            raise Problem(
                "ROLE_REQUIRED", "Evaluation requires a quality engineer or administrator", 403
            )
        from .evaluation import run_evaluation

        return run_evaluation(store)

    dist = ROOT / "web/dist"
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}")
        def spa(path: str):
            if path.startswith("api/"):
                raise HTTPException(404)
            return FileResponse(dist / "index.html")

    return app
