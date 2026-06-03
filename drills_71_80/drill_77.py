import asyncio  # noqa: F401
from contextvars import ContextVar  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_77():
    # =========================================================================
    # SCENARIO: The Police Station
    # =========================================================================
    # A police dispatch system logs every action taken during a case.
    # Each case gets a unique case_id that must appear in every log entry.
    # Instead of passing case_id as an argument to every function,
    # it is stored in a ContextVar at the start of each request and
    # read directly wherever it's needed.
    #
    # NEW CONCEPT: contextvars — request-scoped state without passing everywhere
    # - ContextVar is defined once at module/function level — it's the "slot"
    # - .set(value) stores a value for the current async context, returns a token
    # - .get() reads the current value — no argument needed
    # - .reset(token) restores the previous value (cleanup)
    # - Each concurrent async task has its own context — no bleeding between tasks
    # - This is how FastAPI propagates request state internally
    #
    # REQUIREMENTS:
    #
    # 1. A ContextVar defined inside run_drill_77 (not module level):
    #    - case_id_var: ContextVar[str] with default "none"
    #
    # 2. A Pydantic model Incident:
    #    - case_id: str
    #    - crime: str
    #    - suspect: str
    #
    # 3. Three async functions that read case_id_var directly (no argument):
    #    - async def log_intake() -> str:
    #        - returns f"[{case_id_var.get()}] intake logged"
    #    - async def run_background_check() -> str:
    #        - returns f"[{case_id_var.get()}] background check complete"
    #    - async def file_report() -> str:
    #        - returns f"[{case_id_var.get()}] report filed"
    #
    # 4. A registry: ROUTES = {}
    #
    # 5. A decorator @route(action: str):
    #    - stores handler in ROUTES under action
    #    - returns func unchanged
    #
    # 6. An async handler process_incident(incident: Incident) -> dict:
    #    - decorated with @route("process")
    #    - calls log_intake(), run_background_check(), file_report() in sequence
    #    - returns {
    #        "case_id": incident.case_id,
    #        "suspect": incident.suspect,
    #        "logs": [result of each call in order],
    #        "status": "processed"
    #      }
    #
    # 7. An async dispatch(action: str, raw_payload: dict) -> dict:
    #    - if action not in ROUTES, return {"error": f"unknown action: {action}"}
    #    - validate raw_payload into Incident
    #      - if ValidationError, return {"error": "invalid incident"}
    #    - SET case_id_var to incident.case_id, saving the token
    #    - call and await the handler passing the validated incident
    #    - RESET case_id_var using the token (in a finally block)
    #    - return the result
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    case_id_var: ContextVar[str] = ContextVar("case_id_var", default="none")

    class Incident(BaseModel):
        case_id: str
        crime: str
        suspect: str

    async def log_intake():
        return f"[{case_id_var.get()}] intake logged"

    async def run_background_check():
        return f"[{case_id_var.get()}] background check complete"

    async def file_report():
        return f"[{case_id_var.get()}] report filed"

    ROUTES = {}

    def route(action: str):
        def decorator(func: Callable):
            ROUTES[action] = func
            return func

        return decorator

    @route("process")
    async def process_incident(incident: Incident):
        return {
            "case_id": incident.case_id,
            "suspect": incident.suspect,
            "logs": [
                await log_intake(),
                await run_background_check(),
                await file_report(),
            ],
            "status": "processed",
        }

    async def dispatch(action: str, raw_payload: dict):
        if action not in ROUTES:
            return {"error": f"unknown action: {action}"}
        try:
            incident = Incident(**raw_payload)
        except ValidationError:
            return {"error": "invalid incident"}
        token = case_id_var.set(incident.case_id)
        try:
            return await ROUTES[action](incident)
        finally:
            case_id_var.reset(token)

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    print("Test 1: valid incident — case_id flows through all log calls")
    result = await dispatch(
        "process", {"case_id": "CASE-001", "crime": "theft", "suspect": "Alice"}
    )  # noqa: F821
    print(f"  {result}")
    assert result == {
        "case_id": "CASE-001",
        "suspect": "Alice",
        "logs": [
            "[CASE-001] intake logged",
            "[CASE-001] background check complete",
            "[CASE-001] report filed",
        ],
        "status": "processed",
    }, f"Got {result!r}"
    print("  PASS")

    print("\nTest 2: different case_id — context is independent per dispatch call")
    result = await dispatch(
        "process", {"case_id": "CASE-002", "crime": "fraud", "suspect": "Bob"}
    )  # noqa: F821
    print(f"  {result}")
    assert result["case_id"] == "CASE-002"
    assert all("CASE-002" in log for log in result["logs"])
    print("  PASS")

    print("\nTest 3: case_id_var resets to default after dispatch")
    await dispatch(
        "process", {"case_id": "CASE-003", "crime": "arson", "suspect": "Carol"}
    )  # noqa: F821
    current = case_id_var.get()  # noqa: F821
    print(f"  case_id_var after dispatch: {current!r}")
    assert current == "none", f"Expected 'none', got {current!r}"
    print("  PASS")

    print("\nTest 4: two concurrent dispatches have independent context")

    async def run_case(case_id, suspect):
        return await dispatch(
            "process", {"case_id": case_id, "crime": "trespass", "suspect": suspect}
        )  # noqa: F821

    results = await asyncio.gather(
        run_case("CASE-A", "Dave"), run_case("CASE-B", "Eve")
    )
    print(f"  result A case_id: {results[0]['case_id']}")
    print(f"  result B case_id: {results[1]['case_id']}")
    assert results[0]["case_id"] == "CASE-A"
    assert results[1]["case_id"] == "CASE-B"
    assert all("CASE-A" in log for log in results[0]["logs"])
    assert all("CASE-B" in log for log in results[1]["logs"])
    print("  PASS")

    print("\nTest 5: invalid payload")
    result = await dispatch("process", {"case_id": "X"})  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "invalid incident"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 6: unknown action")
    result = await dispatch(
        "close", {"case_id": "CASE-001", "crime": "theft", "suspect": "Alice"}
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "unknown action: close"}, f"Got {result!r}"
    print("  PASS")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: valid incident — case_id flows through all log calls
    #   {'case_id': 'CASE-001', 'suspect': 'Alice', 'logs': ['[CASE-001] intake logged',
    #    '[CASE-001] background check complete', '[CASE-001] report filed'], 'status': 'processed'}
    #   PASS
    #
    # Test 2: different case_id — context is independent per dispatch call
    #   {'case_id': 'CASE-002', ...logs with CASE-002..., 'status': 'processed'}
    #   PASS
    #
    # Test 3: case_id_var resets to default after dispatch
    #   case_id_var after dispatch: 'none'
    #   PASS
    #
    # Test 4: two concurrent dispatches have independent context
    #   result A case_id: CASE-A
    #   result B case_id: CASE-B
    #   PASS
    #
    # Test 5: invalid payload
    #   {'error': 'invalid incident'}
    #   PASS
    #
    # Test 6: unknown action
    #   {'error': 'unknown action: close'}
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_77())
