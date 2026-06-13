# =============================================================================
# CONCEPT INTRO — Scopes (Fine-Grained Permissions)
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# Roles (D103/D104) are coarse: "admin" or "operator". Scopes are finer:
# a single user can have exactly the permissions they need, e.g.
# ["observations:read", "telescope:write"] without being a full "admin".
# Scopes are embedded in the JWT and checked per-endpoint.
#
# THE PATTERN
# -----------
# 1. Embed a list of scope strings in the JWT claims:
#      {"sub": "alice", "scopes": ["observations:read", "targets:read"]}
#
# 2. Decode them in get_current_user and store on the User object.
#
# 3. Build a require_scope(scope) factory — same shape as require_role:
#      def require_scope(scope: str):
#          def checker(user: User = Depends(get_current_user)) -> User:
#              if scope not in user.scopes:
#                  raise HTTPException(403, detail="insufficient scope")
#              return user
#          return checker
#
# 4. Apply to endpoints:
#      @app.get("/data")
#      def data(user: User = Depends(require_scope("observations:read"))): ...
#
# USER MODEL WITH SCOPES
# ----------------------
# class User(BaseModel):
#     username: str
#     scopes: list[str]
#
# MAKE TOKEN WITH SCOPES
# ----------------------
# def make_token(username: str, scopes: list[str], secret: str) -> str:
#     return jwt.encode(
#         {"sub": username, "scopes": scopes},
#         secret,
#         algorithm="HS256"
#     )
#
# PURE PYTHON TRANSLATION
# -----------------------
# Pure Python (D65 guard registry):          FastAPI equivalent:
# ─────────────────────────────────────────  ──────────────────────────────────
# guards = {"obs:read": check_obs_fn}        require_scope("obs:read") → dep fn
# await guards["obs:read"](user)             Depends(require_scope("obs:read"))
# raise PermissionError if scope missing     raise HTTPException(403)
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
#     scopes: list[str]
#
# def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
#     try:
#         payload = jwt.decode(token, SECRET, algorithms=["HS256"])
#     except JWTError:
#         raise HTTPException(401, detail="invalid token")
#     return User(username=payload["sub"], scopes=payload.get("scopes", []))
#
# def require_scope(scope: str):
#     def checker(user: User = Depends(get_current_user)) -> User:
#         if scope not in user.scopes:
#             raise HTTPException(403, detail="insufficient scope")
#         return user
#     return checker
#
# @app.get("/observations")
# def observations(user: User = Depends(require_scope("observations:read"))):
#     return {"user": user.username}
#
# def make_token(username: str, scopes: list[str], secret: str) -> str:
#     return jwt.encode({"sub": username, "scopes": scopes}, secret, algorithm="HS256")
#
# with TestClient(app) as client:
#     token = make_token("alice", ["observations:read"], SECRET)
#     r = client.get("/observations", headers={"Authorization": f"Bearer {token}"})
#     # → 200
#     token2 = make_token("bob", [], SECRET)
#     r = client.get("/observations", headers={"Authorization": f"Bearer {token2}"})
#     # → 403
# =============================================================================


def run_drill_108():
    # =========================================================================
    # SCENARIO: Telescope Array
    #
    # A telescope array API is used by astronomers and engineers. Permissions
    # are scope-based: reading observations requires "observations:read",
    # submitting new targets requires "targets:write", and adjusting the
    # telescope hardware requires "telescope:control". A user may hold any
    # combination of these scopes. The system uses JWT auth with scopes
    # embedded in the token.
    #
    # REQUIREMENTS
    # ------------
    # 1. SECRET_KEY: str
    #       The HS256 signing secret. Value: "array-secret"
    #
    # 2. APP_STATE: dict
    #       Shared state dict, starts empty.
    #       Lifespan loads APP_STATE["secret"] = SECRET_KEY at startup
    #       and clears at shutdown.
    #
    # 3. OBSERVATIONS: list[dict]
    #       In-memory list of recorded observations.
    #       Pre-populate with:
    #         [
    #           {"id": 1, "target": "M31", "wavelength": "optical", "internal_raw": "raw-data-1"},
    #           {"id": 2, "target": "NGC1234", "wavelength": "radio", "internal_raw": "raw-data-2"},
    #         ]
    #
    # 4. TARGETS: list[dict]
    #       In-memory list of scheduled observation targets.
    #       Starts empty. New targets are appended here.
    #
    # 5. ObservationOut: BaseModel
    #       Response schema for an observation record.
    #       Fields: id: int, target: str, wavelength: str
    #       (internal_raw intentionally excluded)
    #
    # 6. TargetIn: BaseModel
    #       Request body for submitting a new target.
    #       Fields: name: str — the astronomical object name to observe,
    #                           e.g. "Andromeda", representing the target
    #                           queued for the next observation window.
    #
    # 7. TargetOut: BaseModel
    #       Response schema for a submitted target.
    #       Fields: id: int, name: str, submitted_by: str
    #
    # 8. User: BaseModel
    #       Fields: username: str, scopes: list[str]
    #
    # 9. lifespan: asynccontextmanager
    #       Startup: APP_STATE["secret"] = SECRET_KEY
    #       Shutdown: APP_STATE.clear()
    #       Passed to FastAPI(lifespan=lifespan)
    #
    # 10. oauth2_scheme: OAuth2PasswordBearer(tokenUrl="/token")
    #
    # 11. make_token(username: str, scopes: list[str], secret: str) -> str
    #       username : str       — the astronomer's username, embedded as "sub".
    #       scopes   : list[str] — the list of permission scope strings
    #                              this token grants, embedded as "scopes".
    #       secret   : str       — the signing key.
    #       Encodes {"sub": username, "scopes": scopes} with HS256. No expiry.
    #       Returns the encoded JWT string.
    #
    # 12. get_current_user(token: str) -> User
    #       token: str — raw bearer token from Authorization header,
    #                    representing the caller's JWT credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes token using APP_STATE["secret"] and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError.
    #       Returns User(username=payload["sub"],
    #                    scopes=payload.get("scopes", []))
    #
    # 13. require_scope(scope: str) -> callable
    #       scope: str — the permission string the caller must possess,
    #                    representing the access level required for an
    #                    endpoint (e.g. "observations:read").
    #       Returns a dependency function (checker) that:
    #         - takes user: User = Depends(get_current_user)
    #         - raises HTTPException(403, detail="insufficient scope")
    #           if scope not in user.scopes
    #         - returns user if scope is present
    #
    # 14. GET /observations
    #       Protected by: require_scope("observations:read")
    #       response_model: list[ObservationOut]
    #       Returns all observations. internal_raw must be stripped.
    #
    # 15. POST /targets
    #       body: TargetIn — the target to schedule.
    #       Protected by: require_scope("targets:write") — inject as user: User
    #       response_model: TargetOut
    #       Appends {"id": len(TARGETS)+1, "name": body.name,
    #                "submitted_by": user.username} to TARGETS.
    #       Returns the new target record.
    #
    # 16. POST /telescope/adjust
    #       Protected by: require_scope("telescope:control")
    #       Returns {"status": "adjusted", "by": user.username}
    # =========================================================================

    from contextlib import asynccontextmanager  # noqa: F401

    from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
    from fastapi.security import OAuth2PasswordBearer  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from jose import JWTError, jwt  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---
    SECRET_KEY: str = "array-secret"
    ALGO: str = "HS256"
    APP_STATE: dict = {}
    OBSERVATIONS: list[dict] = [
        {
            "id": 1,
            "target": "M31",
            "wavelength": "optical",
            "internal_raw": "raw-data-1",
        },
        {
            "id": 2,
            "target": "NGC1234",
            "wavelength": "radio",
            "internal_raw": "raw-data-2",
        },
    ]
    TARGETS: list[dict] = []

    class ObservationOut(BaseModel):
        id: int
        target: str
        wavelength: str

    class TargetIn(BaseModel):
        name: str

    class TargetOut(BaseModel):
        id: int
        name: str
        submitted_by: str

    class User(BaseModel):
        username: str
        scopes: list[str]

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        APP_STATE["secret"] = SECRET_KEY
        yield
        APP_STATE.clear()

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def make_token(username: str, scopes: list[str], secret: str):
        return jwt.encode(
            claims={"sub": username, "scopes": scopes}, key=secret, algorithm=ALGO
        )

    def get_current_user(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(
                token=token, key=APP_STATE["secret"], algorithms=[ALGO]
            )
            return User(username=payload["sub"], scopes=payload.get("scopes", []))
        except JWTError:
            raise HTTPException(401, detail="invalid token")

    def require_scope(scope: str):
        def checker(user: User = Depends(get_current_user)):
            if scope in user.scopes:
                return user
            raise HTTPException(403, detail="insufficient scope")

        return checker

    app = FastAPI(lifespan=lifespan)

    @app.get("/observations", response_model=list[ObservationOut])
    def get_observations(_=Depends(require_scope("observations:read"))):
        return OBSERVATIONS

    @app.post("/targets", response_model=TargetOut)
    def create_target(
        body: TargetIn, user: User = Depends(require_scope("targets:write"))
    ):
        TARGETS.append(
            t := {
                "id": len(TARGETS) + 1,
                "name": body.name,
                "submitted_by": user.username,
            }
        )
        return t

    @app.post("/telescope/adjust")
    def control_scope(user=Depends(require_scope("telescope:control"))):
        return {"status": "adjusted", "by": user.username}

    # ── Tests ─────────────────────────────────────────────────────────────────

    with TestClient(app) as client:
        # tokens with different scope combinations
        reader_token = make_token("alice", ["observations:read"], SECRET_KEY)
        writer_token = make_token("bob", ["targets:write"], SECRET_KEY)
        engineer_token = make_token("carol", ["telescope:control"], SECRET_KEY)
        full_token = make_token(
            "dave",
            ["observations:read", "targets:write", "telescope:control"],
            SECRET_KEY,
        )
        empty_token = make_token("eve", [], SECRET_KEY)

        reader_auth = {"Authorization": f"Bearer {reader_token}"}
        writer_auth = {"Authorization": f"Bearer {writer_token}"}
        engineer_auth = {"Authorization": f"Bearer {engineer_token}"}
        full_auth = {"Authorization": f"Bearer {full_token}"}
        empty_auth = {"Authorization": f"Bearer {empty_token}"}

        # Test 1: reader can list observations
        print("Test 1: reader lists observations")
        r = client.get("/observations", headers=reader_auth)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert all("internal_raw" not in o for o in data)
        print(
            f"  observations: {len(data)}, internal_raw stripped: {all('internal_raw' not in o for o in data)}"
        )
        print("  PASS")

        # Test 2: writer blocked from observations → 403
        print("Test 2: writer blocked from observations -> 403")
        r = client.get("/observations", headers=writer_auth)
        assert r.status_code == 403
        assert r.json()["detail"] == "insufficient scope"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 3: writer can submit a target
        print("Test 3: writer submits a target")
        r = client.post("/targets", json={"name": "Andromeda"}, headers=writer_auth)
        assert r.status_code == 200
        target = r.json()
        assert target["id"] == 1
        assert target["name"] == "Andromeda"
        assert target["submitted_by"] == "bob"
        print(
            f"  id: {target['id']}, name: {target['name']}, submitted_by: {target['submitted_by']}"
        )
        print("  PASS")

        # Test 4: reader blocked from submitting targets → 403
        print("Test 4: reader blocked from targets:write -> 403")
        r = client.post("/targets", json={"name": "Orion"}, headers=reader_auth)
        assert r.status_code == 403
        assert r.json()["detail"] == "insufficient scope"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 5: engineer can adjust telescope
        print("Test 5: engineer adjusts telescope")
        r = client.post("/telescope/adjust", headers=engineer_auth)
        assert r.status_code == 200
        result = r.json()
        assert result["status"] == "adjusted"
        assert result["by"] == "carol"
        print(f"  status: {result['status']}, by: {result['by']}")
        print("  PASS")

        # Test 6: reader blocked from telescope:control → 403
        print("Test 6: reader blocked from telescope:control -> 403")
        r = client.post("/telescope/adjust", headers=reader_auth)
        assert r.status_code == 403
        assert r.json()["detail"] == "insufficient scope"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 7: full token can access all endpoints
        print("Test 7: full-scope token accesses all endpoints")
        r1 = client.get("/observations", headers=full_auth)
        r2 = client.post("/targets", json={"name": "Pleiades"}, headers=full_auth)
        r3 = client.post("/telescope/adjust", headers=full_auth)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 200
        print(
            f"  observations: {r1.status_code}, targets: {r2.status_code}, adjust: {r3.status_code}"
        )
        print("  PASS")

        # Test 8: empty scope token blocked everywhere → 403
        print("Test 8: empty scope token blocked from all endpoints -> 403")
        r1 = client.get("/observations", headers=empty_auth)
        r2 = client.post("/targets", json={"name": "X"}, headers=empty_auth)
        r3 = client.post("/telescope/adjust", headers=empty_auth)
        assert r1.status_code == 403
        assert r2.status_code == 403
        assert r3.status_code == 403
        print(
            f"  observations: {r1.status_code}, targets: {r2.status_code}, adjust: {r3.status_code}"
        )
        print("  PASS")

        # Test 9: missing token → 401
        print("Test 9: missing token -> 401")
        r = client.get("/observations")
        assert r.status_code == 401
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 10: bad token → 401
        print("Test 10: bad token -> 401")
        r = client.get("/observations", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")


run_drill_108()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: reader lists observations
#   observations: 2, internal_raw stripped: True
#   PASS
# Test 2: writer blocked from observations → 403
#   status: 403, detail: insufficient scope
#   PASS
# Test 3: writer submits a target
#   id: 1, name: Andromeda, submitted_by: bob
#   PASS
# Test 4: reader blocked from targets:write → 403
#   status: 403, detail: insufficient scope
#   PASS
# Test 5: engineer adjusts telescope
#   status: adjusted, by: carol
#   PASS
# Test 6: reader blocked from telescope:control → 403
#   status: 403, detail: insufficient scope
#   PASS
# Test 7: full-scope token accesses all endpoints
#   observations: 200, targets: 200, adjust: 200
#   PASS
# Test 8: empty scope token blocked from all endpoints → 403
#   observations: 403, targets: 403, adjust: 403
#   PASS
# Test 9: missing token → 401
#   status: 401
#   PASS
# Test 10: bad token → 401
#   status: 401, detail: invalid token
#   PASS
# =============================================================================
