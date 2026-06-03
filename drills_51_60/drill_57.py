import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401


async def run_drill_57():
    # =========================================================================
    # SCENARIO: The Command Center
    # =========================================================================
    # A CommandCenter class has a class-level registry that stores method
    # references at definition time. At call time, the correct method is
    # looked up and called via dispatch.
    #
    # REQUIREMENTS:
    #
    # 1. A class CommandCenter:
    #    - REGISTRY = {} at class level (shared across all instances)
    #    - __init__(self, name: str):
    #        - self.name = name
    #        - self.history = []
    #
    # 2. A decorator register(command_name):
    #    - stores the UNBOUND function into CommandCenter.REGISTRY
    #      under command_name as the key
    #    - e.g. CommandCenter.REGISTRY["launch"] = launch  (the raw function)
    #    - return func unchanged
    #    - NOTE: at decoration time the class doesn't exist yet if defined
    #      inside it — define the decorator OUTSIDE the class
    #
    # 3. Three async methods on CommandCenter (you write these):
    #    - async method launch(self):
    #        - decorated with @register("launch")
    #        - appends "launch" to self.history
    #        - prints f"  {self.name}: launch initiated"
    #    - async method abort(self):
    #        - decorated with @register("abort")
    #        - appends "abort" to self.history
    #        - prints f"  {self.name}: abort executed"
    #    - async method status(self):
    #        - decorated with @register("status")
    #        - appends "status" to self.history
    #        - prints f"  {self.name}: all systems nominal"
    #
    # 4. An async method dispatch(self, command_name: str):
    #        - NO decorator
    #        - if command_name not in CommandCenter.REGISTRY,
    #          print f"  Unknown command: {command_name}" and return
    #        - look up the unbound function from REGISTRY
    #        - call it passing self as the first argument and await it
    #          (hint: await CommandCenter.REGISTRY[command_name](self))
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    _TMP_REGISTRY = {}

    def register(command_name: str):
        def decorator(func: Callable) -> Callable:
            _TMP_REGISTRY[command_name] = func
            return func

        return decorator

    class CommandCenter:
        REGISTRY = _TMP_REGISTRY

        def __init__(self, name):
            self.name = name
            self.history = []

        @register("launch")
        async def launch(self):
            self.history.append("launch")
            print(f"  {self.name}: launch initiated")

        @register("abort")
        async def abort(self):
            self.history.append("abort")
            print(f"  {self.name}: abort executed")

        @register("status")
        async def status(self):
            self.history.append("status")
            print(f"  {self.name}: all systems nominal")

        async def dispatch(self, command_name: str):
            if command_name not in CommandCenter.REGISTRY:
                print(f"  Unknown command: {command_name}")
                return
            route = CommandCenter.REGISTRY[command_name]
            return await route(self)

    # --- TESTS (do not modify) ---
    center_a = CommandCenter(name="Alpha")
    center_b = CommandCenter(name="Bravo")

    print("Test 1: Dispatch launch on center A")
    await center_a.dispatch("launch")

    print("\nTest 2: Dispatch status on center A")
    await center_a.dispatch("status")

    print("\nTest 3: Dispatch abort on center B")
    await center_b.dispatch("abort")

    print("\nTest 4: Unknown command")
    await center_a.dispatch("self_destruct")

    print("\nTest 5: Registry is shared — same object for both instances")
    print(f"  Same registry: {center_a.REGISTRY is center_b.REGISTRY}")

    print("\nTest 6: History is per instance")
    print(f"  center_a history: {center_a.history}")
    print(f"  center_b history: {center_b.history}")

    print("\nTest 7: Registry keys")
    print(f"  registered commands: {sorted(CommandCenter.REGISTRY.keys())}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Dispatch launch on center A
    #   Alpha: launch initiated
    #
    # Test 2: Dispatch status on center A
    #   Alpha: all systems nominal
    #
    # Test 3: Dispatch abort on center B
    #   Bravo: abort executed
    #
    # Test 4: Unknown command
    #   Unknown command: self_destruct
    #
    # Test 5: Registry is shared — same object for both instances
    #   Same registry: True
    #
    # Test 6: History is per instance
    #   center_a history: ['launch', 'status']
    #   center_b history: ['abort']
    #
    # Test 7: Registry keys
    #   registered commands: ['abort', 'launch', 'status']
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_57())
