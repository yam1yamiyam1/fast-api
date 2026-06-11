import asyncio  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — Depends()  (Drill 96)
#
# Pure Python:
#   deps = {"current_zone": get_current_zone}
#   resolved = await deps["current_zone"](token)
#   result = await handler(resolved)
#
# FastAPI:
#   def get_current_zone(zone_id: int) -> str:
#       ...
#       return zone_name
#
#   @app.get("/tanks")
#   def list_tanks(zone: str = Depends(get_current_zone)):
#       ...
#
# What it solves: replaces the manual deps dict + resolution loop.
#   FastAPI calls get_current_zone automatically, passing its own
#   parameters from the request, and injects the return value as `zone`.
# Rule: the dependency function is a plain function — its parameters are
#   resolved from the request just like an endpoint's parameters.
# ─────────────────────────────────────────────


def run_drill_96():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Aquarium zone control. The facility is divided into numbered zones.
    Every request must supply a zone_id query parameter; a shared
    dependency validates it and resolves it to a zone name before the
    endpoint runs.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. ZONES: dict[int, str] — in-memory lookup defined before app,
       pre-populated with exactly:
         {1: "Tropical", 2: "Arctic", 3: "Deep Sea"}

    2. TANKS: list[dict] — in-memory store, starts empty, holds tank
       records. Define before app.

    3. get_zone(zone_id: int) -> str  — dependency function (not a route)
       • zone_id: int — numeric zone identifier supplied as a query
         parameter by the caller.
       • If zone_id is not a key in ZONES, raise HTTPException
         status_code=404, detail="zone not found".
       • Returns the zone name string for that id.

    4. TankIn — Pydantic BaseModel
       • species: str — the species name of the animal in the tank.
       • capacity: int — maximum number of animals the tank can hold,
         must be at least 1 (ge=1).

    5. GET /tanks
       • zone: str = Depends(get_zone) — resolved zone name injected by
         FastAPI; zone_id is read from the query string automatically.
       • Returns all tanks in TANKS whose "zone" value matches zone.

    6. POST /tanks
       • body: TankIn — tank details from the request body.
       • zone: str = Depends(get_zone) — resolved zone name injected by
         FastAPI.
       • Builds a dict from body.model_dump() plus {"zone": zone}.
       • Appends it to TANKS and returns it.

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    ZONES: dict[int, str] = {1: "Tropical", 2: "Arctic", 3: "Deep Sea"}
    TANKS: list[dict] = []

    def get_zone(zone_id: int):
        if zone_id not in ZONES:
            raise HTTPException(status_code=404, detail="zone not found")
        return ZONES[zone_id]

    class TankIn(BaseModel):
        species: str
        capacity: int = Field(ge=1)

    app = FastAPI()

    @app.get("/tanks")
    def get_tanks(zone: str = Depends(get_zone)):
        return [t for t in TANKS if t["zone"] == zone]

    @app.post("/tanks")
    def add_tank(body: TankIn, zone: str = Depends(get_zone)):
        tank = {**body.model_dump(), "zone": zone}
        TANKS.append(tank)
        return tank

    # ── TESTS ──────────────────────────────────────────────────────────
    client = TestClient(app)  # noqa: F821

    # Test 1: POST /tanks?zone_id=1 adds a tank to Tropical
    print("Test 1: POST /tanks?zone_id=1 adds Clownfish tank")
    r = client.post("/tanks?zone_id=1", json={"species": "Clownfish", "capacity": 20})
    assert r.status_code == 200
    assert r.json()["zone"] == "Tropical"
    assert r.json()["species"] == "Clownfish"
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 2: POST /tanks?zone_id=2 adds a tank to Arctic
    print("Test 2: POST /tanks?zone_id=2 adds Penguin tank")
    r = client.post("/tanks?zone_id=2", json={"species": "Penguin", "capacity": 5})
    assert r.status_code == 200
    assert r.json()["zone"] == "Arctic"
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 3: GET /tanks?zone_id=1 returns only Tropical tanks
    print("Test 3: GET /tanks?zone_id=1 returns Tropical tanks")
    r = client.get("/tanks?zone_id=1")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["zone"] == "Tropical"
    print(
        f"  status={r.status_code}, count={len(r.json())}, zone={r.json()[0]['zone']}"
    )
    print("  PASS")

    # Test 4: GET /tanks?zone_id=3 returns empty list (no tanks added yet)
    print("Test 4: GET /tanks?zone_id=3 returns empty list")
    r = client.get("/tanks?zone_id=3")
    assert r.status_code == 200
    assert r.json() == []
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 5: GET /tanks?zone_id=99 returns 404 from dependency
    print("Test 5: GET /tanks?zone_id=99 returns 404")
    r = client.get("/tanks?zone_id=99")
    assert r.status_code == 404
    assert r.json()["detail"] == "zone not found"
    print(f"  status={r.status_code}, detail={r.json()['detail']}")
    print("  PASS")

    # Test 6: POST /tanks?zone_id=99 returns 404 from dependency
    print("Test 6: POST /tanks?zone_id=99 returns 404")
    r = client.post("/tanks?zone_id=99", json={"species": "Shark", "capacity": 1})
    assert r.status_code == 404
    assert r.json()["detail"] == "zone not found"
    print(f"  status={r.status_code}, detail={r.json()['detail']}")
    print("  PASS")


run_drill_96()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: POST /tanks?zone_id=1 adds Clownfish tank
#   status=200, body={'species': 'Clownfish', 'capacity': 20, 'zone': 'Tropical'}
#   PASS
# Test 2: POST /tanks?zone_id=2 adds Penguin tank
#   status=200, body={'species': 'Penguin', 'capacity': 5, 'zone': 'Arctic'}
#   PASS
# Test 3: GET /tanks?zone_id=1 returns Tropical tanks
#   status=200, count=1, zone=Tropical
#   PASS
# Test 4: GET /tanks?zone_id=3 returns empty list
#   status=200, body=[]
#   PASS
# Test 5: GET /tanks?zone_id=99 returns 404
#   status=404, detail=zone not found
#   PASS
# Test 6: POST /tanks?zone_id=99 returns 404
#   status=404, detail=zone not found
#   PASS
