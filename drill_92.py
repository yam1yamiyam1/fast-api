import asyncio  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import FastAPI  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — Path params + Query params + Type coercion  (Drill 92)
#
# Pure Python:
#   match = re.match(r"^/stations/(?P<station_id>\d+)$", path)
#   station_id = int(match.groupdict()["station_id"])
#   query params parsed manually from URL string
#
# FastAPI:
#   @app.get("/stations/{station_id}")
#   def get_station(station_id: int, active: bool = True):
#       ...
#   # station_id comes from the path — FastAPI casts it to int
#   # active comes from ?active=false — FastAPI casts it to bool
#   # GET /stations/7?active=false  →  station_id=7, active=False
#
# What it solves: no more manual regex groupdict() or int() casting.
#   FastAPI reads the type annotation and coerces automatically.
#   Wrong type → 422 before your function is called.
# Rule: path param name in the decorator must match the function arg name exactly.
# ─────────────────────────────────────────────


def run_drill_92():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Power grid control panel.  Engineers look up individual substations
    by ID and can filter results by whether the substation is currently
    online.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. SUBSTATIONS: list[dict]  — in-memory store defined before app,
       pre-populated with exactly these three records (in this order):
         {"id": 1, "name": "Alpha",   "online": True}
         {"id": 2, "name": "Beta",    "online": False}
         {"id": 3, "name": "Gamma",   "online": True}

    2. GET /substations/{substation_id}
       • substation_id: int — the numeric ID of the substation to retrieve,
         extracted from the URL path and coerced to int by FastAPI.
       • Returns the matching dict from SUBSTATIONS.
       • If no substation with that id exists, returns {"error": "not found"}.

    3. GET /substations
       • online: Optional[bool] = None — query parameter that filters
         the list to only substations whose "online" value matches;
         if omitted, all substations are returned.
       • Returns the filtered (or full) list.

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    SUBSTATIONS: list[dict] = [
        {"id": 1, "name": "Alpha", "online": True},
        {"id": 2, "name": "Beta", "online": False},
        {"id": 3, "name": "Gamma", "online": True},
    ]
    app = FastAPI()

    @app.get("/substations/{substation_id}")
    def get_substation(substation_id: int):
        return next(
            (s for s in SUBSTATIONS if s["id"] == substation_id), {"error": "not found"}
        )

    @app.get("/substations")
    def get_online(online: Optional[bool] = None):
        if online is None:
            return SUBSTATIONS
        return list(filter(lambda x: x["online"] == online, SUBSTATIONS))

    # ── TESTS ──────────────────────────────────────────────────────────
    client = TestClient(app)  # noqa: F821

    # Test 1: GET /substations with no filter returns all three
    print("Test 1: GET /substations returns all")
    r = client.get("/substations")
    assert r.status_code == 200
    assert len(r.json()) == 3
    print(f"  status={r.status_code}, count={len(r.json())}")
    print("  PASS")

    # Test 2: GET /substations?online=true returns only online ones
    print("Test 2: GET /substations?online=true returns 2")
    r = client.get("/substations?online=true")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert all(s["online"] for s in r.json())
    print(f"  status={r.status_code}, count={len(r.json())}")
    print("  PASS")

    # Test 3: GET /substations?online=false returns only offline ones
    print("Test 3: GET /substations?online=false returns 1")
    r = client.get("/substations?online=false")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Beta"
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 4: GET /substations/2 returns Beta
    print("Test 4: GET /substations/2 returns Beta")
    r = client.get("/substations/2")
    assert r.status_code == 200
    assert r.json()["name"] == "Beta"
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 5: GET /substations/99 returns error dict
    print("Test 5: GET /substations/99 returns not found")
    r = client.get("/substations/99")
    assert r.status_code == 200
    assert r.json() == {"error": "not found"}
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 6: GET /substations/abc returns 422 (type coercion failure)
    print("Test 6: GET /substations/abc returns 422")
    r = client.get("/substations/abc")
    assert r.status_code == 422
    print(f"  status={r.status_code}")
    print("  PASS")


run_drill_92()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: GET /substations returns all
#   status=200, count=3
#   PASS
# Test 2: GET /substations?online=true returns 2
#   status=200, count=2
#   PASS
# Test 3: GET /substations?online=false returns 1
#   status=200, body=[{'id': 2, 'name': 'Beta', 'online': False}]
#   PASS
# Test 4: GET /substations/2 returns Beta
#   status=200, body={'id': 2, 'name': 'Beta', 'online': False}
#   PASS
# Test 5: GET /substations/99 returns not found
#   status=200, body={'error': 'not found'}
#   PASS
# Test 6: GET /substations/abc returns 422
#   status=422
#   PASS
