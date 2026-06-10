import asyncio  # noqa: F401

import httpx  # noqa: F401
from fastapi import FastAPI  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — @app.get / @app.post  (Drill 91)
#
# Pure Python:
#   ROUTES = []
#   ROUTES.append(("GET",  re.compile(r"^/items$"),     list_items))
#   ROUTES.append(("POST", re.compile(r"^/items$"),     create_item))
#   result = dispatch("GET", "/items", body=None)
#
# FastAPI:
#   app = FastAPI()
#
#   @app.get("/items")
#   def list_items(): ...
#
#   @app.post("/items")
#   def create_item(body: MyModel): ...
#
#   client = TestClient(app)
#   client.get("/items")
#   client.post("/items", json={...})
#
# What it solves: replaces the manual ROUTES list + dispatch() + regex
#   matching you built in pure Python.  FastAPI registers and dispatches
#   for you via the decorator.
# Rule: one decorator = one (method, path) pair.  GET and POST on the
#   same path need two separate decorators.
# ─────────────────────────────────────────────


def run_drill_91():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Pharmacy counter.  Staff query the current drug inventory and add new
    drug entries.  Two routes handle all traffic.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. DrugEntry  — Pydantic BaseModel
       • name: str   — the brand name of the drug being registered
       • stock: int  — number of units currently on the pharmacy shelf

    2. INVENTORY: list[dict]  — module-level list (inside run_drill_91)
       that starts empty and accumulates DrugEntry records as dicts.
       (Module-level state is allowed here because TestClient shares the
       same process; define it at the top of run_drill_91, before app.)

    3. GET /drugs
       Returns the full INVENTORY list.
       No parameters.

    4. POST /drugs
       Accepts a DrugEntry in the request body.
       Appends model_dump() of the entry to INVENTORY.
       Returns the dict that was just appended.

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    class DrugEntry(BaseModel):
        name: str
        stock: int

    INVENTORY: list[dict] = []
    app = FastAPI()

    @app.get("/drugs")
    def get_drugs():
        return INVENTORY

    @app.post("/drugs")
    def create_drug(body: DrugEntry):
        dict = body.model_dump()
        INVENTORY.append(dict)
        return dict

    # ── TESTS ──────────────────────────────────────────────────────────
    client = TestClient(app)  # noqa: F821  — app defined in your code above

    # Test 1: GET /drugs returns empty list at start
    print("Test 1: GET /drugs returns empty list")
    r = client.get("/drugs")
    assert r.status_code == 200
    assert r.json() == []
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 2: POST /drugs adds a drug and returns it
    print("Test 2: POST /drugs adds aspirin")
    r = client.post("/drugs", json={"name": "Aspirin", "stock": 200})
    assert r.status_code == 200
    assert r.json() == {"name": "Aspirin", "stock": 200}
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 3: POST /drugs adds a second drug
    print("Test 3: POST /drugs adds ibuprofen")
    r = client.post("/drugs", json={"name": "Ibuprofen", "stock": 75})
    assert r.status_code == 200
    assert r.json() == {"name": "Ibuprofen", "stock": 75}
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 4: GET /drugs now returns both entries
    print("Test 4: GET /drugs returns both entries")
    r = client.get("/drugs")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["name"] == "Aspirin"
    assert r.json()[1]["name"] == "Ibuprofen"
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 5: POST /drugs with missing field returns 422
    print("Test 5: POST /drugs with missing stock returns 422")
    r = client.post("/drugs", json={"name": "Paracetamol"})
    assert r.status_code == 422
    print(f"  status={r.status_code}")
    print("  PASS")


run_drill_91()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: GET /drugs returns empty list
#   status=200, body=[]
#   PASS
# Test 2: POST /drugs adds aspirin
#   status=200, body={'name': 'Aspirin', 'stock': 200}
#   PASS
# Test 3: POST /drugs adds ibuprofen
#   status=200, body={'name': 'Ibuprofen', 'stock': 75}
#   PASS
# Test 4: GET /drugs returns both entries
#   status=200, body=[{'name': 'Aspirin', 'stock': 200}, {'name': 'Ibuprofen', 'stock': 75}]
#   PASS
# Test 5: POST /drugs with missing stock returns 422
#   status=422
#   PASS
