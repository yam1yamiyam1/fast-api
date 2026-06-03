import asyncio  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_61():
    # =========================================================================
    # SCENARIO: The Vending Machine
    # =========================================================================
    # A vending machine exposes a dispatch function. Unlike previous drills,
    # dispatch must RETURN a value that the caller uses — not just print.
    # The caller decides what to do with the result.
    #
    # This drill is about one thing: dispatch returns values, and those
    # values flow back to the caller correctly through every layer.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: MACHINE = {}
    #
    # 2. A decorator @slot(item_name):
    #    - stores the handler into MACHINE under item_name
    #    - returns func unchanged
    #
    # 3. Three async handler functions (you write these):
    #    - async def dispense_cola() -> dict:
    #        - returns {"item": "Cola", "price": 1.50, "calories": 140}
    #    - async def dispense_chips() -> dict:
    #        - returns {"item": "Chips", "price": 2.00, "calories": 250}
    #    - async def dispense_water() -> dict:
    #        - returns {"item": "Water", "price": 1.00, "calories": 0}
    #
    # 4. Apply @slot to each handler:
    #    - @slot("cola")    → dispense_cola
    #    - @slot("chips")   → dispense_chips
    #    - @slot("water")   → dispense_water
    #
    # 5. An async dispatch(item_name: str) -> dict | None:
    #    - if item_name not in MACHINE, print "  Item not found" and return None
    #    - call and await the handler
    #    - return the result — do NOT print inside dispatch
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    MACHINE = {}

    def slot(item_name):
        def decorator(func: Callable) -> Callable:
            MACHINE[item_name] = func
            return func

        return decorator

    @slot("cola")
    async def dispense_cola() -> dict:
        return {"item": "Cola", "price": 1.50, "calories": 140}

    @slot("chips")
    async def dispense_chips() -> dict:
        return {"item": "Chips", "price": 2.00, "calories": 250}

    @slot("water")
    async def dispense_water() -> dict:
        return {"item": "Water", "price": 1.00, "calories": 0}

    async def dispatch(item_name: str) -> dict | None:
        if item_name not in MACHINE:
            print("  Item not found")
            return
        route = MACHINE[item_name]
        return await route()

    # --- TESTS (do not modify) ---
    print("Test 1: Dispense cola")
    result = await dispatch("cola")
    print(f"  Got: {result}")
    print(f"  Price: ${result['price']}")

    print("\nTest 2: Dispense chips")
    result = await dispatch("chips")
    print(f"  Got: {result}")

    print("\nTest 3: Dispense water")
    result = await dispatch("water")
    print(f"  Calories: {result['calories']}")

    print("\nTest 4: Unknown item — returns None")
    result = await dispatch("pizza")
    print(f"  Result: {result}")

    print("\nTest 5: Caller uses return value in logic")
    result = await dispatch("cola")
    if result and result["calories"] > 100:
        print(f"  Warning: {result['item']} is high calorie")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Dispense cola
    #   Got: {'item': 'Cola', 'price': 1.5, 'calories': 140}
    #   Price: $1.5
    #
    # Test 2: Dispense chips
    #   Got: {'item': 'Chips', 'price': 2.0, 'calories': 250}
    #
    # Test 3: Dispense water
    #   Calories: 0
    #
    # Test 4: Unknown item — returns None
    #   Item not found
    #   Result: None
    #
    # Test 5: Caller uses return value in logic
    #   Warning: Cola is high calorie
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_61())
