import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_55():
    # =========================================================================
    # SCENARIO: The Security System
    # =========================================================================
    # A SecuritySystem class keeps a log of every method call made on it.
    # A decorator handles logging automatically — appending an entry to
    # self.history every time a decorated method is called.
    #
    # REQUIREMENTS:
    #
    # 1. A decorator log_action(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - appends func.__name__ to instance.history BEFORE calling func
    #    - calls and awaits func normally
    #    - returns the result
    #
    # 2. A class SecuritySystem:
    #    - __init__(self, location: str):
    #        - self.location = location
    #        - self.history = []
    #        - self.armed = False
    #    - async method arm(self):
    #        - decorated with @log_action
    #        - sets self.armed = True
    #        - prints f"  {self.location} armed"
    #    - async method disarm(self):
    #        - decorated with @log_action
    #        - sets self.armed = False
    #        - prints f"  {self.location} disarmed"
    #    - async method trigger_alarm(self):
    #        - decorated with @log_action
    #        - prints f"  ALARM at {self.location}!"
    #
    # CRITICAL:
    #    - self.history must be defined in __init__ as self.history = []
    #    - NOT as a class-level attribute HISTORY = []
    #    - if defined at class level, ALL instances share the same list
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    def log_action(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            instance = args[0]
            instance.history.append(func.__name__)
            result = await func(*args, **kwargs)
            return result

        return wrapper

    class SecuritySystem:
        def __init__(self, location):
            self.location = location
            self.history = []
            self.armed = False

        @log_action
        async def arm(self):
            self.armed = True
            print(f"  {self.location} armed")

        @log_action
        async def disarm(self):
            self.armed = False
            print(f"  {self.location} disarmed")

        @log_action
        async def trigger_alarm(self):
            print(f"  ALARM at {self.location}!")

    # --- TESTS (do not modify) ---
    system_a = SecuritySystem(location="Front Door")
    system_b = SecuritySystem(location="Back Door")

    print("Test 1: Arm system A")
    await system_a.arm()

    print("\nTest 2: Trigger alarm on system A")
    await system_a.trigger_alarm()

    print("\nTest 3: Arm system B")
    await system_b.arm()

    print("\nTest 4: Disarm system A")
    await system_a.disarm()

    print("\nTest 5: Check history — per instance, not shared")
    print(f"  system_a history: {system_a.history}")
    print(f"  system_b history: {system_b.history}")

    print("\nTest 6: Confirm histories are independent objects")
    print(f"  Same list object: {system_a.history is system_b.history}")

    print("\nTest 7: Confirm decorator preserved method names")
    print(f"  arm name: {system_a.arm.__name__}")
    print(f"  disarm name: {system_a.disarm.__name__}")
    print(f"  trigger_alarm name: {system_a.trigger_alarm.__name__}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Arm system A
    #   Front Door armed
    #
    # Test 2: Trigger alarm on system A
    #   ALARM at Front Door!
    #
    # Test 3: Arm system B
    #   Back Door armed
    #
    # Test 4: Disarm system A
    #   Front Door disarmed
    #
    # Test 5: Check history — per instance, not shared
    #   system_a history: ['arm', 'trigger_alarm', 'disarm']
    #   system_b history: ['arm']
    #
    # Test 6: Confirm histories are independent objects
    #   Same list object: False
    #
    # Test 7: Confirm decorator preserved method names
    #   arm name: arm
    #   disarm name: disarm
    #   trigger_alarm name: trigger_alarm
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_55())
