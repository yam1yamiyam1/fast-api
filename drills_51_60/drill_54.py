import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_54():
    # =========================================================================
    # SCENARIO: The Restaurant Kitchen
    # =========================================================================
    # A Kitchen class has two types of methods — ones that require the kitchen
    # to be open, and ones that require the chef to be present. Two separate
    # decorators handle each check. Each decorator has its own rule.
    #
    # REQUIREMENTS:
    #
    # 1. A decorator require_open(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - if instance.is_open is False, print "  Kitchen is closed" and return None
    #    - otherwise call and await func normally
    #
    # 2. A decorator require_chef(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - if instance.chef_present is False, print "  No chef on duty" and return None
    #    - otherwise call and await func normally
    #
    # 3. A class Kitchen:
    #    - __init__(self, name: str):
    #        - self.name = name
    #        - self.is_open = False
    #        - self.chef_present = False
    #    - async method open_kitchen(self):
    #        - NO decorator
    #        - sets self.is_open = True
    #        - prints f"  {self.name} is now open"
    #    - async method call_chef(self):
    #        - NO decorator
    #        - sets self.chef_present = True
    #        - prints f"  Chef is on duty"
    #    - async method serve_food(self):
    #        - decorated with @require_open
    #        - prints f"  Serving food at {self.name}"
    #    - async method cook_special(self):
    #        - decorated with @require_chef
    #        - prints f"  Cooking the special at {self.name}"
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    def require(key: str, message: str):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                instance = args[0]
                if getattr(instance, key) is False:
                    print(f"  {message}")
                    return None
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    require_open = require(key="is_open", message="Kitchen is closed")
    require_chef = require(key="chef_present", message="No chef on duty")

    class Kitchen:
        def __init__(self, name: str):
            self.name = name
            self.is_open = False
            self.chef_present = False

        async def open_kitchen(self):
            self.is_open = True
            print(f"  {self.name} is now open")

        async def call_chef(self):
            self.chef_present = True
            print("  Chef is on duty")

        @require_open
        async def serve_food(self):
            print(f"  Serving food at {self.name}")

        @require_chef
        async def cook_special(self):
            print(f"  Cooking the special at {self.name}")

    # --- TESTS (do not modify) ---
    kitchen = Kitchen(name="Luigi's")

    print("Test 1: Serve food before kitchen opens")
    await kitchen.serve_food()

    print("\nTest 2: Cook special before chef arrives")
    await kitchen.cook_special()

    print("\nTest 3: Open the kitchen")
    await kitchen.open_kitchen()

    print("\nTest 4: Serve food after kitchen opens")
    await kitchen.serve_food()

    print("\nTest 5: Cook special — still no chef")
    await kitchen.cook_special()

    print("\nTest 6: Call the chef")
    await kitchen.call_chef()

    print("\nTest 7: Cook special after chef arrives")
    await kitchen.cook_special()

    print("\nTest 8: Confirm decorator preserved method names")
    print(f"  serve_food name: {kitchen.serve_food.__name__}")
    print(f"  cook_special name: {kitchen.cook_special.__name__}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Serve food before kitchen opens
    #   Kitchen is closed
    #
    # Test 2: Cook special before chef arrives
    #   No chef on duty
    #
    # Test 3: Open the kitchen
    #   Luigi's is now open
    #
    # Test 4: Serve food after kitchen opens
    #   Serving food at Luigi's
    #
    # Test 5: Cook special — still no chef
    #   No chef on duty
    #
    # Test 6: Call the chef
    #   Chef is on duty
    #
    # Test 7: Cook special after chef arrives
    #   Cooking the special at Luigi's
    #
    # Test 8: Confirm decorator preserved method names
    #   serve_food name: serve_food
    #   cook_special name: cook_special
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_54())
