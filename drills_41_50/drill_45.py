import asyncio  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_45():
    # =========================================================================
    # SCENARIO: The Movie Theater
    # =========================================================================
    # A movie theater has multiple screens. Each screen is registered with a
    # title and a set of "validator" functions. Each validator takes the
    # raw ticket string and returns a processed string.
    #
    # The dispatcher's job:
    # - Take a screen title and a raw ticket string
    # - Find the right screen
    # - Pass the raw ticket to EACH validator registered to that screen
    # - Collect the results into a dict
    # - Pass that dict to the screen's handler as keyword arguments
    #
    # REQUIREMENTS:
    #
    # 1. A registry: SCREENS = {}
    #
    # 2. Three validator functions (you write these):
    #    - validate_ticket(ticket: str) -> str
    #      - if "ticket" not in ticket (case-insensitive), raise ValueError("No ticket")
    #      - otherwise return f"Ticket: {ticket}"
    #    - validate_seat(ticket: str) -> str
    #      - if "seat" not in ticket (case-insensitive), raise ValueError("No seat assigned")
    #      - otherwise return f"Seat: {ticket}"
    #    - validate_snack(ticket: str) -> str
    #      - always returns f"Snack: popcorn (complimentary)"
    #
    # 3. Two async handler functions (you write these):
    #    - vip_screen_handler(ticket, seat, snack)
    #      - prints each argument on its own line, indented with two spaces
    #    - standard_screen_handler(ticket, seat)
    #      - prints each argument on its own line, indented with two spaces
    #
    # 4. A decorator @register(screen_title, validators: dict)
    #    - create an object in SCREENS with handler as func, and validators as validators
    #
    # 5. Apply @register to vip_screen_handler
    #    screen_title = "vip_screen"
    #    validators   = {"ticket": validate_ticket, "seat": validate_seat, "snack": validate_snack}
    #
    # 6. Apply @register to standard_screen_handler
    #    screen_title = "standard_screen"
    #    validators   = {"ticket": validate_ticket, "seat": validate_seat}
    #
    # 7. An async dispatch(screen_title: str, raw_ticket: str):
    #    - if screen not found, print "No screen found" and stop
    #    - create resolved = {}
    #    - loop through validators, call each one with raw_ticket
    #    - collect results into resolved
    #    - if a validator raises ValueError, print "Ticket Error: <msg>" and stop
    #    - call the handler with **resolved
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    SCREENS = {}

    async def validate_ticket(ticket: str) -> str:
        if "ticket" not in ticket.lower():
            raise ValueError("No ticket")
        return f"Ticket: {ticket}"

    async def validate_seat(ticket: str) -> str:
        if "seat" not in ticket.lower():
            raise ValueError("No seat assigned")
        return f"Seat: {ticket}"

    async def validate_snack(ticket: str) -> str:
        return "Snack: popcorn (complimentary)"

    def register(screen_title, validators: dict):
        def decorator(func: Callable) -> Callable:
            SCREENS[screen_title] = {"handler": func, "validators": validators}
            return func

        return decorator

    @register(
        screen_title="vip_screen",
        validators={
            "ticket": validate_ticket,
            "seat": validate_seat,
            "snack": validate_snack,
        },
    )
    async def vip_screen_handler(ticket, seat, snack):
        print(f"  {ticket}")
        print(f"  {seat}")
        print(f"  {snack}")

    @register(
        screen_title="standard_screen",
        validators={"ticket": validate_ticket, "seat": validate_seat},
    )
    async def standard_screen_handler(ticket, seat):
        print(f"  {ticket}")
        print(f"  {seat}")

    async def dispatch(screen_title: str, raw_ticket: str):
        if screen_title not in SCREENS:
            print("No screen found")
            return
        route = SCREENS[screen_title]
        resolved = {}
        for args_name, func in route["validators"].items():
            try:
                resolved[args_name] = await func(raw_ticket)
            except ValueError as msg:
                print(f"Ticket Error: {msg}")
                return
        await route["handler"](**resolved)

    # --- TESTS (do not modify) ---
    print("Test 1: Valid VIP ticket")
    await dispatch("vip_screen", "ticket seat A12")

    print("\nTest 2: Missing seat")
    await dispatch("vip_screen", "ticket only")

    print("\nTest 3: Standard screen valid")
    await dispatch("standard_screen", "ticket seat B5")

    print("\nTest 4: Unknown screen")
    await dispatch("unknown_screen", "ticket seat A1")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid VIP ticket
    #   Ticket: ticket seat A12
    #   Seat: ticket seat A12
    #   Snack: popcorn (complimentary)
    #
    # Test 2: Missing seat
    #   Ticket Error: No seat assigned
    #
    # Test 3: Standard screen valid
    #   Ticket: ticket seat B5
    #   Seat: ticket seat B5
    #
    # Test 4: Unknown screen
    #   No screen found
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_45())
