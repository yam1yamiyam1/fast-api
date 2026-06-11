import asyncio  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import FastAPI  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — Request body with Pydantic model  (Drill 93)
#
# Pure Python:
#   def handler(body: dict):
#       entry = IncidentReport(**body)   # manual validation
#       ...
#
# FastAPI:
#   class IncidentReport(BaseModel):
#       title: str
#       severity: int
#
#   @app.post("/incidents")
#   def create(report: IncidentReport):   # FastAPI parses + validates
#       ...
#
# What it solves: no more manual Model(**body) call.  FastAPI reads the
#   Content-Type, deserializes the JSON, and validates against the model
#   before your function runs.  Invalid body → 422 automatically.
# Rule: annotate the parameter with the Pydantic model class — FastAPI
#   treats any BaseModel parameter as the request body.
# ─────────────────────────────────────────────


def run_drill_93():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Police station incident desk.  Officers file new incident reports and
    retrieve them by case number.  Each report must pass validation before
    it is accepted into the log.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. IncidentReport  — Pydantic BaseModel
       • title: str — short description of the incident being reported,
         must be at least 3 characters long (min_length=3).
       • severity: int — urgency level of the incident on a 1–5 scale
         (ge=1, le=5).
       • location: str — street address or area where the incident occurred.

    2. CASE_LOG: list[dict]  — in-memory store, starts empty, holds
       filed reports as dicts with an added "case_number" key.
       Define before app.

    3. GET /incidents/{case_number}
       • case_number: int — the assigned number of the case to retrieve,
         extracted from the URL path.
       • Returns the matching dict from CASE_LOG.
       • If no case with that number exists, returns {"error": "not found"}.

    4. POST /incidents
       • report: IncidentReport — the incident details submitted by the
         officer, parsed and validated from the JSON request body.
       • Assigns case_number as len(CASE_LOG) + 1 before appending.
       • Appends report.model_dump() plus {"case_number": <assigned>}
         to CASE_LOG.
       • Returns the full dict that was appended.

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    class IncidentReport(BaseModel):
        title: str = Field(min_length=3)
        severity: int = Field(ge=1, le=5)
        location: str

    CASE_LOG: list[dict] = []

    app = FastAPI()

    @app.get("/incidents/{case_number}")
    def get_case(case_number: int):

        return next(
            (c for c in CASE_LOG if c["case_number"] == case_number),
            {"error": "not found"},
        )

    @app.post("/incidents")
    def create_case(report: IncidentReport):
        case_number = len(CASE_LOG) + 1
        case = {**report.model_dump(), "case_number": case_number}
        CASE_LOG.append(case)
        return case

    # ── TESTS ──────────────────────────────────────────────────────────
    client = TestClient(app)  # noqa: F821

    # Test 1: POST /incidents files a valid report
    print("Test 1: POST /incidents files a valid report")
    r = client.post(
        "/incidents",
        json={"title": "Burglary", "severity": 3, "location": "12 Oak Street"},
    )
    assert r.status_code == 200
    assert r.json()["case_number"] == 1
    assert r.json()["title"] == "Burglary"
    assert r.json()["severity"] == 3
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 2: POST /incidents files a second report
    print("Test 2: POST /incidents files second report")
    r = client.post(
        "/incidents",
        json={"title": "Vandalism", "severity": 1, "location": "Central Park"},
    )
    assert r.status_code == 200
    assert r.json()["case_number"] == 2
    print(f"  status={r.status_code}, case_number={r.json()['case_number']}")
    print("  PASS")

    # Test 3: GET /incidents/1 returns the first report
    print("Test 3: GET /incidents/1 returns first report")
    r = client.get("/incidents/1")
    assert r.status_code == 200
    assert r.json()["title"] == "Burglary"
    assert r.json()["case_number"] == 1
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 4: GET /incidents/99 returns not found
    print("Test 4: GET /incidents/99 returns not found")
    r = client.get("/incidents/99")
    assert r.status_code == 200
    assert r.json() == {"error": "not found"}
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 5: POST /incidents with severity=9 returns 422
    print("Test 5: POST /incidents with severity=9 returns 422")
    r = client.post(
        "/incidents", json={"title": "Speeding", "severity": 9, "location": "Highway 1"}
    )
    assert r.status_code == 422
    print(f"  status={r.status_code}")
    print("  PASS")

    # Test 6: POST /incidents with title too short returns 422
    print("Test 6: POST /incidents with title 'AB' returns 422")
    r = client.post(
        "/incidents", json={"title": "AB", "severity": 2, "location": "Downtown"}
    )
    assert r.status_code == 422
    print(f"  status={r.status_code}")
    print("  PASS")


run_drill_93()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: POST /incidents files a valid report
#   status=200, body={'title': 'Burglary', 'severity': 3, 'location': '12 Oak Street', 'case_number': 1}
#   PASS
# Test 2: POST /incidents files second report
#   status=200, case_number=2
#   PASS
# Test 3: GET /incidents/1 returns first report
#   status=200, body={'title': 'Burglary', 'severity': 3, 'location': '12 Oak Street', 'case_number': 1}
#   PASS
# Test 4: GET /incidents/99 returns not found
#   status=200, body={'error': 'not found'}
#   PASS
# Test 5: POST /incidents with severity=9 returns 422
#   status=422
#   PASS
# Test 6: POST /incidents with title 'AB' returns 422
#   status=422
#   PASS
