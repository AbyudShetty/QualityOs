"""SQLite registry, relational dependency edges, append-only facts and receipts."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, text

from .domain import canonical, digest


MIGRATIONS = [
    (
        1,
        [
            "CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)",
            "CREATE TABLE actors (id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('VIEWER','OPERATOR','QUALITY_ENGINEER','ADMIN')), password_hash TEXT NOT NULL)",
            "CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, actor_id TEXT NOT NULL REFERENCES actors(id), csrf_hash TEXT NOT NULL, expires_at TEXT NOT NULL)",
            "CREATE TABLE workspaces (id TEXT PRIMARY KEY, name TEXT NOT NULL, clock TEXT NOT NULL, mode TEXT NOT NULL CHECK(mode='SYNTHETIC_DEMO'), revision INTEGER NOT NULL CHECK(revision>=0), cursor INTEGER NOT NULL DEFAULT 0, scenario_version TEXT NOT NULL)",
            "CREATE TABLE entities (id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id), kind TEXT NOT NULL, data TEXT NOT NULL CHECK(json_valid(data)), UNIQUE(workspace_id,id))",
            "CREATE INDEX entities_workspace_kind ON entities(workspace_id,kind)",
            "CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, workspace_id TEXT NOT NULL REFERENCES workspaces(id), source_id TEXT NOT NULL, source_event_id TEXT NOT NULL, type TEXT NOT NULL, occurred_at TEXT NOT NULL, available_at TEXT NOT NULL, recorded_at TEXT NOT NULL, received_at_system_utc TEXT NOT NULL, actor_id TEXT NOT NULL REFERENCES actors(id), payload TEXT NOT NULL CHECK(json_valid(payload)), payload_sha256 TEXT NOT NULL, UNIQUE(workspace_id,source_id,source_event_id))",
            "CREATE INDEX events_workspace_seq ON events(workspace_id,seq)",
            "CREATE TABLE edges (id INTEGER PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id), from_id TEXT NOT NULL, relation TEXT NOT NULL, to_id TEXT NOT NULL, source_event_id TEXT NOT NULL REFERENCES events(id), FOREIGN KEY(workspace_id,from_id) REFERENCES entities(workspace_id,id), FOREIGN KEY(workspace_id,to_id) REFERENCES entities(workspace_id,id), UNIQUE(workspace_id,from_id,relation,to_id,source_event_id))",
            "CREATE INDEX edges_reverse ON edges(workspace_id,to_id,relation)",
            "CREATE TABLE decisions (id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id), run_id TEXT NOT NULL REFERENCES entities(id), cut INTEGER NOT NULL, evaluated_at TEXT NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)))",
            "CREATE INDEX decisions_run_cut ON decisions(run_id,cut)",
            "CREATE TABLE receipts (workspace_id TEXT NOT NULL REFERENCES workspaces(id), actor_id TEXT NOT NULL REFERENCES actors(id), namespace TEXT NOT NULL, key TEXT NOT NULL, request_hash TEXT NOT NULL, response TEXT NOT NULL CHECK(json_valid(response)), PRIMARY KEY(workspace_id,actor_id,namespace,key))",
            "CREATE TABLE audit (id INTEGER PRIMARY KEY AUTOINCREMENT, workspace_id TEXT, actor_id TEXT, action TEXT NOT NULL, outcome TEXT NOT NULL, system_at TEXT NOT NULL, detail TEXT NOT NULL)",
            "CREATE TABLE reports (id TEXT PRIMARY KEY, payload TEXT NOT NULL CHECK(json_valid(payload)), created_at TEXT NOT NULL)",
            "CREATE TRIGGER events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'events are append-only'); END",
            "CREATE TRIGGER events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'events are append-only'); END",
            "CREATE TRIGGER decisions_no_update BEFORE UPDATE ON decisions BEGIN SELECT RAISE(ABORT,'decisions are immutable'); END",
            "CREATE TRIGGER decisions_no_delete BEFORE DELETE ON decisions BEGIN SELECT RAISE(ABORT,'decisions are immutable'); END",
            "CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'audit is append-only'); END",
            "CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'audit is append-only'); END",
        ],
    )
]


class Store:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            "sqlite:///" + str(self.path), connect_args={"check_same_thread": False, "timeout": 5}
        )

        @event.listens_for(self.engine, "connect")
        def configure(db, _):
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("PRAGMA journal_mode=WAL")

        self.migrate()

    @contextmanager
    def transaction(self):
        with self.engine.connect() as conn:
            conn.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def migrate(self):
        from .security import utcnow

        with self.transaction() as c:
            exists = c.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE name='schema_version'"
            ).first()
            current = (
                c.exec_driver_sql("SELECT coalesce(max(version),0) FROM schema_version").scalar()
                if exists
                else 0
            )
            if current > MIGRATIONS[-1][0]:
                raise RuntimeError("Database schema is newer than this application")
            for version, statements in MIGRATIONS:
                if version > current:
                    for sql in statements:
                        c.exec_driver_sql(sql)
                    c.execute(
                        text("INSERT INTO schema_version VALUES (:v,:at)"),
                        {"v": version, "at": utcnow()},
                    )

    def records(self, conn, wid):
        return {
            row.id: json.loads(row.data)
            for row in conn.execute(
                text("SELECT id,data FROM entities WHERE workspace_id=:w"), {"w": wid}
            )
        }

    def put(self, conn, wid, record):
        conn.execute(
            text(
                "INSERT INTO entities(id,workspace_id,kind,data) VALUES (:id,:w,:kind,:data) ON CONFLICT(id) DO UPDATE SET data=excluded.data"
            ),
            {"id": record["id"], "w": wid, "kind": record["kind"], "data": canonical(record)},
        )

    def semantic_digest(self, wid):
        with self.engine.connect() as c:
            return digest(self.records(c, wid))

    def replay_digest(self, wid):
        records = {}
        with self.engine.connect() as c:
            for row in c.execute(
                text("SELECT payload FROM events WHERE workspace_id=:w ORDER BY seq"), {"w": wid}
            ):
                records.update(json.loads(row.payload)["changes"])
        return digest(records)
