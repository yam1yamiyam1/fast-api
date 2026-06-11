import asyncio  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — BackgroundTasks  (Drill 98)
#
# Pure Python:
#   # D78 — fire and forget with asyncio.create_task
#   asyncio.create_task(send_notification(app_id))
#
# FastAPI:
#   from fastapi import BackgroundTasks
#
#   def send_notification(app_id: int):   # plain function, not async
#       ...
#
#   @app.post("/apply")
#   def apply(bg: BackgroundTasks):
#       bg.add_task(send_notification, app_id)
#       return {"status": "received"}
#
# What it solves: same fire-and-forget pattern as asyncio.create_task,
#   but FastAPI manages it — the response is sent first, then the task
#   runs after. No event loop management needed.
# Rule: inject BackgroundTasks as a parameter, call bg.add_task(fn, *args).
#   The task runs after the response is returned to the client.
# ─────────────────────────────────────────────


def run_drill_98():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    City Hall permit office. Citizens submit permit applications and
    receive an immediate acknowledgement. After the response is sent,
    a background task logs the application to an audit trail.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. ApplicationIn — Pydantic BaseModel
       • applicant: str — full name of the citizen submitting the permit.
       • permit_type: str — category of permit being requested
         (e.g. "construction", "event").

    2. APPLICATIONS: list[dict] — in-memory store, starts empty.
       Holds submitted application dicts with an added "app_id" key.
       Define before app.

    3. AUDIT_LOG: list[str] — in-memory list, starts empty.
       Holds audit message strings written by the background task.
       Define before app.

    4. log_audit(app_id: int, applicant: str) -> None
       — plain (non-async) background task function (not a route)
       • app_id: int — the assigned ID of the application being logged,
         passed in when the task is scheduled.
       • applicant: str — name of the citizen, passed in when scheduled.
       • Appends exactly this string to AUDIT_LOG:
         f"app {app_id} submitted by {applicant}"

    5. POST /applications
       • body: ApplicationIn — application details from request body.
       • bg: BackgroundTasks — injected by FastAPI for scheduling tasks.
       • Assigns app_id as len(APPLICATIONS) + 1.
       • Builds the application dict from body.model_dump() plus
         {"app_id": app_id} and appends it to APPLICATIONS.
       • Schedules log_audit(app_id, body.applicant) as a background task.
       • Returns {"status": "received", "app_id": app_id} immediately.

    6. GET /audit
       • No parameters.
       • Returns the full AUDIT_LOG list.

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    class ApplicationIn(BaseModel):
        applicant: str
        permit_type: str

    APPLICATIONS: list[dict] = []
    AUDIT_LOG: list[str] = []

    def log_audit(app_id: int, applicant: str):
        AUDIT_LOG.append(f"app {app_id} submitted by {applicant}")

    app = FastAPI()

    @app.post("/applications")
    def create_application(body: ApplicationIn, bg: BackgroundTasks):
        app_id = len(APPLICATIONS) + 1
        application = {**body.model_dump(), "app_id": app_id}
        APPLICATIONS.append(application)
        bg.add_task(log_audit, app_id, body.applicant)
        return {"status": "received", "app_id": app_id}

    @app.get("/audit")
    def get_audit():
        return AUDIT_LOG

    # ── TESTS ──────────────────────────────────────────────────────────
    client = TestClient(app)  # noqa: F821

    # Test 1: POST /applications returns immediate acknowledgement
    print("Test 1: POST /applications returns received")
    r = client.post(
        "/applications",
        json={"applicant": "Maria Santos", "permit_type": "construction"},
    )
    assert r.status_code == 200
    assert r.json() == {"status": "received", "app_id": 1}
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 2: AUDIT_LOG has the entry after the request completes
    print("Test 2: AUDIT_LOG has entry for app 1")
    assert len(AUDIT_LOG) == 1  # noqa: F821
    assert AUDIT_LOG[0] == "app 1 submitted by Maria Santos"  # noqa: F821
    print(f"  audit={AUDIT_LOG}")  # noqa: F821
    print("  PASS")

    # Test 3: POST second application
    print("Test 3: POST second application")
    r = client.post(
        "/applications", json={"applicant": "Jose Reyes", "permit_type": "event"}
    )
    assert r.status_code == 200
    assert r.json() == {"status": "received", "app_id": 2}
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 4: GET /audit returns both log entries
    print("Test 4: GET /audit returns 2 entries")
    r = client.get("/audit")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0] == "app 1 submitted by Maria Santos"
    assert r.json()[1] == "app 2 submitted by Jose Reyes"
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 5: APPLICATIONS store has both records with correct fields
    print("Test 5: APPLICATIONS store has 2 records")
    assert len(APPLICATIONS) == 2  # noqa: F821
    assert APPLICATIONS[0]["app_id"] == 1  # noqa: F821
    assert APPLICATIONS[1]["permit_type"] == "event"  # noqa: F821
    print(f"  count={len(APPLICATIONS)}, first={APPLICATIONS[0]}")  # noqa: F821
    print("  PASS")


run_drill_98()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: POST /applications returns received
#   status=200, body={'status': 'received', 'app_id': 1}
#   PASS
# Test 2: AUDIT_LOG has entry for app 1
#   audit=['app 1 submitted by Maria Santos']
#   PASS
# Test 3: POST second application
#   status=200, body={'status': 'received', 'app_id': 2}
#   PASS
# Test 4: GET /audit returns 2 entries
#   status=200, body=['app 1 submitted by Maria Santos', 'app 2 submitted by Jose Reyes']
#   PASS
# Test 5: APPLICATIONS store has 2 records
#   count=2, first={'applicant': 'Maria Santos', 'permit_type': 'construction', 'app_id': 1}
#   PASS
