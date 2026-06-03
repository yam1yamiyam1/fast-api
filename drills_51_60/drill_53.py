import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_53():
    # =========================================================================
    # SCENARIO: The Operating Room
    # =========================================================================
    # A Surgery class tracks whether an operation is in progress via
    # self.in_progress. A decorator sets in_progress = True before the
    # method runs and MUST reset it to False after — even if the method
    # raises. This is the exact problem try/finally solves.
    #
    # REQUIREMENTS:
    #
    # 1. A decorator operation(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - sets instance.in_progress = True BEFORE calling func
    #    - uses try/finally to GUARANTEE instance.in_progress = False after
    #      (whether func succeeds or raises)
    #    - calls and awaits func inside the try block
    #
    # 2. A class Surgery:
    #    - __init__(self, patient: str):
    #        - self.patient = patient
    #        - self.in_progress = False
    #    - async method perform(self):
    #        - decorated with @operation
    #        - prints f"  Operating on {self.patient}"
    #    - async method perform_broken(self):
    #        - decorated with @operation
    #        - raises RuntimeError("Power outage")
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    def operation(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            instance = args[0]
            instance.in_progress = True
            try:
                await func(*args, **kwargs)
            finally:
                instance.in_progress = False

        return wrapper

    class Surgery:
        def __init__(self, patient: str):
            self.patient = patient
            self.in_progress = False

        @operation
        async def perform(self):
            print(f"  Operating on {self.patient}")

        @operation
        async def perform_broken(self):
            raise RuntimeError("Power outage")

    # --- TESTS (do not modify) ---
    surgery = Surgery(patient="Alice")

    print("Test 1: Check initial state")
    print(f"  in_progress: {surgery.in_progress}")

    print("\nTest 2: Perform surgery")
    await surgery.perform()

    print("\nTest 3: Check state after successful surgery")
    print(f"  in_progress: {surgery.in_progress}")

    print("\nTest 4: Perform broken surgery")
    try:
        await surgery.perform_broken()
    except RuntimeError as e:
        print(f"  Caught: {e}")

    print("\nTest 5: Confirm state reset even after failure")
    print(f"  in_progress: {surgery.in_progress}")

    print("\nTest 6: Perform surgery again — still works")
    await surgery.perform()

    print("\nTest 7: Confirm decorator preserved method name")
    print(f"  perform name: {surgery.perform.__name__}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Check initial state
    #   in_progress: False
    #
    # Test 2: Perform surgery
    #   Operating on Alice
    #
    # Test 3: Check state after successful surgery
    #   in_progress: False
    #
    # Test 4: Perform broken surgery
    #   Caught: Power outage
    #
    # Test 5: Confirm state reset even after failure
    #   in_progress: False
    #
    # Test 6: Perform surgery again — still works
    #   Operating on Alice
    #
    # Test 7: Confirm decorator preserved method name
    #   perform name: perform
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_53())
