import asyncio  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import FastAPI, HTTPException  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — HTTPException + status codes  (Drill 95)
#
# Pure Python:
#   raise NotFoundException(404, "player not found")   # custom hierarchy
#   raise MethodNotAllowedException(405, ...)
#
# FastAPI:
#   from fastapi import HTTPException
#   raise HTTPException(status_code=404, detail="player not found")
#   raise HTTPException(status_code=403, detail="table is full")
#
# What it solves: replaces the custom AppError hierarchy from pure Python
#   drills. FastAPI catches HTTPException and converts it to the correct
#   HTTP response automatically — no global error handler needed.
# Rule: always pass status_code and detail. detail becomes the JSON body:
#   {"detail": "player not found"}
# ─────────────────────────────────────────────


def run_drill_95():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Casino floor manager. Players register at the front desk, then join
    tables. The system enforces capacity limits and rejects unknown players.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. PlayerIn — Pydantic BaseModel
       • name: str — the full name of the player checking in at the desk.
       • chips: int — the number of chips the player is buying in with,
         must be at least 1 (ge=1).

    2. PLAYERS: dict[str, dict] — in-memory store keyed by player name,
       starts empty. Define before app.

    3. TABLES: dict[str, list] — in-memory store keyed by table name,
       value is a list of player names seated at that table.
       Pre-populated before app with exactly:
         {"blackjack": [], "poker": [], "roulette": []}

    4. POST /players
       • body: PlayerIn — player details from the request body.
       • If a player with that name already exists, raise HTTPException
         status_code=409, detail="player already registered".
       • Otherwise store {name, chips} in PLAYERS and return it.

    5. GET /players/{name}
       • name: str — the player name to look up, from the URL path.
       • If the player does not exist, raise HTTPException
         status_code=404, detail="player not found".
       • Otherwise return the player dict.

    6. POST /tables/{table_name}/join
       • table_name: str — name of the table to join, from the URL path.
       • body: PlayerIn — player attempting to join, from the request body.
       • If table_name is not a key in TABLES, raise HTTPException
         status_code=404, detail="table not found".
       • If the player name is not in PLAYERS, raise HTTPException
         status_code=404, detail="player not found".
       • If the table already has 3 or more players, raise HTTPException
         status_code=403, detail="table is full".
       • Otherwise append the player name to the table's list and return
         {"table": table_name, "seated": <updated list>}.

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    class PlayerIn(BaseModel):
        name: str
        chips: int = Field(gt=0)

    PLAYERS: dict[str, dict] = {}

    TABLES: dict[str, list] = {"blackjack": [], "poker": [], "roulette": []}

    app = FastAPI()

    @app.post("/players")
    def register_player(body: PlayerIn):
        if body.name in PLAYERS:
            raise HTTPException(status_code=409, detail="player already registered")
        PLAYERS[body.name] = body.model_dump()
        return PLAYERS[body.name]

    @app.get("/players/{name}")
    def get_player(name: str):
        if name not in PLAYERS:
            raise HTTPException(status_code=404, detail="player not found")
        return PLAYERS[name]

    @app.post("/tables/{table_name}/join")
    def add_player_to_table(table_name: str, body: PlayerIn):
        if table_name not in TABLES:
            raise HTTPException(status_code=404, detail="table not found")

        if body.name not in PLAYERS:
            raise HTTPException(status_code=404, detail="player not found")
        found_table = TABLES[table_name]
        if len(found_table) >= 3:
            raise HTTPException(status_code=403, detail="table is full")
        found_table.append(body.name)
        return {"table": table_name, "seated": found_table}

    # ── TESTS ──────────────────────────────────────────────────────────
    client = TestClient(app)  # noqa: F821

    # Test 1: POST /players registers a new player
    print("Test 1: POST /players registers Alice")
    r = client.post("/players", json={"name": "Alice", "chips": 500})
    assert r.status_code == 200
    assert r.json() == {"name": "Alice", "chips": 500}
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 2: POST /players duplicate name returns 409
    print("Test 2: POST /players duplicate returns 409")
    r = client.post("/players", json={"name": "Alice", "chips": 200})
    assert r.status_code == 409
    assert r.json()["detail"] == "player already registered"
    print(f"  status={r.status_code}, detail={r.json()['detail']}")
    print("  PASS")

    # Test 3: GET /players/Alice returns her record
    print("Test 3: GET /players/Alice")
    r = client.get("/players/Alice")
    assert r.status_code == 200
    assert r.json()["chips"] == 500
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 4: GET /players/Ghost returns 404
    print("Test 4: GET /players/Ghost returns 404")
    r = client.get("/players/Ghost")
    assert r.status_code == 404
    assert r.json()["detail"] == "player not found"
    print(f"  status={r.status_code}, detail={r.json()['detail']}")
    print("  PASS")

    # Test 5: POST /tables/blackjack/join — valid join
    print("Test 5: Alice joins blackjack")
    r = client.post("/tables/blackjack/join", json={"name": "Alice", "chips": 500})
    assert r.status_code == 200
    assert r.json()["table"] == "blackjack"
    assert "Alice" in r.json()["seated"]
    print(f"  status={r.status_code}, body={r.json()}")
    print("  PASS")

    # Test 6: POST /tables/slots/join — unknown table returns 404
    print("Test 6: join unknown table returns 404")
    r = client.post("/tables/slots/join", json={"name": "Alice", "chips": 500})
    assert r.status_code == 404
    assert r.json()["detail"] == "table not found"
    print(f"  status={r.status_code}, detail={r.json()['detail']}")
    print("  PASS")

    # Test 7: table full — register 2 more players then overflow
    print("Test 7: table full returns 403")
    client.post("/players", json={"name": "Bob", "chips": 300})
    client.post("/players", json={"name": "Carol", "chips": 400})
    client.post("/players", json={"name": "Dave", "chips": 100})
    client.post("/tables/blackjack/join", json={"name": "Bob", "chips": 300})
    client.post("/tables/blackjack/join", json={"name": "Carol", "chips": 400})
    r = client.post("/tables/blackjack/join", json={"name": "Dave", "chips": 100})
    assert r.status_code == 403
    assert r.json()["detail"] == "table is full"
    print(f"  status={r.status_code}, detail={r.json()['detail']}")
    print("  PASS")


run_drill_95()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: POST /players registers Alice
#   status=200, body={'name': 'Alice', 'chips': 500}
#   PASS
# Test 2: POST /players duplicate returns 409
#   status=409, detail=player already registered
#   PASS
# Test 3: GET /players/Alice
#   status=200, body={'name': 'Alice', 'chips': 500}
#   PASS
# Test 4: GET /players/Ghost returns 404
#   status=404, detail=player not found
#   PASS
# Test 5: Alice joins blackjack
#   status=200, body={'table': 'blackjack', 'seated': ['Alice']}
#   PASS
# Test 6: join unknown table returns 404
#   status=404, detail=table not found
#   PASS
# Test 7: table full returns 403
#   status=403, detail=table is full
#   PASS
