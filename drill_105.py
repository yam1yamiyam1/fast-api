# =============================================================================
# CONCEPT INTRO — Refresh Token Pattern
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# Access tokens are short-lived (minutes). If they lasted forever, a stolen
# token would give permanent access. The refresh token pattern solves this:
#   - Access token: short-lived (e.g. 15 min), used on every API call
#   - Refresh token: long-lived (e.g. 7 days), used ONLY to get a new access token
#
# The client never re-sends credentials after login — it uses the refresh
# token to silently renew the access token when it expires.
#
# TWO TOKEN TYPES — enforced by a "type" claim
# ---------------------------------------------
# Both tokens are JWTs. You distinguish them by embedding a "type" claim:
#
#   access token payload:  {"sub": "alice", "type": "access",  "exp": ...}
#   refresh token payload: {"sub": "alice", "type": "refresh", "exp": ...}
#
# When validating, check that the type claim matches what the endpoint expects.
# A refresh token presented to a protected route must be rejected (wrong type).
#
# THE FLOW
# --------
#   POST /token          — user sends username+password, gets access+refresh tokens
#   GET  /protected      — user sends access token in Authorization header
#   POST /refresh        — user sends refresh token in Authorization header,
#                          gets a NEW access token (and optionally a new refresh token)
#
# NEW CONCEPT — verifying token type
# ------------------------------------
# Nothing new to import. The novelty is checking payload["type"] after decode:
#
#   def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
#       try:
#           payload = jwt.decode(token, SECRET, algorithms=["HS256"])
#       except JWTError:
#           raise HTTPException(401, detail="invalid token")
#       if payload.get("type") != "access":
#           raise HTTPException(401, detail="invalid token")
#       return User(username=payload["sub"])
#
#   def get_refresh_user(token: str = Depends(oauth2_scheme)) -> User:
#       try:
#           payload = jwt.decode(token, SECRET, algorithms=["HS256"])
#       except JWTError:
#           raise HTTPException(401, detail="invalid token")
#       if payload.get("type") != "refresh":
#           raise HTTPException(401, detail="invalid token")
#       return User(username=payload["sub"])
#
# WIRING EXAMPLE
# --------------
# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer
# from fastapi.testclient import TestClient
# from jose import jwt, JWTError
# from pydantic import BaseModel
# from datetime import datetime, timezone, timedelta
#
# SECRET = "secret"
# app = FastAPI()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
#
# class User(BaseModel):
#     username: str
#
# def make_access_token(username: str, secret: str) -> str:
#     exp = datetime.now(timezone.utc) + timedelta(minutes=15)
#     return jwt.encode({"sub": username, "type": "access", "exp": exp},
#                       secret, algorithm="HS256")
#
# def make_refresh_token(username: str, secret: str) -> str:
#     exp = datetime.now(timezone.utc) + timedelta(days=7)
#     return jwt.encode({"sub": username, "type": "refresh", "exp": exp},
#                       secret, algorithm="HS256")
#
# def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
#     try:
#         payload = jwt.decode(token, SECRET, algorithms=["HS256"])
#     except JWTError:
#         raise HTTPException(401, detail="invalid token")
#     if payload.get("type") != "access":
#         raise HTTPException(401, detail="invalid token")
#     return User(username=payload["sub"])
#
# def get_refresh_user(token: str = Depends(oauth2_scheme)) -> User:
#     try:
#         payload = jwt.decode(token, SECRET, algorithms=["HS256"])
#     except JWTError:
#         raise HTTPException(401, detail="invalid token")
#     if payload.get("type") != "refresh":
#         raise HTTPException(401, detail="invalid token")
#     return User(username=payload["sub"])
#
# @app.post("/refresh")
# def refresh(user: User = Depends(get_refresh_user)):
#     return {"access_token": make_access_token(user.username, SECRET)}
#
# @app.get("/me")
# def me(user: User = Depends(get_current_user)):
#     return user
# =============================================================================


def run_drill_105():
    # =========================================================================
    # SCENARIO: Weather Station
    #
    # A weather station API lets registered meteorologists read sensor
    # readings. Login issues both an access token and a refresh token.
    # The access token is short-lived; the refresh token can be used to
    # obtain a new access token without logging in again.
    # Presenting a refresh token to a protected route must be rejected.
    # Presenting an access token to the refresh route must be rejected.
    #
    # REQUIREMENTS
    # ------------
    # 1. SECRET_KEY: str
    #       The HS256 signing secret. Value: "wx-secret"
    #
    # 2. APP_STATE: dict
    #       Shared state dict, starts empty.
    #       Lifespan loads APP_STATE["secret"] = SECRET_KEY at startup
    #       and clears at shutdown.
    #
    # 3. USERS: dict[str, str]
    #       In-memory map from username to password.
    #       Represents registered meteorologist credentials.
    #       Pre-populate with:
    #         {"alice": "pw-alice", "bob": "pw-bob"}
    #
    # 4. READINGS: list[dict]
    #       In-memory list of sensor readings.
    #       Pre-populate with:
    #         [
    #           {"id": 1, "location": "north", "temp_c": 18, "humidity": 72},
    #           {"id": 2, "location": "south", "temp_c": 25, "humidity": 55},
    #         ]
    #
    # 5. ReadingOut: BaseModel
    #       Response schema for a sensor reading.
    #       Fields: id: int, location: str, temp_c: int
    #       (humidity intentionally excluded)
    #
    # 6. User: BaseModel
    #       Fields: username: str
    #
    # 7. lifespan: asynccontextmanager
    #       Startup: APP_STATE["secret"] = SECRET_KEY
    #       Shutdown: APP_STATE.clear()
    #       Passed to FastAPI(lifespan=lifespan)
    #
    # 8. oauth2_scheme: OAuth2PasswordBearer(tokenUrl="/token")
    #
    # 9. make_access_token(username: str, secret: str) -> str
    #       username : str — the meteorologist's username, embedded as "sub".
    #       secret   : str — the signing key.
    #       Encodes {"sub": username, "type": "access",
    #                "exp": utc_now + 15 minutes} with HS256.
    #       Returns the encoded JWT string.
    #
    # 10. make_refresh_token(username: str, secret: str) -> str
    #       username : str — the meteorologist's username, embedded as "sub".
    #       secret   : str — the signing key.
    #       Encodes {"sub": username, "type": "refresh",
    #                "exp": utc_now + 7 days} with HS256.
    #       Returns the encoded JWT string.
    #
    # 11. get_current_user(token: str) -> User
    #       token: str — raw bearer token from Authorization header,
    #                    representing the caller's access credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes token using APP_STATE["secret"] and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError
    #       OR if payload["type"] != "access".
    #       Returns User(username=payload["sub"])
    #
    # 12. get_refresh_user(token: str) -> User
    #       token: str — raw bearer token from Authorization header,
    #                    representing the caller's refresh credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes token using APP_STATE["secret"] and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError
    #       OR if payload["type"] != "refresh".
    #       Returns User(username=payload["sub"])
    #
    # 13. POST /token
    #       Query params:
    #         username: str — the meteorologist's username credential.
    #         password: str — the meteorologist's password credential.
    #       No auth required.
    #       Raises HTTPException(401, detail="invalid credentials") if
    #       username not in USERS or USERS[username] != password.
    #       Returns {"access_token": <access_token>,
    #                "refresh_token": <refresh_token>}
    #       Both tokens signed with APP_STATE["secret"].
    #
    # 14. POST /refresh
    #       Protected by: get_refresh_user — refresh token only
    #       Returns {"access_token": <new_access_token>}
    #       New access token signed with APP_STATE["secret"].
    #
    # 15. GET /readings
    #       Protected by: get_current_user — access token only
    #       response_model: list[ReadingOut]
    #       Returns all readings. humidity must be stripped.
    # =========================================================================

    from contextlib import asynccontextmanager  # noqa: F401
    from datetime import datetime, timedelta, timezone  # noqa: F401

    from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
    from fastapi.security import OAuth2PasswordBearer  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from jose import JWTError, jwt  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---
    SECRET_KEY: str = "wx-secret"
    ALGO: str = "HS256"
    APP_STATE: dict = {}
    USERS: dict[str, str] = {"alice": "pw-alice", "bob": "pw-bob"}
    READINGS: list[dict] = [
        {"id": 1, "location": "north", "temp_c": 18, "humidity": 72},
        {"id": 2, "location": "south", "temp_c": 25, "humidity": 55},
    ]

    class ReadingOut(BaseModel):
        id: int
        location: str
        temp_c: int

    class User(BaseModel):
        username: str

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        APP_STATE["secret"] = SECRET_KEY
        yield
        APP_STATE.clear()

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def make_access_token(username: str, secret: str):
        return jwt.encode(
            claims={
                "sub": username,
                "type": "access",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            },
            key=secret,
            algorithm=ALGO,
        )

    def make_refresh_token(username: str, secret: str):
        return jwt.encode(
            claims={
                "sub": username,
                "type": "refresh",
                "exp": datetime.now(timezone.utc) + timedelta(days=7),
            },
            key=secret,
            algorithm=ALGO,
        )

    def get_current_user(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(
                token=token, key=APP_STATE["secret"], algorithms=[ALGO]
            )
            if payload["type"] != "access":
                raise JWTError
            return User(username=payload["sub"])
        except JWTError:
            raise HTTPException(401, detail="invalid token")

    def get_refresh_user(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(
                token=token, key=APP_STATE["secret"], algorithms=[ALGO]
            )
            if payload["type"] != "refresh":
                raise JWTError
            return User(username=payload["sub"])
        except JWTError:
            raise HTTPException(401, detail="invalid token")

    app = FastAPI(lifespan=lifespan)

    @app.post("/token")
    def create_atoken(username: str, password: str):
        if USERS.get(username) == password:
            args = (username, APP_STATE["secret"])
            return {
                "access_token": make_access_token(*args),
                "refresh_token": make_refresh_token(*args),
            }
        raise HTTPException(401, detail="invalid credentials")

    @app.post("/refresh")
    def create_rtoken(user: User = Depends(get_refresh_user)):
        args = (user.username, APP_STATE["secret"])
        return {"access_token": make_access_token(*args)}

    @app.get("/readings", response_model=list[ReadingOut])
    def get_readings(_=Depends(get_current_user)):
        return READINGS

    # ── Tests ─────────────────────────────────────────────────────────────────

    with TestClient(app) as client:
        # Test 1: login returns access and refresh tokens
        print("Test 1: valid login returns both tokens")
        r = client.post("/token?username=alice&password=pw-alice")
        assert r.status_code == 200
        tokens = r.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access = tokens["access_token"]
        refresh = tokens["refresh_token"]
        print(
            f"  access_token present: {'access_token' in tokens}, refresh_token present: {'refresh_token' in tokens}"
        )
        print("  PASS")

        # Test 2: invalid credentials → 401
        print("Test 2: wrong password -> 401")
        r = client.post("/token?username=alice&password=wrong")
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid credentials"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 3: access token works on /readings
        print("Test 3: access token reads sensor data")
        r = client.get("/readings", headers={"Authorization": f"Bearer {access}"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert all("humidity" not in d for d in data)
        print(
            f"  readings: {len(data)}, humidity stripped: {all('humidity' not in d for d in data)}"
        )
        print("  PASS")

        # Test 4: refresh token rejected on /readings → 401
        print("Test 4: refresh token rejected on protected route -> 401")
        r = client.get("/readings", headers={"Authorization": f"Bearer {refresh}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 5: refresh token issues new access token
        print("Test 5: refresh token issues new access token")
        r = client.post("/refresh", headers={"Authorization": f"Bearer {refresh}"})
        assert r.status_code == 200
        new_tokens = r.json()
        assert "access_token" in new_tokens
        new_access = new_tokens["access_token"]
        print(f"  new access_token present: {'access_token' in new_tokens}")
        print("  PASS")

        # Test 6: new access token works on /readings
        print("Test 6: new access token works on protected route")
        r = client.get("/readings", headers={"Authorization": f"Bearer {new_access}"})
        assert r.status_code == 200
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 7: access token rejected on /refresh → 401
        print("Test 7: access token rejected on refresh route -> 401")
        r = client.post("/refresh", headers={"Authorization": f"Bearer {access}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 8: missing token → 401
        print("Test 8: missing token on /readings -> 401")
        r = client.get("/readings")
        assert r.status_code == 401
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 9: unknown user → 401
        print("Test 9: unknown username -> 401")
        r = client.post("/token?username=nobody&password=x")
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid credentials"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")


run_drill_105()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: valid login returns both tokens
#   access_token present: True, refresh_token present: True
#   PASS
# Test 2: wrong password → 401
#   status: 401, detail: invalid credentials
#   PASS
# Test 3: access token reads sensor data
#   readings: 2, humidity stripped: True
#   PASS
# Test 4: refresh token rejected on protected route → 401
#   status: 401, detail: invalid token
#   PASS
# Test 5: refresh token issues new access token
#   new access_token present: True
#   PASS
# Test 6: new access token works on protected route
#   status: 200
#   PASS
# Test 7: access token rejected on refresh route → 401
#   status: 401, detail: invalid token
#   PASS
# Test 8: missing token on /readings → 401
#   status: 401
#   PASS
# Test 9: unknown username → 401
#   status: 401, detail: invalid credentials
#   PASS
# =============================================================================
