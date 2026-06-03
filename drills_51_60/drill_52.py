import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_52():
    # =========================================================================
    # SCENARIO: The Gym Turnstile
    # =========================================================================
    # A GymMember class tracks how many times a member has entered the gym.
    # A decorator handles incrementing the entry count automatically before
    # the method runs. But there's a danger: if the count is set BEFORE the
    # method runs and the method raises, the count is wrong forever.
    #
    # REQUIREMENTS:
    #
    # 1. A decorator track_entry(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - increments instance.entry_count by 1 BEFORE calling func
    #    - calls and awaits func normally
    #    - if func raises any Exception, decrement instance.entry_count by 1
    #      and re-raise the exception
    #      (hint: try/finally is not enough here — you need try/except/raise)
    #
    # 2. A class GymMember:
    #    - __init__(self, name: str):
    #        - self.name = name
    #        - self.entry_count = 0
    #    - async method enter(self):
    #        - decorated with @track_entry
    #        - prints f"  {self.name} entered. Entries: {self.entry_count}"
    #    - async method enter_broken(self):
    #        - decorated with @track_entry
    #        - raises RuntimeError("Turnstile jammed")
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    def track_entry(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            instance = args[0]
            instance.entry_count += 1
            try:
                return await func(*args, **kwargs)
            except Exception:
                instance.entry_count -= 1
                raise

        return wrapper

    class GymMember:
        def __init__(self, name: str):
            self.name = name
            self.entry_count = 0

        @track_entry
        async def enter(self):
            print(f"  {self.name} entered. Entries: {self.entry_count}")

        @track_entry
        async def enter_broken(self):
            raise RuntimeError("Turnstile jammed")

    # --- TESTS (do not modify) ---
    member = GymMember(name="Bob")

    print("Test 1: Normal entry")
    await member.enter()

    print("\nTest 2: Normal entry again")
    await member.enter()

    print("\nTest 3: Broken turnstile — method raises")
    try:
        await member.enter_broken()
    except RuntimeError as e:
        print(f"  Caught: {e}")

    print("\nTest 4: Confirm entry count is correct after failed entry")
    print(f"  Entry count: {member.entry_count}")

    print("\nTest 5: Normal entry still works after failure")
    await member.enter()

    print("\nTest 6: Confirm decorator preserved method name")
    print(f"  enter name: {member.enter.__name__}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Normal entry
    #   Bob entered. Entries: 1
    #
    # Test 2: Normal entry again
    #   Bob entered. Entries: 2
    #
    # Test 3: Broken turnstile — method raises
    #   Caught: Turnstile jammed
    #
    # Test 4: Confirm entry count is correct after failed entry
    #   Entry count: 2
    #
    # Test 5: Normal entry still works after failure
    #   Bob entered. Entries: 3
    #
    # Test 6: Confirm decorator preserved method name
    #   enter name: enter
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_52())
