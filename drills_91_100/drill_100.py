import asyncio  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException  # noqa: F401
from fastapi.responses import JSONResponse  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# COMBO DRILL — All Phase 2 intro concepts  (Drill 100)
#
# Concepts in play:
#   - @app.get / @app.post          (D91)
#   - path params + query params    (D92)
#   - request body with Pydantic    (D93)
#   - response_model=               (D94)
#   - HTTPException + status codes  (D95)
#   - Depends() single              (D96)
#   - Depends() chained             (D97)
#   - BackgroundTasks               (D98)
#   - lifespan                      (D99)
#
# No new concept. Everything wires together.
# ─────────────────────────────────────────────


def run_drill_100():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Customs office border control. Officers register shipments, inspect
    them by country of origin, and flag suspicious ones. Every request
    requires a valid officer_id. Flagged shipments are audit-logged in
    the background. The office loads allowed countries on startup and
    clears state on shutdown.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. APP_STATE: dict — starts empty. Define before lifespan and app.

    2. SHIPMENTS: list[dict] — starts empty. Define before lifespan and app.

    3. AUDIT_LOG: list[str] — starts empty. Define before lifespan and app.

    4. lifespan(app: FastAPI) — asynccontextmanager
       Startup: sets APP_STATE["allowed_countries"] to exactly:
         ["Philippines", "Japan", "Germany", "Brazil"]
       Shutdown (finally): calls APP_STATE.clear().

    5. ShipmentIn — Pydantic BaseModel (request body)
       • origin: str — country the shipment is coming from.
       • contents: str — description of what is in the shipment.
       • weight_kg: float — total weight in kilograms, must be > 0 (gt=0).

    6. ShipmentOut — Pydantic BaseModel (response_model)
       • id: int — assigned shipment identifier.
       • origin: str — country of origin.
       • contents: str — contents description.
       • weight_kg: float — weight in kilograms.
       • flagged: bool — whether the shipment has been flagged.
       (No officer_notes field — internal only, stripped by response_model.)

    7. get_officer(officer_id: int) -> dict — first dependency (not a route)
       • officer_id: int — numeric officer ID supplied as a query parameter.
       • Looks up officer_id in APP_STATE["officers"].
       • If not found, raise HTTPException 403, detail="unauthorized officer".
       • Returns the officer dict.

    8. get_clearance(officer: dict = Depends(get_officer)) -> str
       — second dependency, chained on get_officer (not a route)
       • officer: dict — resolved officer dict from get_officer.
       • If officer["clearance"] != "senior", raise HTTPException
         403, detail="senior clearance required".
       • Returns officer["clearance"].

    9. flag_audit(shipment_id: int, officer_id: int) -> None
       — plain background task function (not a route)
       • Appends exactly this string to AUDIT_LOG:
         f"shipment {shipment_id} flagged by officer {officer_id}"

    10. POST /setup
        • No Pydantic body. No dependencies.
        • Populates APP_STATE["officers"] with exactly:
            {
              1: {"id": 1, "name": "Cruz",  "clearance": "senior"},
              2: {"id": 2, "name": "Reyes", "clearance": "junior"},
            }
        • Returns {"status": "officers loaded"}.

    11. POST /shipments
        • body: ShipmentIn — shipment details from request body.
        • officer: dict = Depends(get_officer) — any valid officer may
          submit a shipment (no clearance check here).
        • response_model=ShipmentOut
        • Assigns id as len(SHIPMENTS) + 1.
        • Builds the full dict from body.model_dump() plus:
            {"id": id, "flagged": False,
             "officer_notes": f"submitted by {officer['name']}"}
        • Appends to SHIPMENTS and returns the full dict
          (response_model strips officer_notes).

    12. GET /shipments
        • origin: Optional[str] = None — query param to filter by country.
        • officer: dict = Depends(get_officer) — any valid officer.
        • response_model=list[ShipmentOut]
        • Returns all shipments if origin is None, else only those whose
          "origin" matches origin.

    13. POST /shipments/{shipment_id}/flag
        • shipment_id: int — path param, the ID of the shipment to flag.
        • bg: BackgroundTasks — for scheduling the audit log.
        • _clearance: str = Depends(get_clearance) — chained dep; only
          senior officers may flag. Assigned to _clearance (unused directly).
        • officer: dict = Depends(get_officer) — needed for audit log.
        • If no shipment with that id exists, raise HTTPException
          404, detail="shipment not found".
        • Sets shipment["flagged"] = True in place.
        • Schedules flag_audit(shipment_id, officer["id"]) as background task.
        • Returns the updated shipment dict (no response_model needed here).

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    APP_STATE: dict = {}
    SHIPMENTS: list[dict] = []
    AUDIT_LOG: list[str] = []

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        APP_STATE["allowed_countries"] = ["Philippines", "Japan", "Germany", "Brazil"]
        try:
            yield
        finally:
            APP_STATE.clear()

    class ShipmentIn(BaseModel):
        origin: str
        contents: str
        weight_kg: float = Field(gt=0)

    class ShipmentOut(BaseModel):
        id: int
        origin: str
        contents: str
        weight_kg: float
        flagged: bool

    app = FastAPI(lifespan=lifespan)

    def get_officer(officer_id: int):
        officer = APP_STATE["officers"].get(officer_id)
        if not officer:
            raise HTTPException(status_code=403, detail="unauthorized officer")
        return officer

    def get_clearance(officer: dict = Depends(get_officer)):
        if officer["clearance"] != "senior":
            raise HTTPException(status_code=403, detail="senior clearance required")
        return officer["clearance"]

    def flag_audit(shipment_id: int, officer_id: int):
        AUDIT_LOG.append(f"shipment {shipment_id} flagged by officer {officer_id}")

    @app.post("/setup")
    def setup():
        APP_STATE["officers"] = {
            1: {"id": 1, "name": "Cruz", "clearance": "senior"},
            2: {"id": 2, "name": "Reyes", "clearance": "junior"},
        }
        return {"status": "officers loaded"}

    @app.post("/shipments", response_model=ShipmentOut)
    def add_shipment(body: ShipmentIn, officer: dict = Depends(get_officer)):
        shipment_id = len(SHIPMENTS) + 1
        shipment = {
            **body.model_dump(),
            "id": shipment_id,
            "flagged": False,
            "officer_notes": f"submitted by {officer['name']}",
        }
        SHIPMENTS.append(shipment)
        return shipment

    @app.get("/shipments", response_model=list[ShipmentOut])
    def get_shipments(
        origin: Optional[str] = None, officer: dict = Depends(get_officer)
    ):
        if origin is None:
            return SHIPMENTS
        return [s for s in SHIPMENTS if s["origin"] == origin]

    @app.post("/shipments/{shipment_id}/flag")
    def flag_shipment(
        shipment_id: int,
        bg: BackgroundTasks,
        _clearance: str = Depends(get_clearance),
        officer: dict = Depends(get_officer),
    ):
        shipment = next((s for s in SHIPMENTS if s["id"] == shipment_id), None)
        if shipment is None:
            raise HTTPException(status_code=404, detail="shipment not found")
        shipment["flagged"] = True
        bg.add_task(flag_audit, shipment_id, officer["id"])
        return shipment

    # ── TESTS ──────────────────────────────────────────────────────────
    with TestClient(app) as client:  # noqa: F821
        # Test 1: lifespan loaded allowed_countries
        print("Test 1: startup loaded allowed_countries")
        assert APP_STATE["allowed_countries"] == [
            "Philippines",
            "Japan",
            "Germany",
            "Brazil",
        ]  # noqa: F821
        print(f"  countries={APP_STATE['allowed_countries']}")  # noqa: F821
        print("  PASS")

        # Test 2: POST /setup loads officers
        print("Test 2: POST /setup loads officers")
        r = client.post("/setup")
        assert r.status_code == 200
        assert r.json() == {"status": "officers loaded"}
        print(f"  status={r.status_code}, body={r.json()}")
        print("  PASS")

        # Test 3: POST /shipments with valid officer
        print("Test 3: POST /shipments officer_id=1 submits shipment")
        r = client.post(
            "/shipments?officer_id=1",
            json={"origin": "Japan", "contents": "electronics", "weight_kg": 120.5},
        )
        assert r.status_code == 200
        assert r.json()["id"] == 1
        assert r.json()["flagged"] is False
        assert "officer_notes" not in r.json()
        print(f"  status={r.status_code}, body={r.json()}")
        print("  PASS")

        # Test 4: POST /shipments with invalid officer returns 403
        print("Test 4: POST /shipments officer_id=99 returns 403")
        r = client.post(
            "/shipments?officer_id=99",
            json={"origin": "Brazil", "contents": "coffee", "weight_kg": 50.0},
        )
        assert r.status_code == 403
        assert r.json()["detail"] == "unauthorized officer"
        print(f"  status={r.status_code}, detail={r.json()['detail']}")
        print("  PASS")

        # Test 5: POST second shipment with junior officer
        print("Test 5: POST /shipments officer_id=2 submits shipment")
        r = client.post(
            "/shipments?officer_id=2",
            json={"origin": "Germany", "contents": "machinery", "weight_kg": 500.0},
        )
        assert r.status_code == 200
        assert r.json()["id"] == 2
        print(f"  status={r.status_code}, id={r.json()['id']}")
        print("  PASS")

        # Test 6: GET /shipments?officer_id=1 returns all
        print("Test 6: GET /shipments returns all 2 shipments")
        r = client.get("/shipments?officer_id=1")
        assert r.status_code == 200
        assert len(r.json()) == 2
        print(f"  status={r.status_code}, count={len(r.json())}")
        print("  PASS")

        # Test 7: GET /shipments?officer_id=1&origin=Japan filters correctly
        print("Test 7: GET /shipments?origin=Japan returns 1")
        r = client.get("/shipments?officer_id=1&origin=Japan")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["origin"] == "Japan"
        print(f"  status={r.status_code}, count={len(r.json())}")
        print("  PASS")

        # Test 8: POST /shipments/1/flag with senior officer flags it
        print("Test 8: POST /shipments/1/flag officer_id=1 flags shipment")
        r = client.post("/shipments/1/flag?officer_id=1")
        assert r.status_code == 200
        assert r.json()["flagged"] is True
        print(f"  status={r.status_code}, flagged={r.json()['flagged']}")
        print("  PASS")

        # Test 9: AUDIT_LOG has the flag entry
        print("Test 9: AUDIT_LOG has flag entry")
        assert len(AUDIT_LOG) == 1  # noqa: F821
        assert AUDIT_LOG[0] == "shipment 1 flagged by officer 1"  # noqa: F821
        print(f"  audit={AUDIT_LOG}")  # noqa: F821
        print("  PASS")

        # Test 10: POST /shipments/1/flag with junior officer returns 403
        print("Test 10: POST /shipments/1/flag officer_id=2 returns 403")
        r = client.post("/shipments/1/flag?officer_id=2")
        assert r.status_code == 403
        assert r.json()["detail"] == "senior clearance required"
        print(f"  status={r.status_code}, detail={r.json()['detail']}")
        print("  PASS")

        # Test 11: POST /shipments/99/flag returns 404
        print("Test 11: POST /shipments/99/flag returns 404")
        r = client.post("/shipments/99/flag?officer_id=1")
        assert r.status_code == 404
        assert r.json()["detail"] == "shipment not found"
        print(f"  status={r.status_code}, detail={r.json()['detail']}")
        print("  PASS")

    # Test 12: APP_STATE cleared after shutdown
    print("Test 12: APP_STATE cleared after shutdown")
    assert APP_STATE == {}  # noqa: F821
    print(f"  APP_STATE={APP_STATE}")  # noqa: F821
    print("  PASS")


run_drill_100()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: startup loaded allowed_countries
#   countries=['Philippines', 'Japan', 'Germany', 'Brazil']
#   PASS
# Test 2: POST /setup loads officers
#   status=200, body={'status': 'officers loaded'}
#   PASS
# Test 3: POST /shipments officer_id=1 submits shipment
#   status=200, body={'id': 1, 'origin': 'Japan', 'contents': 'electronics', 'weight_kg': 120.5, 'flagged': False}
#   PASS
# Test 4: POST /shipments officer_id=99 returns 403
#   status=403, detail=unauthorized officer
#   PASS
# Test 5: POST /shipments officer_id=2 submits shipment
#   status=200, id=2
#   PASS
# Test 6: GET /shipments returns all 2 shipments
#   status=200, count=2
#   PASS
# Test 7: GET /shipments?origin=Japan returns 1
#   status=200, count=1
#   PASS
# Test 8: POST /shipments/1/flag officer_id=1 flags shipment
#   status=200, flagged=True
#   PASS
# Test 9: AUDIT_LOG has flag entry
#   audit=['shipment 1 flagged by officer 1']
#   PASS
# Test 10: POST /shipments/1/flag officer_id=2 returns 403
#   status=403, detail=senior clearance required
#   PASS
# Test 11: POST /shipments/99/flag returns 404
#   status=404, detail=shipment not found
#   PASS
# Test 12: APP_STATE cleared after shutdown
#   APP_STATE={}
#   PASS
