import asyncio  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import FastAPI  # noqa: F401
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — response_model=  (Drill 94)
#
# Pure Python:
#   # D69 — response model validation
#   result = handler(...)
#   validated = ResponseModel(**result)   # manual output validation
#   return validated.model_dump()
#
# FastAPI:
#   class ArtifactOut(BaseModel):
#       id: int
#       title: str
#
#   @app.get("/artifacts/{id}", response_model=ArtifactOut)
#   def get_artifact(id: int):
#       return {"id": 1, "title": "Vase", "secret_note": "fragile"}
#   # FastAPI strips "secret_note" — only ArtifactOut fields are returned
#
# What it solves: automatically validates and filters the return value.
#   Extra keys are stripped. Missing required fields → 500 at runtime.
#   The client always gets exactly the shape you declared.
# Rule: the function can return a dict, a model instance, or an ORM
#   object — FastAPI coerces it through response_model before sending.
# ─────────────────────────────────────────────


def run_drill_94():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Museum artifact registry.  The internal store keeps sensitive curator
    notes alongside each artifact, but the public API must never expose
    those notes — only the safe fields should appear in responses.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. ArtifactIn  — Pydantic BaseModel (used for request body)
       • title: str       — display name of the artifact being registered.
       • era: str         — historical period the artifact originates from.
       • curator_notes: str — internal staff notes, must never appear in
         any API response.

    2. ArtifactOut  — Pydantic BaseModel (used as response_model)
       • id: int   — unique assigned identifier for the artifact.
       • title: str — display name of the artifact.
       • era: str   — historical period of the artifact.
       (No curator_notes field — this is how sensitive data is stripped.)

    3. REGISTRY: list[dict]  — in-memory store, starts empty.
       Each entry is ArtifactIn.model_dump() plus {"id": <assigned>}.
       Define before app.

    4. POST /artifacts
       • artifact: ArtifactIn — the artifact details from the request body.
       • response_model=ArtifactOut — strips curator_notes from response.
       • Assigns id as len(REGISTRY) + 1.
       • Appends the full dict (including curator_notes) to REGISTRY.
       • Returns the full dict — FastAPI will strip curator_notes via
         response_model.

    5. GET /artifacts/{artifact_id}
       • artifact_id: int — the id of the artifact to retrieve.
       • response_model=ArtifactOut — strips curator_notes from response.
       • Returns the matching dict from REGISTRY.
       • If not found, returns {"error": "not found"} with status 200.
         (No response_model needed on the not-found branch — return early
         without response_model stripping; use a plain dict return.)

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    class ArtifactIn(BaseModel):
        title: str
        era: str
        curator_notes: str

    class ArtifactOut(BaseModel):
        id: int
        title: str
        era: str

    REGISTRY: list[dict] = []

    app = FastAPI()

    @app.post("/artifacts", response_model=ArtifactOut)
    def create_artifact(body: ArtifactIn):
        id = len(REGISTRY) + 1
        artifact = {**body.model_dump(), "id": id}
        REGISTRY.append(artifact)
        return artifact

    @app.get("/artifacts/{artifact_id}", response_model=ArtifactOut)
    def get_artifact(artifact_id: int):
        artifact = next((a for a in REGISTRY if a["id"] == artifact_id), None)
        if artifact is None:
            return JSONResponse(content={"error": "not found"})
        return artifact

    # ── TESTS ──────────────────────────────────────────────────────────
    client = TestClient(app)  # noqa: F821

    # Test 1: POST /artifacts returns ArtifactOut shape (no curator_notes)
    print("Test 1: POST /artifacts strips curator_notes")
    r = client.post(
        "/artifacts",
        json={
            "title": "Roman Vase",
            "era": "1st century AD",
            "curator_notes": "Handle with gloves",
        },
    )
    assert r.status_code == 200
    assert r.json()["id"] == 1
    assert r.json()["title"] == "Roman Vase"
    assert r.json()["era"] == "1st century AD"
    assert "curator_notes" not in r.json()
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 2: curator_notes IS stored internally
    print("Test 2: curator_notes stored in REGISTRY internally")
    assert REGISTRY[0]["curator_notes"] == "Handle with gloves"  # noqa: F821
    print(f"  internal curator_notes={REGISTRY[0]['curator_notes']}")  # noqa: F821
    print("  PASS")

    # Test 3: POST second artifact
    print("Test 3: POST second artifact")
    r = client.post(
        "/artifacts",
        json={
            "title": "Greek Urn",
            "era": "5th century BC",
            "curator_notes": "Cracked base",
        },
    )
    assert r.status_code == 200
    assert r.json()["id"] == 2
    assert "curator_notes" not in r.json()
    print(f"  status={r.status_code}, id={r.json()['id']}")
    print("  PASS")

    # Test 4: GET /artifacts/1 strips curator_notes
    print("Test 4: GET /artifacts/1 strips curator_notes")
    r = client.get("/artifacts/1")
    assert r.status_code == 200
    assert r.json()["title"] == "Roman Vase"
    assert "curator_notes" not in r.json()
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 5: GET /artifacts/99 returns not found
    print("Test 5: GET /artifacts/99 returns not found")
    r = client.get("/artifacts/99")
    assert r.status_code == 200
    assert r.json() == {"error": "not found"}
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")


run_drill_94()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: POST /artifacts strips curator_notes
#   status=200, body={'id': 1, 'title': 'Roman Vase', 'era': '1st century AD'}
#   PASS
# Test 2: curator_notes stored in REGISTRY internally
#   internal curator_notes=Handle with gloves
#   PASS
# Test 3: POST second artifact
#   status=200, id=2
#   PASS
# Test 4: GET /artifacts/1 strips curator_notes
#   status=200, body={'id': 1, 'title': 'Roman Vase', 'era': '1st century AD'}
#   PASS
# Test 5: GET /artifacts/99 returns not found
#   status=200, body={'error': 'not found'}
#   PASS
