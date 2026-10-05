"""Opaque server-side sessions, standard Argon2id and browser mutation guards."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, Request
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError
from sqlalchemy import delete, func, insert, select, text

from medifind.tables import pharmacies, sessions, users

COOKIE = "medifind_session"
HASHER = PasswordHash.recommended()
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))


def fail(status: int, code: str, message: str):
    raise HTTPException(status, detail={"code": code, "message": message})


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def password_hash(password: str) -> str:
    if not 12 <= len(password) <= 128 or password.isspace():
        raise ValueError("Provisioned password must contain 12-128 characters")
    return HASHER.hash(password)


def provision(connection, profile: dict, username: str, password: str):
    """Private operator path only; never public registration."""
    hashed = password_hash(password)
    pharmacy_id, user_id = uuid4(), uuid4()
    connection.execute(insert(pharmacies).values(id=pharmacy_id, synthetic=True, **profile))
    connection.execute(
        insert(users).values(
            id=user_id,
            pharmacy_id=pharmacy_id,
            username=username,
            password_hash=hashed,
        )
    )
    return pharmacy_id


def browser_origin(request: Request):
    if request.headers.get("origin") != request.app.state.settings.browser_origin:
        fail(403, "origin_denied", "Browser origin is not allowed")
    if request.headers.get("sec-fetch-site") == "cross-site":
        fail(403, "origin_denied", "Cross-site mutation is not allowed")


def database(request: Request):
    with request.app.state.engine.begin() as connection:
        yield connection


def authenticate(request: Request, connection):
    token = request.cookies.get(COOKIE, "")
    if not 32 <= len(token) <= 128:
        fail(401, "authentication_required", "Authentication required")
    row = (
        connection.execute(
            select(
                sessions.c.token_hash,
                sessions.c.csrf_token,
                sessions.c.expires_at,
                users.c.id.label("user_id"),
                users.c.username,
                users.c.pharmacy_id,
            )
            .select_from(
                sessions.join(users, sessions.c.user_id == users.c.id).join(
                    pharmacies,
                    users.c.pharmacy_id == pharmacies.c.id,
                )
            )
            .where(
                sessions.c.token_hash == token_hash(token),
                sessions.c.expires_at > func.now(),
                users.c.active.is_(True),
                pharmacies.c.active.is_(True),
            )
        )
        .mappings()
        .first()
    )
    if row is None:
        fail(401, "authentication_required", "Authentication required")
    return row


def mutate(request: Request, connection):
    auth = authenticate(request, connection)
    browser_origin(request)
    if not secrets.compare_digest(
        request.headers.get("x-csrf-token", "").encode("utf-8"), auth["csrf_token"].encode("ascii")
    ):
        fail(403, "csrf_denied", "Valid CSRF token required")
    return auth


def own(pharmacy_id, auth):
    if pharmacy_id != auth["pharmacy_id"]:
        fail(403, "ownership_denied", "Pharmacy ownership required")


def login(request: Request, body, response):
    browser_origin(request)
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        fail(415, "json_required", "JSON request required")
    engine = request.app.state.engine
    key = token_hash(request.client.host if request.client else "unknown")
    # Commit attempts even on failed authentication; row upsert serializes counters across workers.
    with engine.begin() as connection:
        attempts = connection.scalar(
            text("""
            INSERT INTO login_limits(key,attempts,reset_at)
            VALUES (:key,1,clock_timestamp()+interval '1 minute')
            ON CONFLICT(key) DO UPDATE SET
                attempts=CASE WHEN login_limits.reset_at<=clock_timestamp()
                    THEN 1 ELSE login_limits.attempts+1 END,
                reset_at=CASE WHEN login_limits.reset_at<=clock_timestamp()
                    THEN clock_timestamp()+interval '1 minute' ELSE login_limits.reset_at END
            RETURNING attempts
        """),
            {"key": key},
        )
    if attempts > 20:
        fail(429, "login_throttled", "Too many login attempts; retry later")
    with engine.begin() as connection:
        user = (
            connection.execute(select(users).where(users.c.username == body.username))
            .mappings()
            .first()
        )
        stored = user["password_hash"] if user else DUMMY_HASH
        try:
            valid = HASHER.verify(body.password.get_secret_value(), stored)
        except PwdlibError:
            valid = False
        active = user and connection.scalar(
            select(pharmacies.c.active).where(
                pharmacies.c.id == user["pharmacy_id"],
            )
        )
        if not valid or not user or not user["active"] or not active:
            fail(401, "invalid_credentials", "Invalid credentials")
        # Rotate current browser session; cleanup expired sessions on successful login.
        connection.execute(delete(sessions).where(sessions.c.expires_at <= func.now()))
        previous = request.cookies.get(COOKIE, "")
        connection.execute(delete(sessions).where(sessions.c.token_hash == token_hash(previous)))
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        expires = now + timedelta(hours=request.app.state.settings.session_hours)
        connection.execute(
            insert(sessions).values(
                token_hash=token_hash(token),
                user_id=user["id"],
                csrf_token=csrf,
                created_at=now,
                expires_at=expires,
            )
        )
    response.set_cookie(
        COOKIE,
        token,
        max_age=request.app.state.settings.session_hours * 3600,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
        path="/",
    )
    return {
        "pharmacy_id": user["pharmacy_id"],
        "username": user["username"],
        "csrf_token": csrf,
        "expires_at": expires,
    }
