import asyncio  # noqa: F401
import inspect  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_56():
    # =========================================================================
    # SCENARIO: The Smart Home
    # =========================================================================
    # A SmartHome class has both sync and async methods. A single decorator
    # must work on BOTH — without breaking either. The key is checking whether
    # the wrapped function is a coroutine function before deciding how to call it.
    #
    # REQUIREMENTS:
    #
    # 1. A decorator log_call(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - appends func.__name__ to instance.history BEFORE calling func
    #    - checks if func is a coroutine function using inspect.iscoroutinefunction
    #      - if YES: the wrapper must be async, await func(*args, **kwargs)
    #      - if NO: the wrapper must be sync, call func(*args, **kwargs) normally
    #    - returns the result in both branches
    #    - NOTE: you cannot have one wrapper that is both sync and async
    #      you must return a different wrapper depending on which branch
    #
    # 2. A class SmartHome:
    #    - __init__(self, name: str):
    #        - self.name = name
    #        - self.history = []
    #    - sync method get_status(self) -> str:
    #        - decorated with @log_call
    #        - returns f"{self.name} is online"
    #    - async method turn_on_lights(self):
    #        - decorated with @log_call
    #        - prints f"  Lights on in {self.name}"
    #    - async method turn_off_lights(self):
    #        - decorated with @log_call
    #        - prints f"  Lights off in {self.name}"
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    def log_call(func):
        def pre_call(instance):
            instance.history.append(func.__name__)

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                pre_call(args[0])
                return await func(*args, **kwargs)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                pre_call(args[0])
                return func(*args, **kwargs)

            return sync_wrapper

    class SmartHome:
        def __init__(self, name: str):
            self.name = name
            self.history = []

        @log_call
        def get_status(self) -> str:
            return f"{self.name} is online"

        @log_call
        async def turn_on_lights(self):
            print(f"  Lights on in {self.name}")

        @log_call
        async def turn_off_lights(self):
            print(f"  Lights off in {self.name}")

    # --- TESTS (do not modify) ---
    home = SmartHome(name="Beach House")

    print("Test 1: Call sync method")
    status = home.get_status()
    print(f"  Status: {status}")

    print("\nTest 2: Call async method")
    await home.turn_on_lights()

    print("\nTest 3: Call another async method")
    await home.turn_off_lights()

    print("\nTest 4: Check history — all calls logged")
    print(f"  history: {home.history}")

    print("\nTest 5: Confirm sync method is still sync")
    print(f"  get_status is coroutine: {inspect.iscoroutinefunction(home.get_status)}")

    print("\nTest 6: Confirm async method is still async")
    print(
        f"  turn_on_lights is coroutine: {inspect.iscoroutinefunction(home.turn_on_lights)}"
    )

    print("\nTest 7: Confirm decorator preserved method names")
    print(f"  get_status name: {home.get_status.__name__}")
    print(f"  turn_on_lights name: {home.turn_on_lights.__name__}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Call sync method
    #   Status: Beach House is online
    #
    # Test 2: Call async method
    #   Lights on in Beach House
    #
    # Test 3: Call another async method
    #   Lights off in Beach House
    #
    # Test 4: Check history — all calls logged
    #   history: ['get_status', 'turn_on_lights', 'turn_off_lights']
    #
    # Test 5: Confirm sync method is still sync
    #   get_status is coroutine: False
    #
    # Test 6: Confirm async method is still async
    #   turn_on_lights is coroutine: True
    #
    # Test 7: Confirm decorator preserved method names
    #   get_status name: get_status
    #   turn_on_lights name: turn_on_lights
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_56())
