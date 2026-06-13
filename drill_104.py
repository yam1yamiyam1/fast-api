# =============================================================================
# CONCEPT INTRO — Role-Based Access Control (RBAC)
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# Different users need different permissions. RBAC gates endpoints by the
# role embedded in the JWT — the same get_current_user dep resolves the user,
# then a role-checking dep sits on top and raises 403 if the role is wrong.
# This is an extension of what you built in D103 (get_director), now
# generalised to a reusable pattern with multiple roles.
#
# THE PATTERN — role checker factory
# ------------------------------------
# Instead of writing a separate dep for each role, build one factory that
# returns a dep for any role:
#
#   def require_role(required_role: str):
#       def checker(user: User = Depends(get_current_user)) -> User:
#           if user.role != required_role:
#               raise HTTPException(403, detail="forbidden")
#           return user
#       return checker
#
#   @app.delete("/items/{id}")
#   def delete_item(user: User = Depends(require_role("admin"))): ...
#
#   @app.get("/dashboard")
#   def dashboard(user: User = Depends(require_role("operator"))): ...
#
# Each call to require_role() returns a fresh dep function. FastAPI resolves
# it exactly like any other Depends().
#
# PURE PYTHON TRANSLATION
# -----------------------
# Pure Python (D65 handler registry):        FastAPI equivalent:
# ─────────────────────────────────────────  ──────────────────────────────────
# role_guards = {"admin": check_admin_fn}    require_role("admin") → dep fn
# await role_guards["admin"](user)           Depends(require_role("admin"))
# raise PermissionError if wrong role        raise HTTPException(403)
#
# WIRING EXAMPLE
# --------------
# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer
# from fastapi.testclient import TestClient
# from jose import jwt, JWTError
# from pydantic import BaseModel
#
# SECRET = "secret"
# app = FastAPI()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
#
# class User(BaseModel):
#     username: str
#     role: str
#
# def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
#     try:
#         payload = jwt.decode(token, SECRET, algorithms=["HS256"])
#     except JWTError:
#         raise HTTPException(401, detail="invalid token")
#     return User(username=payload["sub"], role=payload["role"])
#
# def require_role(required_role: str):
#     def checker(user: User = Depends(get_current_user)) -> User:
#         if user.role != required_role:
#             raise HTTPException(status_code=403, detail="forbidden")
#         return user
#     return checker
#
# @app.get("/admin-only")
# def admin_only(user: User = Depends(require_role("admin"))):
#     return {"msg": f"hello admin {user.username}"}
#
# @app.get("/operator-only")
# def operator_only(user: User = Depends(require_role("operator"))):
#     return {"msg": f"hello operator {user.username}"}
#
# def make_token(username: str, role: str) -> str:
#     return jwt.encode({"sub": username, "role": role}, SECRET, algorithm="HS256")
#
# client = TestClient(app)
# r = client.get("/admin-only", headers={"Authorization": f"Bearer {make_token('alice','admin')}"})
# # → 200
# r = client.get("/admin-only", headers={"Authorization": f"Bearer {make_token('bob','operator')}"})
# # → 403
# =============================================================================


def run_drill_104():
    # =========================================================================
    # SCENARIO: Satellite Control Room
    #
    # A satellite control room API manages satellite commands and telemetry
    # logs. Staff have one of three roles: "analyst", "operator", "commander".
    # Analysts may only read telemetry. Operators may read telemetry and issue
    # commands. Commanders may do everything operators can, plus purge the
    # command log. After any command is issued, an audit entry is appended
    # in the background.
    #
    # REQUIREMENTS
    # ------------
    # 1. SECRET_KEY: str
    #       The HS256 signing secret. Value: "sat-secret"
    #
    # 2. APP_STATE: dict
    #       Shared state dict, starts empty.
    #       Lifespan loads APP_STATE["secret"] = SECRET_KEY at startup
    #       and clears at shutdown.
    #
    # 3. TELEMETRY: list[dict]
    #       In-memory list of telemetry records.
    #       Represents raw sensor readings from the satellite.
    #       Pre-populate with:
    #         [
    #           {"id": 1, "signal": "nominal", "temp_c": 22},
    #           {"id": 2, "signal": "weak",    "temp_c": 31},
    #         ]
    #
    # 4. COMMANDS: list[dict]
    #       In-memory list of issued command records.
    #       Starts empty. Commands are appended here by the issue endpoint.
    #
    # 5. AUDIT_LOG: list[str]
    #       In-memory list of audit strings.
    #       Starts empty. Background task appends entries here.
    #
    # 6. TelemetryOut: BaseModel
    #       Response schema for a telemetry record.
    #       Fields: id: int, signal: str, temp_c: int
    #
    # 7. CommandIn: BaseModel
    #       Request body for issuing a command.
    #       Fields: action: str — the instruction to send to the satellite,
    #                             e.g. "reboot", "adjust-orbit".
    #
    # 8. CommandOut: BaseModel
    #       Response schema for an issued command.
    #       Fields: id: int, action: str, issued_by: str
    #
    # 9. User: BaseModel
    #       Fields: username: str, role: str
    #
    # 10. lifespan: asynccontextmanager
    #       Startup: APP_STATE["secret"] = SECRET_KEY
    #       Shutdown: APP_STATE.clear()
    #       Passed to FastAPI(lifespan=lifespan)
    #
    # 11. oauth2_scheme: OAuth2PasswordBearer(tokenUrl="/token")
    #
    # 12. make_token(username: str, role: str, secret: str) -> str
    #       username : str — staff username embedded as "sub" claim.
    #       role     : str — staff role embedded as "role" claim.
    #       secret   : str — the signing key.
    #       Encodes {"sub": username, "role": role} with HS256. No expiry.
    #       Returns the encoded JWT string.
    #
    # 13. get_current_user(token: str) -> User
    #       token: str — raw bearer token from Authorization header,
    #                    representing the caller's JWT credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes token using APP_STATE["secret"] and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError.
    #       Returns User(username=payload["sub"], role=payload["role"])
    #
    # 14. require_role(required_role: str) -> callable
    #       required_role: str — the role string that the caller must have,
    #                            representing the minimum access level for
    #                            an endpoint (e.g. "operator", "commander").
    #       Returns a dependency function (checker) that:
    #         - takes user: User = Depends(get_current_user)
    #         - raises HTTPException(403, detail="forbidden") if
    #           user.role != required_role
    #         - returns user if role matches
    #
    # 15. audit_command(action: str, username: str) -> None
    #       action   : str — the command action string that was issued,
    #                        used to build the audit entry message.
    #       username : str — the username of the staff member who issued
    #                        the command, recorded in the audit entry.
    #       Appends f"[AUDIT] {username} issued: {action}" to AUDIT_LOG.
    #       Called as a BackgroundTask — runs after the response is sent.
    #
    # 16. GET /telemetry
    #       Protected by: require_role("analyst") — analysts, operators,
    #                     and commanders all have role checks; for this
    #                     endpoint use require_role("analyst") so only
    #                     analysts are explicitly allowed here.
    #                     NOTE: in this drill each endpoint allows exactly
    #                     one role. Operators and commanders use separate
    #                     routes for their actions.
    #       response_model: list[TelemetryOut]
    #       Returns all telemetry records.
    #
    # 17. POST /commands
    #       body: CommandIn — the command to issue to the satellite.
    #       Protected by: require_role("operator")
    #       response_model: CommandOut
    #       Appends {"id": len(COMMANDS)+1, "action": body.action,
    #                "issued_by": user.username} to COMMANDS.
    #       Adds audit_command as a BackgroundTask with action and username.
    #       Returns the new command record.
    #
    # 18. DELETE /commands
    #       Protected by: require_role("commander")
    #       Clears COMMANDS list (COMMANDS.clear()).
    #       Returns {"purged": True}
    # =========================================================================

    from contextlib import asynccontextmanager  # noqa: F401

    from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException  # noqa: F401
    from fastapi.security import OAuth2PasswordBearer  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from jose import JWTError, jwt  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---
    SECRET_KEY: str = "sat-secret"
    ALGO: str = "HS256"
    APP_STATE: dict = {}
    TELEMETRY: list[dict] = [
        {"id": 1, "signal": "nominal", "temp_c": 22},
        {"id": 2, "signal": "weak", "temp_c": 31},
    ]
    COMMANDS: list[dict] = []
    AUDIT_LOG: list[str] = []

    class TelemetryOut(BaseModel):
        id: int
        signal: str
        temp_c: int

    class CommandIn(BaseModel):
        action: str

    class CommandOut(BaseModel):
        id: int
        action: str
        issued_by: str

    class User(BaseModel):
        username: str
        role: str

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        APP_STATE["secret"] = SECRET_KEY
        yield
        APP_STATE.clear()

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def make_token(username: str, role: str, secret: str):
        return jwt.encode(
            claims={"sub": username, "role": role}, key=secret, algorithm=ALGO
        )

    def get_current_user(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(
                token=token, key=APP_STATE["secret"], algorithms=[ALGO]
            )
            return User(username=payload["sub"], role=payload["role"])
        except JWTError:
            raise HTTPException(401, detail="invalid token")

    def require_role(required_role: str):
        def checker(user: User = Depends(get_current_user)):
            if user.role == required_role:
                return user
            raise HTTPException(403, detail="forbidden")

        return checker

    def audit_command(action: str, username: str):
        AUDIT_LOG.append(f"[AUDIT] {username} issued: {action}")

    app = FastAPI(lifespan=lifespan)

    @app.get("/telemetry", response_model=list[TelemetryOut])
    def get_telemetries(_=Depends(require_role("analyst"))):
        return TELEMETRY

    @app.post("/commands", response_model=CommandOut)
    def add_command(
        body: CommandIn,
        bg: BackgroundTasks,
        user: User = Depends(require_role("operator")),
    ):
        id = len(COMMANDS) + 1
        COMMANDS.append({"id": id, "action": body.action, "issued_by": user.username})
        bg.add_task(audit_command, body.action, user.username)
        return next((c for c in COMMANDS if c.get("id") == id), None)

    @app.delete("/commands")
    def clear_commands(_=Depends(require_role("commander"))):
        COMMANDS.clear()
        return {"purged": True}

    # ── Tests ─────────────────────────────────────────────────────────────────

    with TestClient(app) as client:
        analyst_token = make_token("eve", "analyst", SECRET_KEY)
        operator_token = make_token("dave", "operator", SECRET_KEY)
        commander_token = make_token("carol", "commander", SECRET_KEY)

        analyst_auth = {"Authorization": f"Bearer {analyst_token}"}
        operator_auth = {"Authorization": f"Bearer {operator_token}"}
        commander_auth = {"Authorization": f"Bearer {commander_token}"}

        # Test 1: analyst reads telemetry
        print("Test 1: analyst reads telemetry")
        r = client.get("/telemetry", headers=analyst_auth)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["signal"] == "nominal"
        print(f"  records: {len(data)}, first signal: {data[0]['signal']}")
        print("  PASS")

        # Test 2: operator blocked from telemetry → 403
        print("Test 2: operator blocked from telemetry -> 403")
        r = client.get("/telemetry", headers=operator_auth)
        assert r.status_code == 403
        assert r.json()["detail"] == "forbidden"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 3: operator issues a command
        print("Test 3: operator issues a command")
        r = client.post("/commands", json={"action": "reboot"}, headers=operator_auth)
        assert r.status_code == 200
        cmd = r.json()
        assert cmd["action"] == "reboot"
        assert cmd["issued_by"] == "dave"
        assert cmd["id"] == 1
        print(
            f"  id: {cmd['id']}, action: {cmd['action']}, issued_by: {cmd['issued_by']}"
        )
        print("  PASS")

        # Test 4: analyst blocked from issuing commands → 403
        print("Test 4: analyst blocked from issuing commands -> 403")
        r = client.post("/commands", json={"action": "reboot"}, headers=analyst_auth)
        assert r.status_code == 403
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 5: background audit was recorded
        print("Test 5: audit log entry recorded after command")
        assert len(AUDIT_LOG) == 1
        assert AUDIT_LOG[0] == "[AUDIT] dave issued: reboot"
        print(f"  audit entry: {AUDIT_LOG[0]}")
        print("  PASS")

        # Test 6: analyst blocked from purging → 403
        print("Test 6: analyst blocked from purging commands -> 403")
        r = client.delete("/commands", headers=analyst_auth)
        assert r.status_code == 403
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 7: operator blocked from purging → 403
        print("Test 7: operator blocked from purging commands -> 403")
        r = client.delete("/commands", headers=operator_auth)
        assert r.status_code == 403
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 8: commander purges commands
        print("Test 8: commander purges command log")
        r = client.delete("/commands", headers=commander_auth)
        assert r.status_code == 200
        assert r.json() == {"purged": True}
        assert COMMANDS == []
        print(f"  result: {r.json()}, COMMANDS empty: {COMMANDS == []}")
        print("  PASS")

        # Test 9: missing token → 401
        print("Test 9: missing token -> 401")
        r = client.get("/telemetry")
        assert r.status_code == 401
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 10: bad token → 401
        print("Test 10: bad token -> 401")
        r = client.get("/telemetry", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")


run_drill_104()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: analyst reads telemetry
#   records: 2, first signal: nominal
#   PASS
# Test 2: operator blocked from telemetry → 403
#   status: 403, detail: forbidden
#   PASS
# Test 3: operator issues a command
#   id: 1, action: reboot, issued_by: dave
#   PASS
# Test 4: analyst blocked from issuing commands → 403
#   status: 403
#   PASS
# Test 5: audit log entry recorded after command
#   audit entry: [AUDIT] dave issued: reboot
#   PASS
# Test 6: analyst blocked from purging commands → 403
#   status: 403
#   PASS
# Test 7: operator blocked from purging commands → 403
#   status: 403
#   PASS
# Test 8: commander purges command log
#   result: {'purged': True}, COMMANDS empty: True
#   PASS
# Test 9: missing token → 401
#   status: 401
#   PASS
# Test 10: bad token → 401
#   status: 401, detail: invalid token
#   PASS
# =============================================================================
