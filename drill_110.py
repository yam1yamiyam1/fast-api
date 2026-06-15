# =============================================================================
# CONCEPT INTRO — Final Boss: JWT + Roles + Scopes in One System
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# This drill introduces no new syntax. It combines everything from D101–109
# into one cohesive system:
#   - D101 OAuth2PasswordBearer       — extract token
#   - D102 JWT decode (python-jose)   — verify signature/expiry
#   - D103 User model + chained deps  — token → User
#   - D104 require_role factory       — role gating
#   - D105 access/refresh token types — login + refresh flow
#   - D106-107 (not reused here)
#   - D108 require_scope factory      — fine-grained permission gating
#   - D109 global middleware          — public path exception
#
# THE COMBINED PATTERN
# ---------------------
# A user has BOTH a role (coarse: "operator"/"admin") AND scopes (fine:
# ["telemetry:read", "commands:write"]). An endpoint may require:
#   - just authentication (any valid access token)
#   - a specific role
#   - a specific scope
#   - role AND scope together (stack two Depends() role/scope checkers
#     by chaining — the second dep takes the first dep's User as input)
#
# STACKING ROLE + SCOPE
# -----------------------
#   def require_role_and_scope(role: str, scope: str):
#       def checker(user: User = Depends(get_current_user)) -> User:
#           if user.role != role:
#               raise HTTPException(403, detail="forbidden")
#           if scope not in user.scopes:
#               raise HTTPException(403, detail="insufficient scope")
#           return user
#       return checker
#
# No new imports, no new classes — pure composition of D101-109 patterns.
# This drill is entirely about wiring everything together correctly.
# =============================================================================


def run_drill_110():
    # =========================================================================
    # SCENARIO: Mission Control
    #
    # A mission control API serves flight directors, operators, and analysts.
    # Authentication is JWT-based with access/refresh token types (D105).
    # Each user has a role ("director", "operator", "analyst") AND a list
    # of scopes (e.g. "telemetry:read", "commands:write"). A global
    # middleware (D109) requires an API key on all paths except /health
    # and /token. Individual routes additionally enforce role and/or scope
    # requirements via chained dependencies.
    #
    # REQUIREMENTS
    # ------------
    # 1. SECRET_KEY: str
    #       The HS256 signing secret. Value: "mission-secret"
    #
    # 2. APP_STATE: dict
    #       Shared state dict, starts empty.
    #       Lifespan loads APP_STATE["secret"] = SECRET_KEY at startup
    #       and clears at shutdown.
    #
    # 3. VALID_API_KEYS: set[str]
    #       Set of valid global API keys.
    #       Pre-populate with: {"mc-key-1"}
    #
    # 4. PUBLIC_PATHS: set[str]
    #       Paths that bypass the API-key middleware.
    #       Value: {"/health", "/token"}
    #
    # 5. USERS: dict[str, dict]
    #       In-memory map from username to user record.
    #       Represents registered mission control staff.
    #       Pre-populate with:
    #         "director-rao": {"password": "pw-rao", "role": "director",
    #                           "scopes": ["telemetry:read", "commands:write"]}
    #         "op-lee":       {"password": "pw-lee", "role": "operator",
    #                           "scopes": ["telemetry:read", "commands:write"]}
    #         "analyst-fox":  {"password": "pw-fox", "role": "analyst",
    #                           "scopes": ["telemetry:read"]}
    #
    # 6. TELEMETRY: list[dict]
    #       In-memory list of telemetry records.
    #       Pre-populate with:
    #         [
    #           {"id": 1, "metric": "altitude", "value": 408.2, "internal_sensor_id": "S-100"},
    #           {"id": 2, "metric": "velocity", "value": 7.66,  "internal_sensor_id": "S-200"},
    #         ]
    #
    # 7. COMMAND_LOG: list[dict]
    #       In-memory list of issued commands. Starts empty.
    #
    # 8. TelemetryOut: BaseModel
    #       Response schema for a telemetry record.
    #       Fields: id: int, metric: str, value: float
    #       (internal_sensor_id intentionally excluded)
    #
    # 9. CommandIn: BaseModel
    #       Request body for issuing a command.
    #       Fields: action: str — the command instruction to send,
    #                             representing what mission control wants
    #                             the spacecraft to do (e.g. "adjust-attitude").
    #
    # 10. CommandOut: BaseModel
    #       Response schema for an issued command.
    #       Fields: id: int, action: str, issued_by: str
    #
    # 11. User: BaseModel
    #       Fields: username: str, role: str, scopes: list[str]
    #
    # 12. lifespan: asynccontextmanager
    #       Startup: APP_STATE["secret"] = SECRET_KEY
    #       Shutdown: APP_STATE.clear()
    #       Passed to FastAPI(lifespan=lifespan)
    #
    # 13. oauth2_scheme: OAuth2PasswordBearer(tokenUrl="/token")
    #
    # 14. make_access_token(username: str, role: str, scopes: list[str], secret: str) -> str
    #       username : str       — staff username, embedded as "sub".
    #       role     : str       — staff role, embedded as "role".
    #       scopes   : list[str] — staff permission scopes, embedded as "scopes".
    #       secret   : str       — signing key.
    #       Encodes {"sub": username, "role": role, "scopes": scopes,
    #                "type": "access", "exp": utc_now + 15 minutes} with HS256.
    #       Returns the encoded JWT string.
    #
    # 15. make_refresh_token(username: str, secret: str) -> str
    #       username : str — staff username, embedded as "sub".
    #       secret   : str — signing key.
    #       Encodes {"sub": username, "type": "refresh",
    #                "exp": utc_now + 7 days} with HS256.
    #       Returns the encoded JWT string.
    #
    # 16. get_current_user(token: str) -> User
    #       token: str — raw bearer token from Authorization header,
    #                    representing the caller's access credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes using APP_STATE["secret"] and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError
    #       OR if payload.get("type") != "access".
    #       Returns User(username=payload["sub"], role=payload["role"],
    #                    scopes=payload.get("scopes", []))
    #
    # 17. get_refresh_user(token: str) -> str
    #       token: str — raw bearer token from Authorization header,
    #                    representing the caller's refresh credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes using APP_STATE["secret"] and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError
    #       OR if payload.get("type") != "refresh".
    #       Returns payload["sub"] (the username string).
    #
    # 18. require_scope(scope: str) -> callable
    #       scope: str — the permission string required, representing the
    #                    minimum access level for an endpoint
    #                    (e.g. "commands:write").
    #       Returns a checker dep: takes user: User = Depends(get_current_user),
    #       raises HTTPException(403, detail="insufficient scope") if
    #       scope not in user.scopes, otherwise returns user.
    #
    # 19. require_role_and_scope(role: str, scope: str) -> callable
    #       role  : str — the required role string, representing the minimum
    #                     job function for an endpoint (e.g. "director").
    #       scope : str — the required scope string, representing the
    #                     minimum permission for an endpoint
    #                     (e.g. "commands:write").
    #       Returns a checker dep: takes user: User = Depends(get_current_user),
    #       raises HTTPException(403, detail="forbidden") if user.role != role,
    #       raises HTTPException(403, detail="insufficient scope") if
    #       scope not in user.scopes (checked after the role check),
    #       otherwise returns user.
    #
    # 20. auth_middleware(request, call_next) — @app.middleware("http")
    #       If request.url.path in PUBLIC_PATHS: skip, call call_next.
    #       Otherwise: if request.headers.get("X-API-Key", "") not in
    #       VALID_API_KEYS: return JSONResponse({"detail": "not authenticated"},
    #       status_code=401). Otherwise call call_next.
    #
    # 21. GET /health
    #       Public (no API key, no auth). Returns {"status": "ok"}
    #
    # 22. POST /token
    #       Public path (no API key needed — in PUBLIC_PATHS), but still
    #       validates credentials.
    #       Query params: username: str, password: str — staff login
    #           credentials.
    #       Raises HTTPException(401, detail="invalid credentials") if
    #       username not in USERS or USERS[username]["password"] != password.
    #       Returns {"access_token": ..., "refresh_token": ...} using
    #       the user's role and scopes from USERS.
    #
    # 23. POST /refresh
    #       Requires valid X-API-Key (middleware enforced).
    #       Protected by: get_refresh_user — returns username string.
    #       Looks up USERS[username] for role and scopes to build new
    #       access token.
    #       Returns {"access_token": <new_access_token>}
    #
    # 24. GET /telemetry
    #       Requires valid X-API-Key (middleware enforced).
    #       Protected by: require_scope("telemetry:read")
    #       response_model: list[TelemetryOut]
    #       Returns all telemetry. internal_sensor_id must be stripped.
    #
    # 25. POST /commands
    #       Requires valid X-API-Key (middleware enforced).
    #       body: CommandIn
    #       Protected by: require_scope("commands:write") — inject as user: User
    #       response_model: CommandOut
    #       Appends {"id": len(COMMAND_LOG)+1, "action": body.action,
    #                "issued_by": user.username} to COMMAND_LOG.
    #       Returns the new command record.
    #
    # 26. POST /commands/{command_id}/abort
    #       Requires valid X-API-Key (middleware enforced).
    #       command_id: int — the numeric ID of the command to abort,
    #                         representing a previously issued instruction.
    #       Protected by: require_role_and_scope("director", "commands:write")
    #       Raises HTTPException(404, detail="command not found") if no
    #       command in COMMAND_LOG has that id.
    #       Returns {"aborted": command_id, "by": user.username}
    # =========================================================================

    from contextlib import asynccontextmanager  # noqa: F401
    from datetime import datetime, timedelta, timezone  # noqa: F401

    from fastapi import Depends, FastAPI, HTTPException, Request  # noqa: F401
    from fastapi.responses import JSONResponse  # noqa: F401
    from fastapi.security import OAuth2PasswordBearer  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from jose import JWTError, jwt  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---

    # ── Tests ─────────────────────────────────────────────────────────────────

    with TestClient(app) as client:

        key = {"X-API-Key": "mc-key-1"}

        # Test 1: /health public, no key needed
        print("Test 1: /health is public")
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
        print(f"  status: {r.status_code}, body: {r.json()}")
        print("  PASS")

        # Test 2: /token public, no key needed
        print("Test 2: /token is public, valid login")
        r = client.post("/token?username=director-rao&password=pw-rao")
        assert r.status_code == 200
        tokens = r.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        director_access = tokens["access_token"]
        director_refresh = tokens["refresh_token"]
        print(f"  access_token present: {'access_token' in tokens}, refresh_token present: {'refresh_token' in tokens}")
        print("  PASS")

        # Test 3: invalid login → 401
        print("Test 3: invalid login → 401")
        r = client.post("/token?username=director-rao&password=wrong")
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid credentials"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 4: other roles login
        op_tokens = client.post("/token?username=op-lee&password=pw-lee").json()
        analyst_tokens = client.post("/token?username=analyst-fox&password=pw-fox").json()
        operator_access = op_tokens["access_token"]
        analyst_access  = analyst_tokens["access_token"]

        director_auth = {**key, "Authorization": f"Bearer {director_access}"}
        operator_auth = {**key, "Authorization": f"Bearer {operator_access}"}
        analyst_auth  = {**key, "Authorization": f"Bearer {analyst_access}"}

        # Test 4: protected route without API key → 401
        print("Test 4: protected route without API key → 401")
        r = client.get("/telemetry", headers={"Authorization": f"Bearer {director_access}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "not authenticated"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 5: analyst reads telemetry (telemetry:read scope)
        print("Test 5: analyst reads telemetry")
        r = client.get("/telemetry", headers=analyst_auth)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert all("internal_sensor_id" not in t for t in data)
        print(f"  telemetry: {len(data)}, internal_sensor_id stripped: {all('internal_sensor_id' not in t for t in data)}")
        print("  PASS")

        # Test 6: analyst blocked from issuing commands (no commands:write scope)
        print("Test 6: analyst blocked from issuing commands → 403")
        r = client.post("/commands", json={"action": "ping"}, headers=analyst_auth)
        assert r.status_code == 403
        assert r.json()["detail"] == "insufficient scope"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 7: operator issues a command (has commands:write scope)
        print("Test 7: operator issues a command")
        r = client.post("/commands", json={"action": "adjust-attitude"}, headers=operator_auth)
        assert r.status_code == 200
        cmd = r.json()
        assert cmd["id"] == 1
        assert cmd["action"] == "adjust-attitude"
        assert cmd["issued_by"] == "op-lee"
        print(f"  id: {cmd['id']}, action: {cmd['action']}, issued_by: {cmd['issued_by']}")
        print("  PASS")

        # Test 8: operator cannot abort (wrong role, needs director)
        print("Test 8: operator blocked from abort (role check) → 403")
        r = client.post("/commands/1/abort", headers=operator_auth)
        assert r.status_code == 403
        assert r.json()["detail"] == "forbidden"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 9: director aborts the command (role + scope match)
        print("Test 9: director aborts command")
        r = client.post("/commands/1/abort", headers=director_auth)
        assert r.status_code == 200
        result = r.json()
        assert result["aborted"] == 1
        assert result["by"] == "director-rao"
        print(f"  aborted: {result['aborted']}, by: {result['by']}")
        print("  PASS")

        # Test 10: aborting unknown command → 404
        print("Test 10: abort unknown command_id → 404")
        r = client.post("/commands/999/abort", headers=director_auth)
        assert r.status_code == 404
        assert r.json()["detail"] == "command not found"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 11: refresh token rejected on protected route → 401
        print("Test 11: refresh token rejected on /telemetry → 401")
        r = client.get("/telemetry", headers={**key, "Authorization": f"Bearer {director_refresh}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 12: refresh flow issues new access token with correct role/scopes
        print("Test 12: refresh issues new access token")
        r = client.post("/refresh", headers={**key, "Authorization": f"Bearer {director_refresh}"})
        assert r.status_code == 200
        new_access = r.json()["access_token"]
        # new token should retain director permissions
        r2 = client.post("/commands/2/abort", headers={**key, "Authorization": f"Bearer {new_access}"})
        # command 2 doesn't exist, but should pass role+scope check and hit 404
        assert r2.status_code == 404
        print(f"  refresh status: {r.status_code}, new-token abort check: {r2.status_code}")
        print("  PASS")

        # Test 13: access token rejected on /refresh → 401
        print("Test 13: access token rejected on /refresh → 401")
        r = client.post("/refresh", headers={**key, "Authorization": f"Bearer {director_access}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")


run_drill_110()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: /health is public
#   status: 200, body: {'status': 'ok'}
#   PASS
# Test 2: /token is public, valid login
#   access_token present: True, refresh_token present: True
#   PASS
# Test 3: invalid login → 401
#   status: 401, detail: invalid credentials
#   PASS
# Test 4: protected route without API key → 401
#   status: 401, detail: not authenticated
#   PASS
# Test 5: analyst reads telemetry
#   telemetry: 2, internal_sensor_id stripped: True
#   PASS
# Test 6: analyst blocked from issuing commands → 403
#   status: 403, detail: insufficient scope
#   PASS
# Test 7: operator issues a command
#   id: 1, action: adjust-attitude, issued_by: op-lee
#   PASS
# Test 8: operator blocked from abort (role check) → 403
#   status: 403, detail: forbidden
#   PASS
# Test 9: director aborts command
#   aborted: 1, by: director-rao
#   PASS
# Test 10: abort unknown command_id → 404
#   status: 404, detail: command not found
#   PASS
# Test 11: refresh token rejected on /telemetry → 401
#   status: 401, detail: invalid token
#   PASS
# Test 12: refresh issues new access token
#   refresh status: 200, new-token abort check: 404
#   PASS
# Test 13: access token rejected on /refresh → 401
#   status: 401, detail: invalid token
#   PASS
# =============================================================================
