# =============================================================================
# CONCEPT INTRO — HTTPBasic Auth
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# HTTPBasic is the simplest auth scheme: the client sends a username and
# password encoded in the Authorization header on every request. It's useful
# for internal tools, admin panels, or any system where managing JWTs or
# API keys is unnecessary overhead.
#
# NEW IMPORTS
# -----------
# from fastapi.security import HTTPBasic, HTTPBasicCredentials
#   └─ HTTPBasic             — dependency that extracts username+password
#                              from the Authorization: Basic <base64> header
#   └─ HTTPBasicCredentials  — the object returned by the dependency;
#                              has .username: str and .password: str fields
#
# import secrets
#   └─ secrets.compare_digest(a: str, b: str) -> bool
#        Timing-safe string comparison. Always use this instead of == when
#        comparing passwords, to prevent timing attacks.
#
# NEW CLASSES
# -----------
# HTTPBasic() → instance
#   No required arguments.
#   When resolved as a dependency: reads the Authorization header, decodes
#   the base64 credentials, returns HTTPBasicCredentials.
#   Raises HTTPException(401) automatically if the header is missing.
#
# HTTPBasicCredentials
#   .username : str — the username sent by the client
#   .password : str — the password sent by the client
#
# WIRING EXAMPLE
# --------------
# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.security import HTTPBasic, HTTPBasicCredentials
# from fastapi.testclient import TestClient
# import secrets
#
# app = FastAPI()
# security = HTTPBasic()
# USERS = {"alice": "pw-alice"}
#
# def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
#     stored = USERS.get(credentials.username, "")
#     if not secrets.compare_digest(credentials.password, stored):
#         raise HTTPException(status_code=401, detail="invalid credentials")
#     return credentials.username
#
# @app.get("/me")
# def me(username: str = Depends(get_current_user)):
#     return {"username": username}
#
# client = TestClient(app)
# r = client.get("/me", auth=("alice", "pw-alice"))  # → 200
# r = client.get("/me", auth=("alice", "wrong"))     # → 401
# r = client.get("/me")                              # → 401
#
# NOTE — TestClient auth= shorthand
# ----------------------------------
# client.get("/path", auth=("username", "password"))
# is equivalent to sending Authorization: Basic <base64(username:password)>
#
# PURE PYTHON TRANSLATION
# -----------------------
# Pure Python (manual header parse):         FastAPI equivalent:
# ─────────────────────────────────────────  ──────────────────────────────────
# raw = request.headers.get("Authorization") security = HTTPBasic()
# decoded = base64.decode(raw.split()[1])    creds: HTTPBasicCredentials = Depends(security)
# username, password = decoded.split(":", 1) creds.username, creds.password
# if password != stored: raise 401           secrets.compare_digest(pw, stored)
# =============================================================================


def run_drill_107():
    # =========================================================================
    # SCENARIO: Submarine
    #
    # A submarine operations API is accessed by crew members via a basic
    # auth terminal. Crew log in with username and password. After any
    # depth adjustment is submitted, a systems log entry is written in the
    # background. The API exposes current system readings and allows
    # submitting depth adjustments.
    #
    # REQUIREMENTS
    # ------------
    # 1. CREW: dict[str, str]
    #       In-memory map from username to password.
    #       Represents registered crew members.
    #       Pre-populate with:
    #         {"kapitan": "depth-1", "navigator": "depth-2"}
    #
    # 2. SYSTEMS: list[dict]
    #       In-memory list of system status readings.
    #       Represents current submarine system states.
    #       Pre-populate with:
    #         [
    #           {"id": 1, "system": "ballast",  "status": "nominal", "internal_code": "BT-01"},
    #           {"id": 2, "system": "sonar",    "status": "active",  "internal_code": "SN-07"},
    #           {"id": 3, "system": "reactor",  "status": "nominal", "internal_code": "RC-03"},
    #         ]
    #
    # 3. DEPTH_LOG: list[str]
    #       In-memory list of background log entries.
    #       Starts empty. Background task appends entries here.
    #
    # 4. SystemOut: BaseModel
    #       Response schema for a system reading.
    #       Fields: id: int, system: str, status: str
    #       (internal_code intentionally excluded)
    #
    # 5. AdjustIn: BaseModel
    #       Request body for a depth adjustment.
    #       Fields: meters: int — the depth change in metres (positive = dive,
    #                             negative = surface), representing the crew's
    #                             intended depth adjustment command.
    #
    # 6. security: HTTPBasic
    #       Instance used to extract HTTPBasicCredentials from each request.
    #
    # 7. get_current_crew(credentials: HTTPBasicCredentials) -> str
    #       credentials: HTTPBasicCredentials — the username and password
    #                    extracted from the Authorization header, representing
    #                    the crew member's basic auth submission.
    #       Must declare: credentials: HTTPBasicCredentials = Depends(security)
    #       Looks up credentials.username in CREW.
    #       Uses secrets.compare_digest to compare credentials.password
    #       against the stored password.
    #       Raises HTTPException(401, detail="invalid credentials") if
    #       username not found or password does not match.
    #       Returns credentials.username on success.
    #
    # 8. log_adjustment(username: str, meters: int) -> None
    #       username : str — the crew member who submitted the adjustment,
    #                        recorded in the log entry.
    #       meters   : int — the depth change value submitted, recorded
    #                        in the log entry.
    #       Appends f"[LOG] {username} adjusted depth by {meters}m" to DEPTH_LOG.
    #       Called as a BackgroundTask — runs after the response is sent.
    #
    # 9. GET /systems
    #       Protected by: Depends(get_current_crew)
    #       response_model: list[SystemOut]
    #       Returns all system readings. internal_code must be stripped.
    #
    # 10. POST /depth
    #       body: AdjustIn — the depth adjustment command.
    #       Protected by: get_current_crew — inject as username: str
    #       Adds log_adjustment as a BackgroundTask with username and meters.
    #       Returns {"username": username, "meters": body.meters, "status": "submitted"}
    # =========================================================================

    import secrets  # noqa: F401

    from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException  # noqa: F401
    from fastapi.security import HTTPBasic, HTTPBasicCredentials  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---
    CREW: dict[str, str] = {"kapitan": "depth-1", "navigator": "depth-2"}
    SYSTEMS: list[dict] = [
        {"id": 1, "system": "ballast", "status": "nominal", "internal_code": "BT-01"},
        {"id": 2, "system": "sonar", "status": "active", "internal_code": "SN-07"},
        {"id": 3, "system": "reactor", "status": "nominal", "internal_code": "RC-03"},
    ]
    DEPTH_LOG: list[str] = []

    class SystemOut(BaseModel):
        id: int
        system: str
        status: str

    class AdjustIn(BaseModel):
        meters: int

    security = HTTPBasic()

    def get_current_crew(credentials: HTTPBasicCredentials = Depends(security)):
        if (password := CREW.get(credentials.username)) and secrets.compare_digest(
            credentials.password, password
        ):
            return credentials.username
        raise HTTPException(401, detail="invalid credentials")

    def log_adjustment(username: str, meters: int):
        DEPTH_LOG.append(f"[LOG] {username} adjusted depth by {meters}m")

    app = FastAPI()

    @app.get("/systems", response_model=list[SystemOut])
    def get_sys_readings(_=Depends(get_current_crew)):
        return SYSTEMS

    @app.post("/depth")
    def adjust_depth(
        body: AdjustIn, bg: BackgroundTasks, username: str = Depends(get_current_crew)
    ):
        bg.add_task(log_adjustment, username, body.meters)
        return {"username": username, "meters": body.meters, "status": "submitted"}

    # ── Tests ─────────────────────────────────────────────────────────────────

    client = TestClient(app)

    # Test 1: valid credentials — list systems
    print("Test 1: valid credentials return all systems")
    r = client.get("/systems", auth=("kapitan", "depth-1"))
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    assert all("internal_code" not in s for s in data)
    print(
        f"  systems: {len(data)}, internal_code stripped: {all('internal_code' not in s for s in data)}"
    )
    print("  PASS")

    # Test 2: wrong password → 401
    print("Test 2: wrong password -> 401")
    r = client.get("/systems", auth=("kapitan", "wrong"))
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid credentials"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 3: unknown username → 401
    print("Test 3: unknown username -> 401")
    r = client.get("/systems", auth=("ghost", "depth-1"))
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid credentials"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 4: missing auth header → 401
    print("Test 4: missing auth header -> 401")
    r = client.get("/systems")
    assert r.status_code == 401
    print(f"  status: {r.status_code}")
    print("  PASS")

    # Test 5: navigator submits depth adjustment
    print("Test 5: navigator submits depth adjustment")
    r = client.post("/depth", json={"meters": -50}, auth=("navigator", "depth-2"))
    assert r.status_code == 200
    result = r.json()
    assert result["username"] == "navigator"
    assert result["meters"] == -50
    assert result["status"] == "submitted"
    print(
        f"  username: {result['username']}, meters: {result['meters']}, status: {result['status']}"
    )
    print("  PASS")

    # Test 6: background log recorded after adjustment
    print("Test 6: depth log entry recorded in background")
    assert len(DEPTH_LOG) == 1
    assert DEPTH_LOG[0] == "[LOG] navigator adjusted depth by -50m"
    print(f"  log entry: {DEPTH_LOG[0]}")
    print("  PASS")

    # Test 7: second crew member submits adjustment
    print("Test 7: kapitan submits depth adjustment")
    r = client.post("/depth", json={"meters": 100}, auth=("kapitan", "depth-1"))
    assert r.status_code == 200
    result = r.json()
    assert result["username"] == "kapitan"
    assert result["meters"] == 100
    print(f"  username: {result['username']}, meters: {result['meters']}")
    print("  PASS")

    # Test 8: two log entries total
    print("Test 8: two log entries recorded total")
    assert len(DEPTH_LOG) == 2
    assert DEPTH_LOG[1] == "[LOG] kapitan adjusted depth by 100m"
    print(f"  log count: {len(DEPTH_LOG)}, second entry: {DEPTH_LOG[1]}")
    print("  PASS")


run_drill_107()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: valid credentials return all systems
#   systems: 3, internal_code stripped: True
#   PASS
# Test 2: wrong password → 401
#   status: 401, detail: invalid credentials
#   PASS
# Test 3: unknown username → 401
#   status: 401, detail: invalid credentials
#   PASS
# Test 4: missing auth header → 401
#   status: 401
#   PASS
# Test 5: navigator submits depth adjustment
#   username: navigator, meters: -50, status: submitted
#   PASS
# Test 6: depth log entry recorded in background
#   log entry: [LOG] navigator adjusted depth by -50m
#   PASS
# Test 7: kapitan submits depth adjustment
#   username: kapitan, meters: 100
#   PASS
# Test 8: two log entries recorded total
#   log count: 2, second entry: [LOG] kapitan adjusted depth by 100m
#   PASS
# =============================================================================
