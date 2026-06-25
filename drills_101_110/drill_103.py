# =============================================================================
# CONCEPT INTRO — Current User Dependency (token → User object)
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# In D102, get_current_vet returned a plain dict {"username": ...}.
# As the system grows you want a typed User object — not a raw dict — so
# endpoints can access user fields safely and the type system can help you.
# The pattern is: split auth into two chained deps:
#   1. get_current_user  — decodes JWT, returns a User Pydantic model
#   2. downstream deps   — receive User via Depends(get_current_user)
#
# This is the standard FastAPI auth pattern used in every real project.
#
# NEW CONCEPT — User as a Pydantic model in a dependency chain
# ------------------------------------------------------------
# Nothing new to import. The novelty is structural:
#
#   class User(BaseModel):
#       username: str
#       role: str
#
#   def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
#       try:
#           payload = jwt.decode(token, SECRET, algorithms=["HS256"])
#       except JWTError:
#           raise HTTPException(401, detail="invalid token")
#       return User(username=payload["sub"], role=payload["role"])
#
#   @app.get("/me")
#   def me(user: User = Depends(get_current_user)):
#       return user          # user is a typed User instance, not a dict
#
# CHAINED DEP REMINDER (from D97)
# --------------------------------
# A dep that depends on another dep declares Depends() in its own signature:
#
#   def get_admin(user: User = Depends(get_current_user)) -> User:
#       if user.role != "admin":
#           raise HTTPException(403, detail="admins only")
#       return user
#
#   @app.get("/admin-only")
#   def admin_route(user: User = Depends(get_admin)): ...
#
# PURE PYTHON TRANSLATION
# -----------------------
# Pure Python (D68 chained deps):            FastAPI equivalent:
# ─────────────────────────────────────────  ──────────────────────────────────
# user_dict = await get_user_dict(token)     user: User = Depends(get_current_user)
# admin = await check_admin(user_dict)       admin: User = Depends(get_admin)
# inject admin into handler                  FastAPI injects automatically
#
# MINIMAL WIRING EXAMPLE
# ----------------------
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
#         raise HTTPException(status_code=401, detail="invalid token")
#     return User(username=payload["sub"], role=payload["role"])
#
# @app.get("/me")
# def me(user: User = Depends(get_current_user)):
#     return user
#
# # helper for tests
# def make_token(username: str, role: str) -> str:
#     return jwt.encode({"sub": username, "role": role}, SECRET, algorithm="HS256")
#
# client = TestClient(app)
# token = make_token("alice", "producer")
# r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
# # → 200, {"username": "alice", "role": "producer"}
# =============================================================================


def run_drill_103():
    # =========================================================================
    # SCENARIO: Broadcast Studio
    #
    # A broadcast studio API manages scheduled programmes. Staff are either
    # "producer" or "director". Both roles can list and view programmes.
    # Only directors may look up the full schedule for a specific studio room.
    # Authentication uses JWTs that embed username and role as claims.
    #
    # REQUIREMENTS
    # ------------
    # 1. SECRET_KEY: str
    #       The HS256 signing secret. Value: "studio-secret"
    #
    # 2. APP_STATE: dict
    #       Shared state dict, starts empty.
    #       Lifespan loads APP_STATE["secret"] = SECRET_KEY at startup
    #       and clears at shutdown.
    #
    # 3. PROGRAMMES: dict[int, dict]
    #       In-memory map from programme ID (int) to programme record.
    #       Represents all scheduled broadcast content.
    #       Pre-populate with:
    #         1: {"id": 1, "title": "Morning News", "room": "A", "internal_cost": 5000}
    #         2: {"id": 2, "title": "Evening Drama", "room": "B", "internal_cost": 12000}
    #         3: {"id": 3, "title": "Late Sport",   "room": "A", "internal_cost": 8000}
    #
    # 4. ProgrammeOut: BaseModel
    #       Response schema for a single programme.
    #       Fields: id: int, title: str, room: str
    #       (internal_cost intentionally excluded)
    #
    # 5. User: BaseModel
    #       Represents an authenticated staff member.
    #       Fields: username: str, role: str
    #
    # 6. lifespan: asynccontextmanager
    #       Startup: APP_STATE["secret"] = SECRET_KEY
    #       Shutdown: APP_STATE.clear()
    #       Passed to FastAPI(lifespan=lifespan)
    #
    # 7. oauth2_scheme: OAuth2PasswordBearer
    #       Extracts bearer token from Authorization header.
    #       tokenUrl should be "/token"
    #
    # 8. make_token(username: str, role: str, secret: str) -> str
    #       username : str — the staff member's username, embedded as "sub" claim.
    #       role     : str — the staff member's role, embedded as "role" claim.
    #       secret   : str — the signing key.
    #       Encodes {"sub": username, "role": role} using HS256.
    #       No expiry needed for this drill.
    #       Returns the encoded JWT string.
    #
    # 9. get_current_user(token: str) -> User
    #       token: str — raw bearer token from the Authorization header,
    #                    representing the caller's JWT credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes token using APP_STATE["secret"] and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError.
    #       Returns User(username=payload["sub"], role=payload["role"])
    #
    # 10. get_director(user: User) -> User
    #       user: User — the authenticated staff member resolved from the JWT,
    #                    representing the caller whose role is being checked.
    #       Must declare: user: User = Depends(get_current_user)
    #       Raises HTTPException(403, detail="directors only") if user.role != "director".
    #       Returns user unchanged if role check passes.
    #
    # 11. GET /programmes
    #       Protected by: Depends(get_current_user)  — any authenticated staff
    #       response_model: list[ProgrammeOut]
    #       Returns all programmes. internal_cost must be stripped.
    #
    # 12. GET /programmes/{programme_id}
    #       programme_id: int — numeric identifier of a specific programme
    #                           in the broadcast schedule.
    #       Protected by: Depends(get_current_user)  — any authenticated staff
    #       response_model: ProgrammeOut
    #       Raises HTTPException(404, detail="programme not found") if not found.
    #       Returns the matching programme. internal_cost must be stripped.
    #
    # 13. GET /rooms/{room}/schedule
    #       room: str — the studio room identifier (e.g. "A" or "B"),
    #                   representing the physical broadcast room to query.
    #       Protected by: Depends(get_director)  — directors only
    #       response_model: list[ProgrammeOut]
    #       Returns all programmes assigned to that room.
    #       internal_cost must be stripped.
    # =========================================================================

    from contextlib import asynccontextmanager  # noqa: F401

    from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
    from fastapi.security import OAuth2PasswordBearer  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from jose import JWTError, jwt  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---
    SECRET_KEY: str = "studio-secret"
    ALGO: str = "HS256"
    APP_STATE: dict = {}
    PROGRAMMES: dict[int, dict] = {
        1: {"id": 1, "title": "Morning News", "room": "A", "internal_cost": 5000},
        2: {"id": 2, "title": "Evening Drama", "room": "B", "internal_cost": 12000},
        3: {"id": 3, "title": "Late Sport", "room": "A", "internal_cost": 8000},
    }

    class ProgrammeOut(BaseModel):
        id: int
        title: str
        room: str

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

    def get_director(user: User = Depends(get_current_user)):
        if user.role == "director":
            return user
        raise HTTPException(403, detail="directors only")

    app = FastAPI(lifespan=lifespan)

    @app.get("/programmes", response_model=list[ProgrammeOut])
    def get_programmes(_=Depends(get_current_user)):
        return list(PROGRAMMES.values())

    @app.get("/programmes/{programme_id}", response_model=ProgrammeOut)
    def get_programme(programme_id: int, _=Depends(get_current_user)):
        if programme := PROGRAMMES.get(programme_id):
            return programme
        raise HTTPException(404, detail="programme not found")

    @app.get("/rooms/{room}/schedule", response_model=list[ProgrammeOut])
    def get_room_sched(room: str, _=Depends(get_director)):
        return [p for p in PROGRAMMES.values() if p["room"] == room]

    # ── Tests ─────────────────────────────────────────────────────────────────

    with TestClient(app) as client:
        producer_token = make_token("alice", "producer", SECRET_KEY)
        director_token = make_token("bob", "director", SECRET_KEY)
        producer_auth = {"Authorization": f"Bearer {producer_token}"}
        director_auth = {"Authorization": f"Bearer {director_token}"}

        # Test 1: producer can list all programmes
        print("Test 1: producer lists all programmes")
        r = client.get("/programmes", headers=producer_auth)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        assert all("internal_cost" not in p for p in data)
        print(
            f"  programmes: {len(data)}, internal_cost stripped: {all('internal_cost' not in p for p in data)}"
        )
        print("  PASS")

        # Test 2: director can list all programmes
        print("Test 2: director lists all programmes")
        r = client.get("/programmes", headers=director_auth)
        assert r.status_code == 200
        assert len(r.json()) == 3
        print(f"  programmes: {len(r.json())}")
        print("  PASS")

        # Test 3: producer can fetch a programme by ID
        print("Test 3: producer fetches programme by ID")
        r = client.get("/programmes/2", headers=producer_auth)
        assert r.status_code == 200
        prog = r.json()
        assert prog["id"] == 2
        assert prog["title"] == "Evening Drama"
        assert "internal_cost" not in prog
        print(
            f"  id: {prog['id']}, title: {prog['title']}, internal_cost present: {'internal_cost' in prog}"
        )
        print("  PASS")

        # Test 4: programme not found → 404
        print("Test 4: unknown programme_id -> 404")
        r = client.get("/programmes/999", headers=producer_auth)
        assert r.status_code == 404
        assert r.json()["detail"] == "programme not found"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 5: director can view room schedule
        print("Test 5: director fetches room A schedule")
        r = client.get("/rooms/A/schedule", headers=director_auth)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert all(p["room"] == "A" for p in data)
        print(f"  room A programmes: {len(data)}")
        print("  PASS")

        # Test 6: producer cannot view room schedule → 403
        print("Test 6: producer blocked from room schedule -> 403")
        r = client.get("/rooms/A/schedule", headers=producer_auth)
        assert r.status_code == 403
        assert r.json()["detail"] == "directors only"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 7: missing token → 401
        print("Test 7: missing token -> 401")
        r = client.get("/programmes")
        assert r.status_code == 401
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 8: bad token → 401
        print("Test 8: bad token -> 401")
        r = client.get("/programmes", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 9: user object has correct fields
        print("Test 9: decoded user has correct username and role")
        r = client.get("/programmes", headers=director_auth)
        assert r.status_code == 200
        # verify room schedule only works for director — confirms role was decoded
        r2 = client.get("/rooms/B/schedule", headers=director_auth)
        assert r2.status_code == 200
        data = r2.json()
        assert len(data) == 1
        assert data[0]["title"] == "Evening Drama"
        print(f"  room B programmes: {len(data)}, title: {data[0]['title']}")
        print("  PASS")


run_drill_103()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: producer lists all programmes
#   programmes: 3, internal_cost stripped: True
#   PASS
# Test 2: director lists all programmes
#   programmes: 3
#   PASS
# Test 3: producer fetches programme by ID
#   id: 2, title: Evening Drama, internal_cost present: False
#   PASS
# Test 4: unknown programme_id → 404
#   status: 404, detail: programme not found
#   PASS
# Test 5: director fetches room A schedule
#   room A programmes: 2
#   PASS
# Test 6: producer blocked from room schedule → 403
#   status: 403, detail: directors only
#   PASS
# Test 7: missing token → 401
#   status: 401
#   PASS
# Test 8: bad token → 401
#   status: 401, detail: invalid token
#   PASS
# Test 9: decoded user has correct username and role
#   room B programmes: 1, title: Evening Drama
#   PASS
# =============================================================================
