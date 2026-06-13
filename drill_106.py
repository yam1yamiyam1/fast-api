# =============================================================================
# CONCEPT INTRO — API Key Auth (Header + Query Param)
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# JWT/OAuth2 is designed for user-facing flows. For machine-to-machine calls
# (scripts, external services, dashboards) you often want a simpler scheme:
# a static API key the caller includes on every request. FastAPI provides
# two security classes for this: APIKeyHeader and APIKeyQuery.
#
# NEW IMPORTS
# -----------
# from fastapi.security import APIKeyHeader, APIKeyQuery
#   └─ APIKeyHeader — dependency that reads a key from a named request header
#   └─ APIKeyQuery  — dependency that reads a key from a named query parameter
#
# NEW CLASSES
# -----------
# APIKeyHeader(name: str, auto_error: bool = True) → instance
#   name       : str  — the header name to read from (e.g. "X-API-Key")
#   auto_error : bool — if True (default), raises 403 automatically when
#                       the header is absent. Set False to handle manually.
#   When resolved: returns the header value as str, or raises 403 if missing.
#
# APIKeyQuery(name: str, auto_error: bool = True) → instance
#   name       : str  — the query param name to read from (e.g. "api_key")
#   auto_error : bool — same as above but for the query param.
#   When resolved: returns the query param value as str, or raises 403 if missing.
#
# ACCEPTING EITHER HEADER OR QUERY PARAM
# ----------------------------------------
# Set auto_error=False on both so neither raises on its own. Your dep
# then checks whichever one is present and raises 403 if neither is valid:
#
#   api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
#   api_key_query  = APIKeyQuery(name="api_key",   auto_error=False)
#
#   VALID_KEYS = {"key-abc", "key-xyz"}
#
#   def get_api_key(
#       header_key: str | None = Depends(api_key_header),
#       query_key:  str | None = Depends(api_key_query),
#   ) -> str:
#       key = header_key or query_key
#       if key not in VALID_KEYS:
#           raise HTTPException(status_code=403, detail="invalid api key")
#       return key
#
# PURE PYTHON TRANSLATION
# -----------------------
# Pure Python (manual header parse):         FastAPI equivalent:
# ─────────────────────────────────────────  ──────────────────────────────────
# key = request.headers.get("X-API-Key")     header_key = Depends(api_key_header)
# key = key or request.query.get("api_key")  query_key  = Depends(api_key_query)
# if key not in VALID_KEYS: raise 403        if key not in VALID_KEYS: raise 403
#
# WIRING EXAMPLE
# --------------
# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.security import APIKeyHeader, APIKeyQuery
# from fastapi.testclient import TestClient
#
# app = FastAPI()
# api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
# api_key_query  = APIKeyQuery(name="api_key",    auto_error=False)
# VALID_KEYS = {"key-abc"}
#
# def get_api_key(
#     header_key: str | None = Depends(api_key_header),
#     query_key:  str | None = Depends(api_key_query),
# ) -> str:
#     key = header_key or query_key
#     if key not in VALID_KEYS:
#         raise HTTPException(status_code=403, detail="invalid api key")
#     return key
#
# @app.get("/data")
# def data(key: str = Depends(get_api_key)):
#     return {"key": key}
#
# client = TestClient(app)
# r = client.get("/data", headers={"X-API-Key": "key-abc"})  # → 200
# r = client.get("/data?api_key=key-abc")                    # → 200
# r = client.get("/data")                                    # → 403
# r = client.get("/data", headers={"X-API-Key": "bad"})      # → 403
# =============================================================================


def run_drill_106():
    # =========================================================================
    # SCENARIO: Airport Control Tower
    #
    # An airport control tower API is accessed by automated ground systems
    # and external aviation services. These machine clients authenticate with
    # a static API key, passed either as a header or a query parameter.
    # The API exposes runway status and flight slot records.
    #
    # REQUIREMENTS
    # ------------
    # 1. VALID_KEYS: set[str]
    #       In-memory set of valid API keys.
    #       Represents all authorised machine clients.
    #       Pre-populate with: {"tower-key-1", "tower-key-2"}
    #
    # 2. RUNWAYS: dict[str, dict]
    #       In-memory map from runway identifier (str) to runway status dict.
    #       Represents current operational status of each runway.
    #       Pre-populate with:
    #         "09L": {"id": "09L", "status": "open",   "surface": "asphalt", "internal_inspection": "due"}
    #         "27R": {"id": "27R", "status": "closed", "surface": "concrete", "internal_inspection": "overdue"}
    #
    # 3. SLOTS: list[dict]
    #       In-memory list of flight slot records.
    #       Represents scheduled landing/departure windows.
    #       Pre-populate with:
    #         [
    #           {"id": 1, "flight": "QZ401", "runway": "09L", "type": "landing",   "internal_priority": 1},
    #           {"id": 2, "flight": "QZ808", "runway": "27R", "type": "departure", "internal_priority": 2},
    #           {"id": 3, "flight": "QZ212", "runway": "09L", "type": "landing",   "internal_priority": 3},
    #         ]
    #
    # 4. RunwayOut: BaseModel
    #       Response schema for a runway record.
    #       Fields: id: str, status: str, surface: str
    #       (internal_inspection intentionally excluded)
    #
    # 5. SlotOut: BaseModel
    #       Response schema for a flight slot.
    #       Fields: id: int, flight: str, runway: str, type: str
    #       (internal_priority intentionally excluded)
    #
    # 6. api_key_header: APIKeyHeader
    #       Reads the API key from the "X-API-Key" request header.
    #       auto_error=False — does not raise on its own.
    #
    # 7. api_key_query: APIKeyQuery
    #       Reads the API key from the "api_key" query parameter.
    #       auto_error=False — does not raise on its own.
    #
    # 8. get_api_key(header_key, query_key) -> str
    #       header_key: str | None — API key from the X-API-Key header,
    #                                representing the machine client's
    #                                header-based credential. May be None.
    #       query_key:  str | None — API key from the api_key query param,
    #                                representing the machine client's
    #                                query-based credential. May be None.
    #       Must declare:
    #         header_key: str | None = Depends(api_key_header)
    #         query_key:  str | None = Depends(api_key_query)
    #       Uses header_key if present, otherwise query_key.
    #       Raises HTTPException(403, detail="invalid api key") if the
    #       resolved key is not in VALID_KEYS.
    #       Returns the valid key string.
    #
    # 9. GET /runways
    #       Protected by: Depends(get_api_key)
    #       response_model: list[RunwayOut]
    #       Returns all runways. internal_inspection must be stripped.
    #
    # 10. GET /runways/{runway_id}
    #       runway_id: str — the runway identifier (e.g. "09L"),
    #                        representing a specific runway to look up.
    #       Protected by: Depends(get_api_key)
    #       response_model: RunwayOut
    #       Raises HTTPException(404, detail="runway not found") if not found.
    #       Returns the matching runway. internal_inspection must be stripped.
    #
    # 11. GET /slots
    #       Protected by: Depends(get_api_key)
    #       Query param: runway: Optional[str] = None — a filter string
    #           representing the runway identifier to narrow slot results.
    #           When None, all slots are returned.
    #       response_model: list[SlotOut]
    #       Returns all slots matching runway filter (or all if None).
    #       internal_priority must be stripped.
    # =========================================================================

    from typing import Optional  # noqa: F401

    from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
    from fastapi.security import APIKeyHeader, APIKeyQuery  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---
    VALID_KEYS: set[str] = {"tower-key-1", "tower-key-2"}
    RUNWAYS: dict[str, dict] = {
        "09L": {
            "id": "09L",
            "status": "open",
            "surface": "asphalt",
            "internal_inspection": "due",
        },
        "27R": {
            "id": "27R",
            "status": "closed",
            "surface": "concrete",
            "internal_inspection": "overdue",
        },
    }
    SLOTS: list[dict] = [
        {
            "id": 1,
            "flight": "QZ401",
            "runway": "09L",
            "type": "landing",
            "internal_priority": 1,
        },
        {
            "id": 2,
            "flight": "QZ808",
            "runway": "27R",
            "type": "departure",
            "internal_priority": 2,
        },
        {
            "id": 3,
            "flight": "QZ212",
            "runway": "09L",
            "type": "landing",
            "internal_priority": 3,
        },
    ]

    class RunwayOut(BaseModel):
        id: str
        status: str
        surface: str

    class SlotOut(BaseModel):
        id: int
        flight: str
        runway: str
        type: str

    api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
    api_key_query = APIKeyQuery(name="api_key", auto_error=False)

    def get_api_key(
        header_key: str | None = Depends(api_key_header),
        query_key: str | None = Depends(api_key_query),
    ):
        key = header_key or query_key
        if (key := header_key or query_key) in VALID_KEYS:
            return key
        raise HTTPException(403, detail="invalid api key")

    app = FastAPI()

    @app.get("/runways", response_model=list[RunwayOut])
    def get_runways(_=Depends(get_api_key)):
        return list(RUNWAYS.values())

    @app.get("/runways/{runway_id}", response_model=RunwayOut)
    def get_runway(runway_id: str, _=Depends(get_api_key)):
        if runway := RUNWAYS.get(runway_id):
            return runway
        raise HTTPException(404, detail="runway not found")

    @app.get("/slots", response_model=list[SlotOut])
    def get_slots(runway: Optional[str] = None, _=Depends(get_api_key)):
        return [s for s in SLOTS if not runway or s["runway"] == runway]

    # ── Tests ─────────────────────────────────────────────────────────────────

    client = TestClient(app)

    # Test 1: valid key via header — list runways
    print("Test 1: valid header key returns all runways")
    r = client.get("/runways", headers={"X-API-Key": "tower-key-1"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert all("internal_inspection" not in rw for rw in data)
    print(
        f"  runways: {len(data)}, internal_inspection stripped: {all('internal_inspection' not in rw for rw in data)}"
    )
    print("  PASS")

    # Test 2: valid key via query param — list runways
    print("Test 2: valid query param key returns all runways")
    r = client.get("/runways?api_key=tower-key-2")
    assert r.status_code == 200
    assert len(r.json()) == 2
    print(f"  runways: {len(r.json())}")
    print("  PASS")

    # Test 3: get runway by ID via header key
    print("Test 3: fetch runway by ID")
    r = client.get("/runways/09L", headers={"X-API-Key": "tower-key-1"})
    assert r.status_code == 200
    rw = r.json()
    assert rw["id"] == "09L"
    assert rw["status"] == "open"
    assert "internal_inspection" not in rw
    print(
        f"  id: {rw['id']}, status: {rw['status']}, internal_inspection present: {'internal_inspection' in rw}"
    )
    print("  PASS")

    # Test 4: runway not found → 404
    print("Test 4: unknown runway_id -> 404")
    r = client.get("/runways/99X", headers={"X-API-Key": "tower-key-1"})
    assert r.status_code == 404
    assert r.json()["detail"] == "runway not found"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 5: list all slots
    print("Test 5: list all slots")
    r = client.get("/slots", headers={"X-API-Key": "tower-key-1"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    assert all("internal_priority" not in s for s in data)
    print(
        f"  slots: {len(data)}, internal_priority stripped: {all('internal_priority' not in s for s in data)}"
    )
    print("  PASS")

    # Test 6: filter slots by runway
    print("Test 6: filter slots by runway")
    r = client.get("/slots?runway=09L", headers={"X-API-Key": "tower-key-2"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert all(s["runway"] == "09L" for s in data)
    print(f"  09L slots: {len(data)}")
    print("  PASS")

    # Test 7: missing key → 403
    print("Test 7: missing api key -> 403")
    r = client.get("/runways")
    assert r.status_code == 403
    assert r.json()["detail"] == "invalid api key"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 8: invalid header key → 403
    print("Test 8: invalid header key -> 403")
    r = client.get("/runways", headers={"X-API-Key": "bad-key"})
    assert r.status_code == 403
    assert r.json()["detail"] == "invalid api key"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 9: invalid query key → 403
    print("Test 9: invalid query key -> 403")
    r = client.get("/slots?api_key=bad-key")
    assert r.status_code == 403
    assert r.json()["detail"] == "invalid api key"
    print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
    print("  PASS")

    # Test 10: header key takes precedence over query key when both present
    print("Test 10: valid header key wins over invalid query key")
    r = client.get("/runways?api_key=bad-key", headers={"X-API-Key": "tower-key-1"})
    assert r.status_code == 200
    print(f"  status: {r.status_code}")
    print("  PASS")


run_drill_106()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: valid header key returns all runways
#   runways: 2, internal_inspection stripped: True
#   PASS
# Test 2: valid query param key returns all runways
#   runways: 2
#   PASS
# Test 3: fetch runway by ID
#   id: 09L, status: open, internal_inspection present: False
#   PASS
# Test 4: unknown runway_id → 404
#   status: 404, detail: runway not found
#   PASS
# Test 5: list all slots
#   slots: 3, internal_priority stripped: True
#   PASS
# Test 6: filter slots by runway
#   09L slots: 2
#   PASS
# Test 7: missing api key → 403
#   status: 403, detail: invalid api key
#   PASS
# Test 8: invalid header key → 403
#   status: 403, detail: invalid api key
#   PASS
# Test 9: invalid query key → 403
#   status: 403, detail: invalid api key
#   PASS
# Test 10: valid header key wins over invalid query key
#   status: 200
#   PASS
# =============================================================================
