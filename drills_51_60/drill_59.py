import asyncio  # noqa: F401
import inspect  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_59():
    # =========================================================================
    # SCENARIO: The Space Station
    # =========================================================================
    # A SpaceStation class combines everything from drills 51-58:
    # - A decorator that reads self.state and blocks if not ready (drill 51)
    # - try/finally to guarantee state reset (drill 53)
    # - sync + async branch in one decorator (drill 56)
    # - class-level registry with unbound functions (drill 57)
    # - Pydantic validation + domain exception in dispatch (drill 58)
    #
    # REQUIREMENTS:
    #
    # 1. A Pydantic model MissionData:
    #    - destination: str
    #    - crew_size: int
    #
    # 2. A custom exception InvalidMissionDataError(Exception)
    #
    # 3. A decorator require_ready(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - if instance.ready is False:
    #        print "  Station not ready" and return None
    #    - sets instance.busy = True before calling
    #    - uses try/finally to reset instance.busy = False after
    #    - handles both sync and async methods via inspect.iscoroutinefunction
    #
    # 4. A class SpaceStation:
    #    - REGISTRY = {} at class level
    #    - __init__(self, name: str):
    #        - self.name = name
    #        - self.ready = False
    #        - self.busy = False
    #        - self.history = []
    #    - sync method activate(self):
    #        - NO decorator
    #        - sets self.ready = True
    #        - prints f"  {self.name} activated"
    #    - async method launch(self, data: MissionData):
    #        - decorated with @register("launch") AND @require_ready
    #        - appends "launch" to self.history
    #        - prints f"  {self.name}: launching to {data.destination} with {data.crew_size} crew"
    #    - async method abort(self, data: MissionData):
    #        - decorated with @register("abort") AND @require_ready
    #        - appends "abort" to self.history
    #        - prints f"  {self.name}: aborting mission to {data.destination}"
    #    - async method dispatch(self, command_name: str, raw_payload: dict):
    #        - NO decorator
    #        - if command not found, print "  Unknown command: <name>" and return
    #        - validate raw_payload into MissionData
    #          - if ValidationError, raise InvalidMissionDataError(str(e))
    #        - call unbound function passing self and validated data
    #
    # 5. A decorator register(command_name) defined OUTSIDE the class:
    #    - stores unbound function into SpaceStation.REGISTRY
    #    - returns func unchanged
    #
    # NOTE: decorator order matters —
    #   @register("launch")
    #   @require_ready
    #   async def launch(self, data):
    #   This means require_ready wraps launch first, then register stores
    #   the already-wrapped function. So dispatch calls require_ready automatically.
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class MissionData(BaseModel):
        destination: str
        crew_size: int

    class InvalidMissionDataError(Exception):
        pass

    def require_ready(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                instance = args[0]
                if instance.ready is False:
                    print("  Station not ready")
                    return None
                instance.busy = True
                try:
                    result = await func(*args, **kwargs)
                finally:
                    instance.busy = False
                return result

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                instance = args[0]
                if instance.ready is False:
                    print("  Station not ready")
                    return None
                instance.busy = True
                try:
                    result = func(*args, **kwargs)
                finally:
                    instance.busy = False
                return result

            return sync_wrapper

    _REGISTRY = {}

    def register(command_name):
        def decorator(func: Callable) -> Callable:
            _REGISTRY[command_name] = func
            return func

        return decorator

    class SpaceStation:
        REGISTRY = _REGISTRY

        def __init__(self, name: str):
            self.name = name
            self.ready = False
            self.busy = False
            self.history = []

        def activate(self):
            self.ready = True
            print(f"  {self.name} activated")

        @register(command_name="launch")
        @require_ready
        async def launch(self, data: MissionData):
            self.history.append("launch")
            print(
                f"  {self.name}: launching to {data.destination} with {data.crew_size} crew"
            )

        @register(command_name="abort")
        @require_ready
        async def abort(self, data: MissionData):
            self.history.append("abort")
            print(f"  {self.name}: aborting mission to {data.destination}")

        async def dispatch(self, command_name: str, raw_payload: dict):
            if command_name not in SpaceStation.REGISTRY:
                print(f"  Unknown command: {command_name}")
                return
            route = SpaceStation.REGISTRY[command_name]
            try:
                validated_payload = MissionData(**raw_payload)
            except ValidationError as e:
                raise InvalidMissionDataError(str(e))
            return await route(self, validated_payload)

    # --- TESTS (do not modify) ---
    station_a = SpaceStation(name="Orion")
    station_b = SpaceStation(name="Pegasus")

    print("Test 1: Launch before activation — blocked")
    await station_a.dispatch("launch", {"destination": "Mars", "crew_size": 4})

    print("\nTest 2: Activate station A")
    station_a.activate()

    print("\nTest 3: Launch after activation")
    await station_a.dispatch("launch", {"destination": "Mars", "crew_size": 4})

    print("\nTest 4: Abort on station A")
    await station_a.dispatch("abort", {"destination": "Mars", "crew_size": 4})

    print("\nTest 5: Station B still not ready")
    await station_b.dispatch("launch", {"destination": "Venus", "crew_size": 2})

    print("\nTest 6: Invalid payload")
    try:
        await station_a.dispatch("launch", {"destination": "Mars", "crew_size": "four"})
    except InvalidMissionDataError:
        print("  Caught InvalidMissionDataError")

    print("\nTest 7: Unknown command")
    await station_a.dispatch("self_destruct", {"destination": "X", "crew_size": 1})

    print("\nTest 8: busy resets after method completes")
    print(f"  station_a busy: {station_a.busy}")

    print("\nTest 9: Registry is shared")
    print(f"  Same registry: {station_a.REGISTRY is station_b.REGISTRY}")

    print("\nTest 10: History is per instance")
    print(f"  station_a history: {station_a.history}")
    print(f"  station_b history: {station_b.history}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Launch before activation — blocked
    #   Station not ready
    #
    # Test 2: Activate station A
    #   Orion activated
    #
    # Test 3: Launch after activation
    #   Orion: launching to Mars with 4 crew
    #
    # Test 4: Abort on station A
    #   Orion: aborting mission to Mars
    #
    # Test 5: Station B still not ready
    #   Station not ready
    #
    # Test 6: Invalid payload
    #   Caught InvalidMissionDataError
    #
    # Test 7: Unknown command
    #   Unknown command: self_destruct
    #
    # Test 8: busy resets after method completes
    #   station_a busy: False
    #
    # Test 9: Registry is shared
    #   Same registry: True
    #
    # Test 10: History is per instance
    #   station_a history: ['launch', 'abort']
    #   station_b history: []
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_59())
