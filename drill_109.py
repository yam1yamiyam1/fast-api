# =============================================================================
# CONCEPT INTRO — Auth Middleware (Global vs Per-Route)
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# Per-route Depends() works well but repeating it on every endpoint is noisy.
# Middleware lets you enforce auth globally — every request passes through it
# before hitting any route. You can then carve out public routes as exceptions.
#
# The tradeoff: middleware runs before FastAPI resolves path params and deps,
# so you don't get a User object injected — just raw request headers.
# Use middleware for coarse global gates; use Depends() for fine-grained logic.
#
# NEW PATTERN — @app.middleware("http")
# --------------------------------------
# Already covered in D83 (pure Python call_next pattern). In real FastAPI:
#
#   @app.middleware("http")
#   async def auth_middleware(request: Request, call_next):
#       # runs before every route handler
#       response = await call_next(request)
#       # runs after every route handler
#       return response
#
# NEW IMPORT
# ----------
# from fastapi import Request
#   └─ Request — gives access to request.headers, request.url.path,
#                request.method inside middleware
#
# GLOBAL GATE WITH PUBLIC ROUTE EXCEPTIONS
# -----------------------------------------
#   PUBLIC_PATHS = {"/health", "/token"}
#
#   @app.middleware("http")
#   async def auth_middleware(request: Request, call_next):
#       if request.url.path in PUBLIC_PATHS:
#           return await call_next(request)   # skip auth for public routes
#       token = request.headers.get("Authorization", "")
#       if not token.startswith("Bearer "):
#           return JSONResponse({"detail": "not authenticated"}, status_code=401)
#       # validate token here...
#       return await call_next(request)
#
# NEW IMPORT
# ----------
# from fastapi.responses import JSONResponse
#   └─ JSONResponse(content: dict, status_code: int) — returns a JSON HTTP
#      response directly from middleware (bypasses route handlers).
#      Use this instead of raising HTTPException inside middleware, because
#      HTTPException is only caught by FastAPI's exception handlers which
#      run after middleware.
#
# PURE PYTHON TRANSLATION
# -----------------------
# Pure Python (D83 call_next middleware):    FastAPI equivalent:
# ─────────────────────────────────────────  ──────────────────────────────────
# async def mw(request, call_next):          @app.middleware("http")
#     if request.path in PUBLIC: ...         async def mw(request: Request, call_next):
#     token = request.headers["Auth"]            if request.url.path in PUBLIC: ...
#     await call_next(request)                   token = request.headers.get("Authorization")
#                                                return await call_next(request)
#
# WIRING EXAMPLE
# --------------
# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# from fastapi.testclient import TestClient
#
# app = FastAPI()
# VALID_KEYS = {"key-abc"}
# PUBLIC_PATHS = {"/health"}
#
# @app.middleware("http")
# async def api_key_gate(request: Request, call_next):
#     if request.url.path in PUBLIC_PATHS:
#         return await call_next(request)
#     key = request.headers.get("X-API-Key", "")
#     if key not in VALID_KEYS:
#         return JSONResponse({"detail": "not authenticated"}, status_code=401)
#     return await call_next(request)
#
# @app.get("/health")
# def health():
#     return {"status": "ok"}
#
# @app.get("/data")
# def data():
#     return {"secret": "stuff"}
#
# client = TestClient(app)
# client.get("/health")                              # → 200, no key needed
# client.get("/data", headers={"X-API-Key": "key-abc"})  # → 200
# client.get("/data")                                # → 401
# =============================================================================


def run_drill_109():
    # =========================================================================
    # SCENARIO: Space Station
    #
    # A space station operations API is protected by a global API-key
    # middleware that gates all routes except the public /health endpoint.
    # Individual sensitive routes additionally require a specific role
    # embedded in a JWT — demonstrating global middleware + per-route dep
    # working together in the same app.
    #
    # REQUIREMENTS
    # ------------
    # 1. SECRET_KEY: str
    #       The HS256 signing secret. Value: "station-secret"
    #
    # 2. VALID_API_KEYS: set[str]
    #       Set of valid API keys for the global gate.
    #       Pre-populate with: {"station-key-1", "station-key-2"}
    #
    # 3. MODULES: list[dict]
    #       In-memory list of station module status records.
    #       Pre-populate with:
    #         [
    #           {"id": 1, "name": "Habitat",    "status": "nominal"},
    #           {"id": 2, "name": "Solar Array", "status": "degraded"},
    #         ]
    #
    # 4. PUBLIC_PATHS: set[str]
    #       Set of URL paths that bypass the global auth middleware.
    #       Value: {"/health"}
    #
    # 5. User: BaseModel
    #       Fields: username: str, role: str
    #
    # 6. oauth2_scheme: OAuth2PasswordBearer(tokenUrl="/token")
    #
    # 7. make_token(username: str, role: str, secret: str) -> str
    #       username : str — the crew member's username, embedded as "sub".
    #       role     : str — the crew member's role, embedded as "role".
    #       secret   : str — the signing key.
    #       Encodes {"sub": username, "role": role} with HS256. No expiry.
    #       Returns the encoded JWT string.
    #
    # 8. get_current_user(token: str) -> User
    #       token: str — raw bearer token from Authorization header,
    #                    representing the caller's JWT credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes using SECRET_KEY and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError.
    #       Returns User(username=payload["sub"], role=payload["role"])
    #
    # 9. auth_middleware(request: Request, call_next) — @app.middleware("http")
    #       request  : Request  — the incoming HTTP request, used to read
    #                             the URL path and X-API-Key header.
    #       call_next : callable — passes the request to the next handler,
    #                              representing the rest of the request pipeline.
    #       If request.url.path is in PUBLIC_PATHS: skip auth, call call_next.
    #       Otherwise: read "X-API-Key" from request.headers.
    #       If the key is not in VALID_API_KEYS:
    #           return JSONResponse({"detail": "not authenticated"}, status_code=401)
    #       Otherwise: call call_next and return the response.
    #
    # 10. GET /health
    #       No auth required (public path).
    #       Returns {"status": "ok"}
    #
    # 11. GET /modules
    #       Requires valid X-API-Key header (enforced by middleware).
    #       No additional per-route dep.
    #       Returns list of all module dicts (no response_model stripping needed).
    #
    # 12. POST /eva/approve
    #       Requires valid X-API-Key header (enforced by middleware).
    #       Additionally protected by: Depends(get_current_user) with
    #       role check — raises HTTPException(403, detail="commanders only")
    #       if user.role != "commander".
    #       Returns {"approved": True, "by": user.username}
    # =========================================================================
    from contextlib import asynccontextmanager  # noqa: F401

    from fastapi import Depends, FastAPI, HTTPException, Request  # noqa: F401
    from fastapi.responses import JSONResponse  # noqa: F401
    from fastapi.security import OAuth2PasswordBearer  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from jose import JWTError, jwt  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---
    SECRET_KEY: str = "station-secret"
    ALGO = "HS256"
    VALID_API_KEYS: set[str] = {"station-key-1", "station-key-2"}
    MODULES: list[dict] = [
        {"id": 1, "name": "Habitat", "status": "nominal"},
        {"id": 2, "name": "Solar Array", "status": "degraded"},
    ]
    PUBLIC_PATHS: set[str] = {"/health"}

    class User(BaseModel):
        username: str
        role: str

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def make_token(username: str, role: str, secret: str):
        return jwt.encode(
            claims={"sub": username, "role": role}, key=secret, algorithm=ALGO
        )

    def get_current_user(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=ALGO)
            return User(username=payload.get("sub"), role=payload.get("role"))
        except JWTError:
            raise HTTPException(401, detail="invalid token")

    # ── Tests ─────────────────────────────────────────────────────────────────

    client = TestClient(app)

    key1 = {"X-API-Key": "station-key-1"}
    key2 = {"X-API-Key": "station-key-2"}
    bad_key = {"X-API-Key": "bad"}

    commander_token = make_token("maj-chen", "commander", SECRET_KEY)
    crew_token = make_token("eng-park", "crew", SECRET_KEY)
    cmd_auth = {**key1, "Authorization": f"Bearer {commander_token}"}
    crew_auth = {**key1, "Authorization": f"Bearer {crew_token}"}

    # Test 1: /health is public — no key needed
    print("Test 1: /health accessible without API key")
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    print(f"  status: {r.status_code}, body: {r.json()}")
    print("  PASS")

    # Test 2: valid key lists modules
    print("Test 2: valid API key lists modules")
    r = client.get("/modules", headers=key1)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    print(f"  modules: {len(data)}")
    print("  PASS")

    # Test 3: missing key blocked by middleware → 401
    print("Test 3: missing API key → 401 from middleware")
    r = client.get("/modules")
    assert r.status_code == 401
    assert r.json()["detail"] == "not authenticated"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 4: bad key blocked by middleware → 401
    print("Test 4: invalid API key → 401 from middleware")
    r = client.get("/modules", headers=bad_key)
    assert r.status_code == 401
    assert r.json()["detail"] == "not authenticated"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 5: commander approves EVA
    print("Test 5: commander approves EVA")
    r = client.post("/eva/approve", headers=cmd_auth)
    assert r.status_code == 200
    result = r.json()
    assert result["approved"] is True
    assert result["by"] == "maj-chen"
    print(f"  approved: {result['approved']}, by: {result['by']}")
    print("  PASS")

    # Test 6: crew role blocked from EVA approval → 403
    print("Test 6: non-commander blocked from EVA → 403")
    r = client.post("/eva/approve", headers=crew_auth)
    assert r.status_code == 403
    assert r.json()["detail"] == "commanders only"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 7: valid key but no JWT on EVA route → 401
    print("Test 7: valid API key but no JWT on EVA route → 401")
    r = client.post("/eva/approve", headers=key2)
    assert r.status_code == 401
    print(f"  status: {r.status_code}")
    print("  PASS")

    # Test 8: key2 also valid for modules
    print("Test 8: second valid key also works")
    r = client.get("/modules", headers=key2)
    assert r.status_code == 200
    print(f"  status: {r.status_code}")
    print("  PASS")


run_drill_109()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: /health accessible without API key
#   status: 200, body: {'status': 'ok'}
#   PASS
# Test 2: valid API key lists modules
#   modules: 2
#   PASS
# Test 3: missing API key → 401 from middleware
#   status: 401, detail: not authenticated
#   PASS
# Test 4: invalid API key → 401 from middleware
#   status: 401, detail: not authenticated
#   PASS
# Test 5: commander approves EVA
#   approved: True, by: maj-chen
#   PASS
# Test 6: non-commander blocked from EVA → 403
#   status: 403, detail: commanders only
#   PASS
# Test 7: valid API key but no JWT on EVA route → 401
#   status: 401
#   PASS
# Test 8: second valid key also works
#   status: 200
#   PASS
# =============================================================================
