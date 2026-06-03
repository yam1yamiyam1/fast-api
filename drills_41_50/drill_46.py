import asyncio  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_46():
    # =========================================================================
    # SCENARIO: The Gym
    # =========================================================================
    # A gym has multiple workout stations. Each station is registered with a
    # name and a set of "check" functions. Each check takes the member's
    # raw access string and returns a verified string.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: STATIONS = {}
    #
    # 2. Three check functions (you write these — NOTE: these are NOT async):
    #    - check_membership(access: str) -> str
    #      - if "member" not in access (case-insensitive), raise ValueError("Not a member")
    #      - otherwise return f"Member: {access}"
    #    - check_equipment(access: str) -> str
    #      - if "equipment" not in access (case-insensitive), raise ValueError("No equipment clearance")
    #      - otherwise return f"Equipment: {access}"
    #    - check_towel(access: str) -> str
    #      - always returns f"Towel: included"
    #
    # 3. Two async handler functions (you write these):
    #    - vip_station_handler(membership, equipment, towel)
    #      - prints each argument on its own line, indented with two spaces
    #    - basic_station_handler(membership)
    #      - prints the membership argument, indented with two spaces
    #
    # 4. A decorator @register(station_name, checks: dict)
    #    - create an object in STATIONS with handler as func, and checks as checks
    #    - NOTE: the decorator must return something so the handler stays callable
    #
    # 5. Apply @register to vip_station_handler
    #    station_name = "vip_station"
    #    checks = {"membership": check_membership, "equipment": check_equipment, "towel": check_towel}
    #
    # 6. Apply @register to basic_station_handler
    #    station_name = "basic_station"
    #    checks = {"membership": check_membership}
    #
    # 7. An async dispatch(station_name: str, raw_access: str):
    #    - if station not found, print "No station found" and stop
    #    - create resolved = {}
    #    - loop through checks — NOTE: check functions are NOT async, so don't await them
    #    - collect results into resolved
    #    - if a check raises ValueError, print "Access Error: <msg>", stop immediately
    #    - call the handler with **resolved
    #    - NOTE: the handler IS async, so you do need to await it
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    STATIONS = {}

    def check_membership(access: str) -> str:
        if "member" not in access.lower():
            raise ValueError("Not a member")
        return f"Member: {access}"

    def check_equipment(access: str) -> str:
        if "equipment" not in access.lower():
            raise ValueError("No equipment clearance")
        return f"Equipment: {access}"

    def check_towel(access: str) -> str:
        return "Towel: included"

    def register(station_name, checks: dict):
        def decorator(func: Callable) -> Callable:
            STATIONS[station_name] = {"handler": func, "checks": checks}
            return func

        return decorator

    @register(
        station_name="vip_station",
        checks={
            "membership": check_membership,
            "equipment": check_equipment,
            "towel": check_towel,
        },
    )
    async def vip_station_handler(membership, equipment, towel):
        print(f"  {membership}")
        print(f"  {equipment}")
        print(f"  {towel}")

    @register(
        station_name="basic_station",
        checks={"membership": check_membership},
    )
    async def basic_station_handler(membership):
        print(f"  {membership}")

    async def dispatch(station_name: str, raw_access: str):
        if station_name not in STATIONS:
            print("No station found")
            return
        route = STATIONS[station_name]
        resolved = {}
        for arg_name, func in route["checks"].items():
            try:
                resolved[arg_name] = func(raw_access)
            except ValueError as msg:
                print(f"Access Error: {msg}")
                return
        return await route["handler"](**resolved)

    # --- TESTS (do not modify) ---
    print("Test 1: Valid VIP access")
    await dispatch("vip_station", "member equipment")

    print("\nTest 2: Missing equipment clearance")
    await dispatch("vip_station", "member only")

    print("\nTest 3: Basic station valid")
    await dispatch("basic_station", "member access")

    print("\nTest 4: Unknown station")
    await dispatch("unknown_station", "member equipment")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid VIP access
    #   Member: member equipment
    #   Equipment: member equipment
    #   Towel: included
    #
    # Test 2: Missing equipment clearance
    #   Access Error: No equipment clearance
    #
    # Test 3: Basic station valid
    #   Member: member access
    #
    # Test 4: Unknown station
    #   No station found
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_46())
