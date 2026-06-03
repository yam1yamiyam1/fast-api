import asyncio  # noqa: F401
from typing import Callable  # noqa: F401

# =========================================================================
# SCENARIO:
# A food court has multiple stalls. Each stall is registered with a name
# and a "preparer" function that takes a raw order string and returns a
# prepared meal string.
#
# The dispatcher's job:
# - Take a stall name and a raw order
# - Find the right stall
# - Pass the raw order to EACH preparer function registered to that stall
# - Collect the results into a dict
# - Pass that dict to the stall's handler as keyword arguments
#
# REQUIREMENTS:
# 1. A registry: STALLS = {}
#
# 2. Three preparer functions (you write these):
#    - prepare_burger(order: str) -> str
#      - if "burger" not in order (case-insensitive), raise ValueError("No burger in order")
#      - otherwise return f"Burger: {order}"
#    - prepare_drink(order: str) -> str
#      - if "drink" not in order (case-insensitive), raise ValueError("No drink in order")
#      - otherwise return f"Drink: {order}"
#    - prepare_side(order: str) -> str
#      - always returns f"Side: fries (auto-added)"  (no validation needed)
#
# 3. Two async handler functions (you write these):
#    - burger_stall_handler(meal, drink, side)
#      - prints each argument on its own line, indented with two spaces
#    - simple_stall_handler(meal)
#      - prints the meal argument, indented with two spaces
#
# 4. A decorator @register(stall_name, preparers: dict)
#    - preparers maps an argument name to a preparer function
#      e.g. {"meal": prepare_burger}
#    - saves {"handler": func, "preparers": preparers} into STALLS[stall_name]
#
# 5. Apply @register to burger_stall_handler
#    stall_name = "burger_stall"
#    preparers  = {"meal": prepare_burger, "drink": prepare_drink, "side": prepare_side}
#
# 6. Apply @register to simple_stall_handler
#    stall_name = "simple_stall"
#    preparers  = {"meal": prepare_burger}
#
# 7. An async dispatch(stall_name: str, raw_order: str):
#    - If stall not found, print "No stall found"
#    - Loop through preparers, call each one with raw_order
#    - Collect results: resolved["meal"] = "Burger: ..." etc.
#    - If a preparer raises ValueError, print "Order Error: <msg>" and stop
#    - Call the handler with **resolved
#
# =========================================================================

# --- YOUR CODE HERE ---

# 1. STALLS registry
STALLS = {}


# 2. Three preparer functions
def prepare_burger(order: str) -> str:
    if "burger" not in order.lower():
        raise ValueError("No burger in order")
    return f"Burger: {order}"


def prepare_drink(order: str) -> str:
    if "drink" not in order.lower():
        raise ValueError("No drink in order")
    return f"Drink: {order}"


def prepare_side(order: str) -> str:
    return "Side: fries (auto-added)"


# 3. Two async handler functions


# 4. @register decorator
def register(stall_name, preparers: dict):
    def decorator(func: Callable) -> Callable:
        STALLS[stall_name] = {"handler": func, "preparers": preparers}
        return func

    return decorator


# 5. Apply @register to burger_stall_handler


# 6. Apply @register to simple_stall_handler
@register(
    stall_name="burger_stall",
    preparers={"meal": prepare_burger, "drink": prepare_drink, "side": prepare_side},
)
async def burger_stall_handler(meal, drink, side):
    print(f"  {meal}")
    print(f"  {drink}")
    print(f"  {side}")


@register(
    stall_name="simple_stall",
    preparers={"meal": prepare_burger},
)
async def simple_stall_handler(meal):
    print(f"  {meal}")


# 7. dispatch function
async def dispatch(stall_name: str, raw_order: str):
    if stall_name not in STALLS:
        print("No stall found")
        return
    stall = STALLS[stall_name]
    preparers = stall["preparers"]
    resolved = {}
    for process, func in preparers.items():
        try:
            resolved[process] = func(raw_order)
        except ValueError as e:
            print(f"Order Error: {e}")
            return
    await stall["handler"](**resolved)


# --- TESTS (do not modify) ---


async def main():
    print("Test 1: Valid full order")
    await dispatch("burger_stall", "burger and drink")

    print("\nTest 2: Missing drink")
    await dispatch("burger_stall", "burger only")

    print("\nTest 3: Simple stall valid")
    await dispatch("simple_stall", "burger please")

    print("\nTest 4: Unknown stall")
    await dispatch("pizza_stall", "burger and drink")


asyncio.run(main())

# =========================================================================
# EXPECTED OUTPUT:
#
# Test 1: Valid full order
#   Burger: burger and drink
#   Drink: burger and drink
#   Side: fries (auto-added)
#
# Test
