import asyncio  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401

# started 7:43pm


async def run_drill_50():
    # =========================================================================
    # SCENARIO: The Airport
    # =========================================================================
    # An airport has multiple boarding gates. Each gate runs three stages
    # before a passenger boards:
    #
    # STAGE 1 — Pydantic: validate the raw payload into a Passenger object
    # STAGE 2 — Middleware: a list of hooks that check the Passenger object
    #           (just raise if invalid, return nothing)
    # STAGE 3 — Dependencies: a dict of async functions that take the token
    #           and return real objects collected into resolved
    #
    # If any stage fails, block immediately with the correct error message.
    # If all pass, call the handler with **resolved.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: GATES = {}
    #
    # 2. A Pydantic model Passenger:
    #    - name: str
    #    - age: int
    #
    # 3. A Pydantic model BoardingPass:
    #    - seat: str
    #    - flight: str
    #
    # 4. Two middleware hooks (NOT async, no return value):
    #    - check_age(passenger: Passenger):
    #      - if passenger.age < 18, raise ValueError("Passenger too young")
    #    - check_name(passenger: Passenger):
    #      - if "banned" in passenger.name.lower(), raise ValueError("Passenger banned")
    #
    # 5. One async dependency function:
    #    - get_boarding_pass(token: str) -> BoardingPass
    #      - if token != "valid-token", raise ValueError("Invalid boarding pass")
    #      - otherwise return BoardingPass(seat="12A", flight="PH-001")
    #
    # 6. A decorator @register(gate_name, middleware: list, dependencies: dict)
    #    - create an object in GATES with handler, middleware, and dependencies
    #    - return func
    #
    # 7. An async handler boarding_handler(boarding_pass) (you write this):
    #    - prints f"  Boarding: {boarding_pass.seat} on {boarding_pass.flight}"
    #
    # 8. Apply @register to boarding_handler:
    #    gate_name    = "gate_1"
    #    middleware   = [check_age, check_name]
    #    dependencies = {"boarding_pass": get_boarding_pass}
    #
    # 9. An async dispatch(gate_name: str, raw_payload: dict, token: str):
    #    - if gate not found, print "404" and stop
    #    - STAGE 1: validate raw_payload into Passenger
    #      - if ValidationError, print "Invalid data" and stop
    #    - STAGE 2: loop through middleware, pass Passenger object to each
    #      - if ValueError, print "Boarding Denied: <msg>" and stop
    #    - STAGE 3: loop through dependencies, await each passing token
    #      - if ValueError, print "Boarding Denied: <msg>" and stop
    #    - call the handler with **resolved
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    GATES = {}

    class Passenger(BaseModel):
        name: str
        age: int

    class BoardingPass(BaseModel):
        seat: str
        flight: str

    def check_age(passenger: Passenger):
        if passenger.age < 18:
            raise ValueError("Passenger too young")

    def check_name(passenger: Passenger):
        if "banned" in passenger.name.lower():
            raise ValueError("Passenger banned")

    async def get_boarding_pass(token: str) -> BoardingPass:
        if token != "valid-token":
            raise ValueError("Invalid boarding pass")
        return BoardingPass(seat="12A", flight="PH-001")

    def register(gate_name, middleware: list, dependencies: dict):
        def decorator(func: Callable) -> Callable:
            GATES[gate_name] = {
                "handler": func,
                "middleware": middleware,
                "dependencies": dependencies,
            }
            return func

        return decorator

    @register(
        gate_name="gate_1",
        middleware=[check_age, check_name],
        dependencies={"boarding_pass": get_boarding_pass},
    )
    async def boarding_handler(boarding_pass):
        print(f"  Boarding: {boarding_pass.seat} on {boarding_pass.flight}")

    async def dispatch(gate_name: str, raw_payload: dict, token: str):
        if gate_name not in GATES:
            print("404")
            return
        route = GATES[gate_name]
        resolved = {}
        try:
            validated_pax = Passenger(**raw_payload)
        except ValidationError:
            print("Invalid data")
            return
        for check in route["middleware"]:
            try:
                check(validated_pax)
            except ValueError as msg:
                print(f"Boarding Denied: {msg}")
                return
        for arg_name, func in route["dependencies"].items():
            try:
                resolved[arg_name] = await func(token)
            except ValueError as msg:
                print(f"Boarding Denied: {msg}")
                return
        return await route["handler"](**resolved)

    # --- TESTS (do not modify) ---
    print("Test 1: Valid passenger")
    await dispatch("gate_1", {"name": "Alice", "age": 30}, token="valid-token")

    print("\nTest 2: Invalid data")
    await dispatch("gate_1", {"name": "Alice", "age": "old"}, token="valid-token")

    print("\nTest 3: Too young")
    await dispatch("gate_1", {"name": "Alice", "age": 15}, token="valid-token")

    print("\nTest 4: Banned passenger")
    await dispatch("gate_1", {"name": "Banned Bob", "age": 30}, token="valid-token")

    print("\nTest 5: Invalid boarding pass")
    await dispatch("gate_1", {"name": "Alice", "age": 30}, token="wrong-token")

    print("\nTest 6: Unknown gate")
    await dispatch("unknown_gate", {"name": "Alice", "age": 30}, token="valid-token")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid passenger
    #   Boarding: 12A on PH-001
    #
    # Test 2: Invalid data
    #   Invalid data
    #
    # Test 3: Too young
    #   Boarding Denied: Passenger too young
    #
    # Test 4: Banned passenger
    #   Boarding Denied: Passenger banned
    #
    # Test 5: Invalid boarding pass
    #   Boarding Denied: Invalid boarding pass
    #
    # Test 6: Unknown gate
    #   404
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_50())
