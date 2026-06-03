import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_73():
    # =========================================================================
    # SCENARIO: The Courthouse
    # =========================================================================
    # A courthouse case management system handles multiple case types.
    # Instead of a standalone dict registry + separate decorator + separate
    # dispatch function, all three live together inside a single Router class.
    #
    # A Router instance owns its registry, its decorator method, and its
    # dispatch method. Multiple Router instances are completely independent.
    # This is the shape FastAPI's APIRouter uses internally.
    #
    # NEW CONCEPT: class-based router — registry + OOP + dispatch in one object
    # - The registry is an instance attribute (self.routes = {})
    #   not a module-level dict — so each Router owns its own routes
    # - The decorator is a method on the Router that registers handlers
    #   into self.routes
    # - dispatch is also a method — it looks up and calls from self.routes
    # - Two Router instances never share routes
    #
    # REQUIREMENTS:
    #
    # 1. Two Pydantic models:
    #    - CaseFile: case_id (str), charge (str)
    #    - Verdict: case_id (str), outcome (str), judge (str)
    #
    # 2. A class Router:
    #    - __init__(self, name: str):
    #        - self.name = name
    #        - self.routes = {}
    #    - method register(self, action: str):
    #        - a decorator factory — action is the registry key
    #        - stores the handler in self.routes under action
    #        - returns func unchanged
    #    - async method dispatch(self, action: str, case: CaseFile) -> dict | None:
    #        - if action not in self.routes, return {"error": f"unknown action: {action}"}
    #        - call and await the handler passing case
    #        - return the result
    #
    # 3. Two Router instances:
    #    - criminal = Router(name="Criminal Court")
    #    - civil    = Router(name="Civil Court")
    #
    # 4. Three async handler functions:
    #    - async def arraign(case: CaseFile) -> dict:
    #        - returns Verdict(case_id=case.case_id, outcome="arraigned", judge="Judge Reyes").model_dump()
    #    - async def sentence(case: CaseFile) -> dict:
    #        - returns Verdict(case_id=case.case_id, outcome="sentenced", judge="Judge Reyes").model_dump()
    #    - async def mediate(case: CaseFile) -> dict:
    #        - returns Verdict(case_id=case.case_id, outcome="mediated", judge="Judge Santos").model_dump()
    #
    # 5. Register handlers:
    #    - @criminal.register("arraign")  → arraign
    #    - @criminal.register("sentence") → sentence
    #    - @civil.register("mediate")     → mediate
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class CaseFile(BaseModel):
        case_id: str
        charge: str

    class Verdict(BaseModel):
        case_id: str
        outcome: str
        judge: str

    class Router:
        def __init__(self, name: str):
            self.name = name
            self.routes = {}

        def register(self, action: str):
            def decorator(func: Callable):
                self.routes[action] = func
                return func

            return decorator

        async def dispatch(self, action: str, case: CaseFile):
            if action not in self.routes:
                return {"error": f"unknown action: {action}"}
            return await self.routes[action](case)

    criminal = Router(name="Criminal Court")
    civil = Router(name="Civil Court")

    @criminal.register("arraign")
    async def arraign(case: CaseFile):
        return Verdict(
            case_id=case.case_id, outcome="arraigned", judge="Judge Reyes"
        ).model_dump()

    @criminal.register("sentence")
    async def sentence(case: CaseFile):
        return Verdict(
            case_id=case.case_id, outcome="sentenced", judge="Judge Reyes"
        ).model_dump()

    @civil.register("mediate")
    async def mediate(case: CaseFile):
        return Verdict(
            case_id=case.case_id, outcome="mediated", judge="Judge Santos"
        ).model_dump()

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    case_a = CaseFile(case_id="CR-001", charge="theft")  # noqa: F821
    case_b = CaseFile(case_id="CV-001", charge="breach of contract")  # noqa: F821

    print("Test 1: criminal.dispatch arraign")
    result = await criminal.dispatch("arraign", case_a)  # noqa: F821
    assert result == {
        "case_id": "CR-001",
        "outcome": "arraigned",
        "judge": "Judge Reyes",
    }, f"Got {result!r}"
    print("  PASS")

    print("\nTest 2: criminal.dispatch sentence")
    result = await criminal.dispatch("sentence", case_a)  # noqa: F821
    assert result == {
        "case_id": "CR-001",
        "outcome": "sentenced",
        "judge": "Judge Reyes",
    }, f"Got {result!r}"
    print("  PASS")

    print("\nTest 3: civil.dispatch mediate")
    result = await civil.dispatch("mediate", case_b)  # noqa: F821
    assert result == {
        "case_id": "CV-001",
        "outcome": "mediated",
        "judge": "Judge Santos",
    }, f"Got {result!r}"
    print("  PASS")

    print("\nTest 4: criminal cannot access civil routes")
    result = await criminal.dispatch("mediate", case_a)  # noqa: F821
    assert result == {"error": "unknown action: mediate"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 5: civil cannot access criminal routes")
    result = await civil.dispatch("arraign", case_b)  # noqa: F821
    assert result == {"error": "unknown action: arraign"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 6: unknown action on either router")
    result = await criminal.dispatch("dismiss", case_a)  # noqa: F821
    assert result == {"error": "unknown action: dismiss"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 7: routers have independent registries")
    assert criminal.routes is not civil.routes  # noqa: F821
    assert set(criminal.routes.keys()) == {"arraign", "sentence"}  # noqa: F821
    assert set(civil.routes.keys()) == {"mediate"}  # noqa: F821
    print("  PASS")

    print("\nTest 8: a third router starts empty")
    appeals = Router(name="Appeals Court")  # noqa: F821
    assert appeals.routes == {}
    result = await appeals.dispatch("arraign", case_a)
    assert result == {"error": "unknown action: arraign"}, f"Got {result!r}"
    print("  PASS")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: criminal.dispatch arraign
    #   PASS
    #
    # Test 2: criminal.dispatch sentence
    #   PASS
    #
    # Test 3: civil.dispatch mediate
    #   PASS
    #
    # Test 4: criminal cannot access civil routes
    #   PASS
    #
    # Test 5: civil cannot access criminal routes
    #   PASS
    #
    # Test 6: unknown action on either router
    #   PASS
    #
    # Test 7: routers have independent registries
    #   PASS
    #
    # Test 8: a third router starts empty
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_73())
