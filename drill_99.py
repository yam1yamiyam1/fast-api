import asyncio  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401
from typing import Optional  # noqa: F401

import httpx  # noqa: F401
from fastapi import FastAPI, HTTPException  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401

# ─────────────────────────────────────────────
# NEW CONCEPT — lifespan  (Drill 99)
#
# Pure Python:
#   # D67 — asynccontextmanager lifespan + APP_STATE
#   @asynccontextmanager
#   async def lifespan():
#       APP_STATE["db"] = connect()   # startup
#       yield
#       APP_STATE["db"].close()       # shutdown
#
# FastAPI:
#   APP_STATE = {}
#
#   @asynccontextmanager
#   async def lifespan(app: FastAPI):
#       APP_STATE["db"] = connect()   # startup — before yield
#       yield
#       APP_STATE["db"].close()       # shutdown — after yield
#
#   app = FastAPI(lifespan=lifespan)
#
# What it solves: same pattern as the pure Python toy — one function
#   handles both startup and shutdown. FastAPI wires it in via the
#   lifespan= argument on FastAPI().
# Rule: the lifespan function must accept one argument (the app instance)
#   even if you don't use it.
# ─────────────────────────────────────────────


def run_drill_99():
    """
    ── SCENARIO ──────────────────────────────────────────────────────────
    Unemployment office system. On startup the office loads a fixed set
    of benefit tiers into shared state. Routes read from that state.
    On shutdown the state is cleared. TestClient triggers both lifecycle
    events when used as a context manager.

    ── REQUIREMENTS ──────────────────────────────────────────────────────
    1. APP_STATE: dict — module-level (inside run_drill_99) shared state
       dict, starts empty. Define before lifespan and app.

    2. lifespan(app: FastAPI) — asynccontextmanager lifespan function
       • app: FastAPI — the application instance passed by FastAPI
         automatically; not used inside the function.
       Startup (before yield):
         Populates APP_STATE["tiers"] with exactly this dict:
           {"basic": 500, "standard": 800, "premium": 1200}
         Populates APP_STATE["status"] with the string "open".
       Shutdown (after yield, in finally block):
         Clears APP_STATE by calling APP_STATE.clear().

    3. app = FastAPI(lifespan=lifespan)

    4. GET /tiers
       • No parameters.
       • Returns APP_STATE["tiers"].

    5. GET /status
       • No parameters.
       • Returns {"status": APP_STATE["status"]}.

    ── YOUR CODE HERE ─────────────────────────────────────────────────────
    """

    # --- YOUR CODE HERE ---
    APP_STATE: dict = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        APP_STATE["tiers"] = {"basic": 500, "standard": 800, "premium": 1200}
        APP_STATE["status"] = "open"
        try:
            yield
        finally:
            APP_STATE.clear()

    app = FastAPI(lifespan=lifespan)

    @app.get("/tiers")
    def get_tiers():
        return APP_STATE["tiers"]

    @app.get("/status")
    def get_status():
        return {"status": APP_STATE["status"]}

    # ── TESTS ──────────────────────────────────────────────────────────
    # TestClient used as context manager triggers lifespan startup/shutdown

    # Test 1: APP_STATE is empty before client starts
    print("Test 1: APP_STATE empty before startup")
    assert APP_STATE == {}  # noqa: F821
    print(f"  APP_STATE={APP_STATE}")  # noqa: F821
    print("  PASS")

    with TestClient(app) as client:  # noqa: F821
        # Test 2: startup populated APP_STATE
        print("Test 2: startup populated APP_STATE")
        assert APP_STATE["status"] == "open"  # noqa: F821
        assert APP_STATE["tiers"] == {"basic": 500, "standard": 800, "premium": 1200}  # noqa: F821
        print(f"  APP_STATE={APP_STATE}")  # noqa: F821
        print("  PASS")

        # Test 3: GET /tiers returns the tiers dict
        print("Test 3: GET /tiers returns tiers")
        r = client.get("/tiers")
        assert r.status_code == 200
        assert r.json() == {"basic": 500, "standard": 800, "premium": 1200}
        print(f"  status={r.status_code}, body={r.json()}")
        print("  PASS")

        # Test 4: GET /status returns open
        print("Test 4: GET /status returns open")
        r = client.get("/status")
        assert r.status_code == 200
        assert r.json() == {"status": "open"}
        print(f"  status={r.status_code}, body={r.json()}")
        print("  PASS")

    # Test 5: APP_STATE is cleared after shutdown
    print("Test 5: APP_STATE cleared after shutdown")
    assert APP_STATE == {}  # noqa: F821
    print(f"  APP_STATE={APP_STATE}")  # noqa: F821
    print("  PASS")


run_drill_99()


# ── EXPECTED OUTPUT ────────────────────────────────────────────────────
# Test 1: APP_STATE empty before startup
#   APP_STATE={}
#   PASS
# Test 2: startup populated APP_STATE
#   APP_STATE={'status': 'open', 'tiers': {'basic': 500, 'standard': 800, 'premium': 1200}}
#   PASS
# Test 3: GET /tiers returns tiers
#   status=200, body={'basic': 500, 'standard': 800, 'premium': 1200}
#   PASS
# Test 4: GET /status returns open
#   status=200, body={'status': 'open'}
#   PASS
# Test 5: APP_STATE cleared after shutdown
#   APP_STATE={}
#   PASS
