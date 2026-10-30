from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    return (
        salt
        + ":"
        + hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()
    )


def password_ok(password, encoded):
    return hmac.compare_digest(password_hash(password, encoded.split(":")[0]), encoded)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def initialise_accounts(store, credentials_path):
    """Only first local setup; private random credentials never returned by API."""
    credentials = {}
    with store.transaction() as c:
        if c.execute(text("SELECT count(*) FROM actors")).scalar():
            return
        for username, role, name in [
            ("qa", "QUALITY_ENGINEER", "Maya Rao"),
            ("operator", "OPERATOR", "Alex Morgan"),
            ("viewer", "VIEWER", "Review visitor"),
            ("admin", "ADMIN", "Local administrator"),
        ]:
            password = secrets.token_urlsafe(18)
            c.execute(
                text("INSERT INTO actors VALUES (:id,:u,:n,:r,:p)"),
                {"id": username, "u": username, "n": name, "r": role, "p": password_hash(password)},
            )
            credentials[username] = {"password": password, "role": role}
        p = Path(credentials_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation: never overwrite an existing credential record.
        with p.open("x", encoding="utf-8") as f:
            json.dump(credentials, f, indent=2)


def new_session(store, username, password):
    with store.transaction() as c:
        actor = (
            c.execute(text("SELECT * FROM actors WHERE username=:u"), {"u": username})
            .mappings()
            .first()
        )
        if not actor or not password_ok(password, actor["password_hash"]):
            return None
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
        c.execute(
            text("INSERT INTO sessions VALUES (:t,:a,:c,:e)"),
            {"t": token_hash(token), "a": actor["id"], "c": token_hash(csrf), "e": expires},
        )
        return token, csrf, {k: actor[k] for k in ["id", "display_name", "role", "username"]}
