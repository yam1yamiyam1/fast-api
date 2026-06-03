import asyncio  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


# started 706pm
async def run_drill_48():
    # =========================================================================
    # SCENARIO: The Concert Venue
    # =========================================================================
    # A concert venue has multiple entry gates. Each gate has a list of
    # middleware hooks that run in order before the attendee is let in.
    # If any hook fails, entry is blocked immediately.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: GATES = {}
    #
    # 2. A Pydantic model Attendee with two fields:
    #    - name: str
    #    - age: int
    #
    # 3. Three middleware hooks (NOT async, return nothing, just raise if invalid):
    #    - check_age(attendee: Attendee):
    #      - if attendee.age < 18, raise ValueError("Must be 18 or older")
    #    - check_ticket(attendee: Attendee):
    #      - if "vip" not in attendee.name.lower(), raise ValueError("No VIP ticket")
    #    - check_banned(attendee: Attendee):
    #      - if attendee.name.lower() == "john", raise ValueError("Banned attendee")
    #
    # 4. A decorator @register(gate_name, middleware: list)
    #    - middleware is a LIST of hook functions (not a dict)
    #    - create an object in GATES with handler as func, and middleware as middleware
    #    - return func
    #
    # 5. An async handler vip_gate_handler(attendee: Attendee) (you write this):
    #    - prints f"  Welcome, {attendee.name}!"
    #
    # 6. Apply @register to vip_gate_handler:
    #    gate_name  = "vip_gate"
    #    middleware = [check_age, check_ticket, check_banned]
    #
    # 7. An async dispatch(gate_name: str, raw_payload: dict):
    #    - if gate not found, print "404" and stop
    #    - validate raw_payload into an Attendee object
    #      - if ValidationError, print "Invalid data" and stop
    #    - loop through middleware list, call each hook passing the Attendee object
    #      - if any hook raises ValueError, print "Entry Denied: <msg>" and stop
    #    - if all hooks pass, call the handler passing the Attendee object directly
    #      (no **resolved this time — just pass attendee as a positional argument)
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    GATES = {}

    class Attendee(BaseModel):
        name: str
        age: int

    def check_age(attendee: Attendee):
        if attendee.age < 18:
            raise ValueError("Must be 18 or older")

    def check_ticket(attendee: Attendee):
        if "vip" not in attendee.name.lower():
            raise ValueError("No VIP ticket")

    def check_banned(attendee: Attendee):
        if "john" in attendee.name.lower():
            raise ValueError("Banned attendee")

    def register(gate_name, middleware: list):
        def decorator(func: Callable) -> Callable:
            GATES[gate_name] = {"handler": func, "middleware": middleware}
            return func

        return decorator

    @register(gate_name="vip_gate", middleware=[check_age, check_ticket, check_banned])
    async def vip_gate_handler(attendee: Attendee):
        print(f"  Welcome, {attendee.name}!")

    async def dispatch(gate_name: str, raw_payload: dict):
        if gate_name not in GATES:
            print("404")
            return
        route = GATES[gate_name]
        try:
            validated_attendee = Attendee(**raw_payload)
            for check in route["middleware"]:
                check(validated_attendee)
        except ValidationError:
            print("Invalid data")
            return
        except ValueError as msg:
            print(f"Entry Denied: {msg}")
            return
        return await route["handler"](validated_attendee)

    # --- TESTS (do not modify) ---
    print("Test 1: Valid VIP attendee")
    await dispatch("vip_gate", {"name": "VIP Alice", "age": 25})

    print("\nTest 2: Too young")
    await dispatch("vip_gate", {"name": "VIP Bob", "age": 16})

    print("\nTest 3: No VIP ticket")
    await dispatch("vip_gate", {"name": "Charlie", "age": 25})

    print("\nTest 4: Banned attendee")
    await dispatch("vip_gate", {"name": "VIP John", "age": 25})

    print("\nTest 5: Invalid data")
    await dispatch("vip_gate", {"name": "VIP Dave", "age": "old"})

    print("\nTest 6: Unknown gate")
    await dispatch("unknown_gate", {"name": "VIP Eve", "age": 30})

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid VIP attendee
    #   Welcome, VIP Alice!
    #
    # Test 2: Too young
    #   Entry Denied: Must be 18 or older
    #
    # Test 3: No VIP ticket
    #   Entry Denied: No VIP ticket
    #
    # Test 4: Banned attendee
    #   Entry Denied: Banned attendee
    #
    # Test 5: Invalid data
    #   Invalid data
    #
    # Test 6: Unknown gate
    #   404
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_48())
