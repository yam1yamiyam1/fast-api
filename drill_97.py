import asyncio  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — Depends() chained  (Drill 97)
#
# Pure Python:
#   # D68 — chained deps: dep2 takes dep1 result
#   async def get_vessel(vessel_id: int): ...
#   async def get_manifest(vessel=dep_result_of_get_vessel): ...
#
# FastAPI:
#   def get_vessel(vessel_id: int) -> dict:
#       ...
#       return vessel
#
#   def get_manifest(vessel: dict = Depends(get_vessel)) -> dict:
#       ...
#       return manifest
#
#   @app.get("/cargo")
#   def list_cargo(manifest: dict = Depends(get_manifest)):
#       ...
#
# What it solves: same as the pure Python chained dep pattern — each dep
#   builds on the result of the previous one. FastAPI resolves the chain
#   automatically; the endpoint only sees the final result.
# Rule: declare Depends() inside the dependent function's signature,
#   not in the endpoint. The endpoint only depends on the last link.
# ─────────────────────────────────────────────


def run_drill_97():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Seaport cargo control. Every request targets a vessel by ID. A
    vessel lookup dependency validates the vessel exists. A manifest
    dependency builds on that — it takes the resolved vessel and returns
    its cargo manifest. The endpoint only receives the final manifest.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. VESSELS: dict[int, dict] — in-memory store defined before app,
       pre-populated with exactly:
         {
           1: {"id": 1, "name": "Ever Given",  "manifest_id": 101},
           2: {"id": 2, "name": "Maersk Alpha", "manifest_id": 102},
         }

    2. MANIFESTS: dict[int, dict] — in-memory store defined before app,
       pre-populated with exactly:
         {
           101: {"manifest_id": 101, "cargo": ["steel", "timber"]},
           102: {"manifest_id": 102, "cargo": ["electronics", "grain"]},
         }

    3. get_vessel(vessel_id: int) -> dict  — first dependency (not a route)
       • vessel_id: int — numeric vessel identifier supplied as a query
         parameter by the caller.
       • If vessel_id is not in VESSELS, raise HTTPException
         status_code=404, detail="vessel not found".
       • Returns the vessel dict.

    4. get_manifest(vessel: dict = Depends(get_vessel)) -> dict
       — second dependency, chained on get_vessel (not a route)
       • vessel: dict — the resolved vessel dict injected by FastAPI
         from the get_vessel dependency.
       • Looks up vessel["manifest_id"] in MANIFESTS.
       • If not found, raise HTTPException
         status_code=404, detail="manifest not found".
       • Returns the manifest dict.

    5. GET /cargo
       • manifest: dict = Depends(get_manifest) — the fully resolved
         manifest injected by FastAPI through the chain.
       • Returns the manifest dict.

    6. POST /cargo/item
       • item: str — a query parameter representing the cargo item name
         to add to the manifest.
       • manifest: dict = Depends(get_manifest) — resolved manifest.
       • Appends item to manifest["cargo"] in place (the MANIFESTS store
         is mutated directly).
       • Returns the updated manifest dict.

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    VESSELS: dict[int, dict] = {
        1: {"id": 1, "name": "Ever Given", "manifest_id": 101},
        2: {"id": 2, "name": "Maersk Alpha", "manifest_id": 102},
    }
    MANIFESTS: dict[int, dict] = {
        101: {"manifest_id": 101, "cargo": ["steel", "timber"]},
        102: {"manifest_id": 102, "cargo": ["electronics", "grain"]},
    }

    def get_vessel(vessel_id: int):
        if vessel_id not in VESSELS:
            raise HTTPException(status_code=404, detail="vessel not found")
        return VESSELS[vessel_id]

    def get_manifest(vessel: dict = Depends(get_vessel)):
        manifest = MANIFESTS[vessel["manifest_id"]]
        if not manifest:
            raise HTTPException(status_code=404, detail="manifest not found")
        return manifest

    app = FastAPI()

    @app.get("/cargo")
    def get_cargo(manifest: dict = Depends(get_manifest)):
        return manifest

    @app.post("/cargo/item")
    def add_cargo(item: str, manifest: dict = Depends(get_manifest)):
        manifest["cargo"].append(item)
        return manifest

    # ── TESTS ──────────────────────────────────────────────────────────
    client = TestClient(app)  # noqa: F821

    # Test 1: GET /cargo?vessel_id=1 returns manifest for Ever Given
    print("Test 1: GET /cargo?vessel_id=1 returns manifest 101")
    r = client.get("/cargo?vessel_id=1")
    assert r.status_code == 200
    assert r.json()["manifest_id"] == 101
    assert "steel" in r.json()["cargo"]
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 2: GET /cargo?vessel_id=2 returns manifest for Maersk Alpha
    print("Test 2: GET /cargo?vessel_id=2 returns manifest 102")
    r = client.get("/cargo?vessel_id=2")
    assert r.status_code == 200
    assert r.json()["manifest_id"] == 102
    assert "electronics" in r.json()["cargo"]
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 3: GET /cargo?vessel_id=99 returns 404 from get_vessel
    print("Test 3: GET /cargo?vessel_id=99 returns 404")
    r = client.get("/cargo?vessel_id=99")
    assert r.status_code == 404
    assert r.json()["detail"] == "vessel not found"
    print(f"  status={r.status_code}, detail={r.json()['detail']}")
    print("  PASS")

    # Test 4: POST /cargo/item?vessel_id=1&item=rubber adds item
    print("Test 4: POST /cargo/item?vessel_id=1&item=rubber adds rubber")
    r = client.post("/cargo/item?vessel_id=1&item=rubber")
    assert r.status_code == 200
    assert "rubber" in r.json()["cargo"]
    print(f"  status={r.status_code}, cargo={r.json()['cargo']}")
    print("  PASS")

    # Test 5: GET /cargo?vessel_id=1 now includes rubber
    print("Test 5: GET /cargo?vessel_id=1 now includes rubber")
    r = client.get("/cargo?vessel_id=1")
    assert r.status_code == 200
    assert "rubber" in r.json()["cargo"]
    print(f"  status={r.status_code}, cargo={r.json()['cargo']}")
    print("  PASS")

    # Test 6: POST /cargo/item?vessel_id=99&item=coal returns 404
    print("Test 6: POST /cargo/item?vessel_id=99 returns 404")
    r = client.post("/cargo/item?vessel_id=99&item=coal")
    assert r.status_code == 404
    assert r.json()["detail"] == "vessel not found"
    print(f"  status={r.status_code}, detail={r.json()['detail']}")
    print("  PASS")


run_drill_97()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: GET /cargo?vessel_id=1 returns manifest 101
#   status=200, body={'manifest_id': 101, 'cargo': ['steel', 'timber']}
#   PASS
# Test 2: GET /cargo?vessel_id=2 returns manifest 102
#   status=200, body={'manifest_id': 102, 'cargo': ['electronics', 'grain']}
#   PASS
# Test 3: GET /cargo?vessel_id=99 returns 404
#   status=404, detail=vessel not found
#   PASS
# Test 4: POST /cargo/item?vessel_id=1&item=rubber adds rubber
#   status=200, cargo=['steel', 'timber', 'rubber']
#   PASS
# Test 5: GET /cargo?vessel_id=1 now includes rubber
#   status=200, cargo=['steel', 'timber', 'rubber']
#   PASS
# Test 6: POST /cargo/item?vessel_id=99 returns 404
#   status=404, detail=vessel not found
#   PASS
