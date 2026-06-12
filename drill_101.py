# =============================================================================
# CONCEPT INTRO — OAuth2PasswordBearer
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# You need to protect endpoints so only callers who present a valid token
# (in the Authorization header) are allowed through. OAuth2PasswordBearer
# is a FastAPI dependency that extracts that token for you automatically.
# Without it you'd have to manually parse the "Authorization: Bearer <tok>"
# header on every request.
#
# NEW IMPORTS
# -----------
# from fastapi.security import OAuth2PasswordBearer
#   └─ OAuth2PasswordBearer  — a callable class that acts as a dependency.
#                              When invoked by FastAPI it reads the
#                              Authorization header, strips the "Bearer "
#                              prefix, and returns the raw token string.
#                              If the header is missing it raises 401
#                              automatically.
#
# NEW CLASS
# ---------
# OAuth2PasswordBearer(tokenUrl: str) → instance
#   tokenUrl : str  — the path where clients POST credentials to get a token
#                     (e.g. "/token"). FastAPI uses this only for OpenAPI docs;
#                     it does NOT create the route for you.
#   Returns  : a dependency callable; when resolved it returns str (the token).
#   Raises   : HTTPException(401) automatically if Authorization header absent.
#
# SIGNATURE IN USE
# ----------------
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
#
# async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
#     ...  # validate token here
#
# @app.get("/protected")
# def protected(user: dict = Depends(get_current_user)): ...
#
# PURE PYTHON TRANSLATION
# -----------------------
# Pure Python (D68 chained deps):            FastAPI equivalent:
# ─────────────────────────────────────────  ──────────────────────────────────
# deps = {"token": extract_token_fn}         oauth2_scheme = OAuth2PasswordBearer(...)
# token = await deps["token"](request)       token: str = Depends(oauth2_scheme)
# user  = await get_user(token)              user: dict = Depends(get_current_user)
# inject user into handler                   FastAPI injects automatically
#
# MINIMAL WIRING EXAMPLE
# ----------------------
# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer
# from fastapi.testclient import TestClient
#
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
# VALID_TOKENS = {"abc123": {"username": "alice"}}
#
# def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
#     user = VALID_TOKENS.get(token)
#     if not user:
#         raise HTTPException(status_code=401, detail="invalid token")
#     return user
#
# app = FastAPI()
#
# @app.get("/me")
# def me(user: dict = Depends(get_current_user)):
#     return user
#
# client = TestClient(app)
# r = client.get("/me", headers={"Authorization": "Bearer abc123"})
# # → 200, {"username": "alice"}
# r = client.get("/me", headers={"Authorization": "Bearer bad"})
# # → 401
# r = client.get("/me")
# # → 401 (no header at all)
# =============================================================================


def run_drill_101():
    # =========================================================================
    # SCENARIO: Blood Bank
    #
    # A blood bank API allows registered technicians to look up blood unit
    # records. Only technicians who present a valid bearer token may access
    # the records. Each token belongs to exactly one technician. Units are
    # identified by a numeric ID. The system also filters by blood type when
    # requested.
    #
    # REQUIREMENTS
    # ------------
    # 1. VALID_TOKENS: dict[str, dict]
    #       In-memory map from token string to technician info dict.
    #       Represents the set of all active session tokens issued to
    #       technicians. Pre-populate with at least two entries:
    #         "token-alice": {"username": "alice", "role": "technician"}
    #         "token-bob":   {"username": "bob",   "role": "technician"}
    #
    # 2. BLOOD_UNITS: dict[int, dict]
    #       In-memory map from unit ID (int) to blood unit record dict.
    #       Represents the blood bank's inventory of stored units.
    #       Pre-populate with at least three entries:
    #         1: {"id": 1, "blood_type": "A+", "volume_ml": 450, "donor": "donor-1"}
    #         2: {"id": 2, "blood_type": "O-", "volume_ml": 500, "donor": "donor-2"}
    #         3: {"id": 3, "blood_type": "A+", "volume_ml": 475, "donor": "donor-3"}
    #
    # 3. UnitOut: BaseModel
    #       Response schema for a single blood unit.
    #       Fields: id: int, blood_type: str, volume_ml: int
    #       (donor field is intentionally excluded — internal only)
    #
    # 4. oauth2_scheme: OAuth2PasswordBearer
    #       Dependency that extracts the bearer token from the
    #       Authorization header. tokenUrl should be "/token".
    #
    # 5. get_current_technician(token: str) -> dict
    #       token: str — the raw bearer token extracted from the
    #                    Authorization header, representing the caller's
    #                    session credential.
    #       Dependency function. Looks up token in VALID_TOKENS.
    #       Raises HTTPException(401, detail="invalid token") if not found.
    #       Returns the technician dict on success.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #
    # 6. GET /units
    #       Query param: blood_type: Optional[str] = None — a filter string
    #           representing the ABO/Rh blood type to narrow results
    #           (e.g. "A+"). When None, all units are returned.
    #       Protected by: technician: dict = Depends(get_current_technician)
    #       response_model: list[UnitOut]
    #       Returns all units matching blood_type filter (or all if None).
    #       The "donor" field must be stripped from every response item.
    #
    # 7. GET /units/{unit_id}
    #       unit_id: int — the numeric identifier of a specific blood unit
    #                      in the inventory.
    #       Protected by: technician: dict = Depends(get_current_technician)
    #       response_model: UnitOut
    #       Raises HTTPException(404, detail="unit not found") if unit_id
    #       not in BLOOD_UNITS.
    #       Returns the matching unit. The "donor" field must be stripped.
    # =========================================================================

    from typing import Optional  # noqa: F401

    from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
    from fastapi.security import OAuth2PasswordBearer  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---
    VALID_TOKENS: dict[str, dict] = {
        "token-alice": {"username": "alice", "role": "technician"},
        "token-bob": {"username": "bob", "role": "technician"},
    }
    BLOOD_UNITS: dict[int, dict] = {
        1: {"id": 1, "blood_type": "A+", "volume_ml": 450, "donor": "donor-1"},
        2: {"id": 2, "blood_type": "O-", "volume_ml": 500, "donor": "donor-2"},
        3: {"id": 3, "blood_type": "A+", "volume_ml": 475, "donor": "donor-3"},
    }

    class UnitOut(BaseModel):
        id: int
        blood_type: str
        volume_ml: int

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def get_current_technician(token: str = Depends(oauth2_scheme)):
        if token not in VALID_TOKENS:
            raise HTTPException(401, detail="invalid token")
        return VALID_TOKENS[token]

    app = FastAPI()

    @app.get("/units", response_model=list[UnitOut])
    def get_units(
        blood_type: Optional[str] = None,
        _: dict = Depends(get_current_technician),
    ):
        return [
            u
            for u in BLOOD_UNITS.values()
            if not blood_type or u["blood_type"] == blood_type
        ]

    @app.get("/units/{unit_id}", response_model=UnitOut)
    def get_unit(
        unit_id: int,
        _: dict = Depends(get_current_technician),
    ):
        if unit := BLOOD_UNITS.get(unit_id):
            return unit
        raise HTTPException(404, detail="unit not found")

    # ── Tests ─────────────────────────────────────────────────────────────────

    client = TestClient(app)

    # Test 1: valid token — list all units
    print("Test 1: valid token returns all units")
    r = client.get("/units", headers={"Authorization": "Bearer token-alice"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    assert all("donor" not in unit for unit in data)
    print(
        f"  units returned: {len(data)}, donor stripped: {all('donor' not in u for u in data)}"
    )
    print("  PASS")

    # Test 2: valid token — filter by blood_type
    print("Test 2: blood_type filter returns matching units only")
    r = client.get(
        "/units?blood_type=A%2B", headers={"Authorization": "Bearer token-bob"}
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert all(u["blood_type"] == "A+" for u in data)
    print(f"  A+ units: {len(data)}")
    print("  PASS")

    # Test 3: valid token — get specific unit by ID
    print("Test 3: valid token fetches unit by ID")
    r = client.get("/units/2", headers={"Authorization": "Bearer token-alice"})
    assert r.status_code == 200
    unit = r.json()
    assert unit["id"] == 2
    assert unit["blood_type"] == "O-"
    assert "donor" not in unit
    print(
        f"  unit id: {unit['id']}, blood_type: {unit['blood_type']}, donor present: {'donor' in unit}"
    )
    print("  PASS")

    # Test 4: missing Authorization header → 401
    print("Test 4: missing token -> 401")
    r = client.get("/units")
    assert r.status_code == 401
    print(f"  status: {r.status_code}")
    print("  PASS")

    # Test 5: invalid token → 401
    print("Test 5: invalid token -> 401")
    r = client.get("/units", headers={"Authorization": "Bearer bad-token"})
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid token"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 6: unit not found → 404
    print("Test 6: unknown unit_id -> 404")
    r = client.get("/units/999", headers={"Authorization": "Bearer token-alice"})
    assert r.status_code == 404
    assert r.json()["detail"] == "unit not found"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 7: filter with no matches returns empty list
    print("Test 7: blood_type filter with no matches -> empty list")
    r = client.get(
        "/units?blood_type=AB-", headers={"Authorization": "Bearer token-bob"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data == []
    print(f"  result: {data}")
    print("  PASS")


run_drill_101()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: valid token returns all units
#   units returned: 3, donor stripped: True
#   PASS
# Test 2: blood_type filter returns matching units only
#   A+ units: 2
#   PASS
# Test 3: valid token fetches unit by ID
#   unit id: 2, blood_type: O-, donor present: False
#   PASS
# Test 4: missing token → 401
#   status: 401
#   PASS
# Test 5: invalid token → 401
#   status: 401, detail: invalid token
#   PASS
# Test 6: unknown unit_id → 404
#   status: 404, detail: unit not found
#   PASS
# Test 7: blood_type filter with no matches → empty list
#   result: []
#   PASS
# =============================================================================
