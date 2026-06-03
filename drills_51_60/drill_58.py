import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_58():
    # =========================================================================
    # SCENARIO: The Mission Control
    # =========================================================================
    # A MissionControl class has a class-level registry and a dispatch method.
    # This time, dispatch receives a raw dict payload that must be validated
    # into a Pydantic model before the command runs. If validation fails,
    # raise a custom domain exception instead of letting ValidationError leak.
    #
    # REQUIREMENTS:
    #
    # 1. A Pydantic model MissionPayload:
    #    - target: str
    #    - priority: int
    #
    # 2. A custom exception class InvalidMissionError(Exception):
    #    - no extra logic needed, just define it
    #
    # 3. A class MissionControl:
    #    - REGISTRY = {} at class level
    #    - __init__(self, station: str):
    #        - self.station = station
    #        - self.history = []
    #
    # 4. A decorator register(command_name) defined OUTSIDE the class:
    #    - stores unbound function into MissionControl.REGISTRY
    #    - returns func unchanged
    #
    # 5. Three async methods on MissionControl:
    #    - async method fire(self, payload: MissionPayload):
    #        - decorated with @register("fire")
    #        - appends "fire" to self.history
    #        - prints f"  {self.station}: firing at {payload.target} (priority {payload.priority})"
    #    - async method scan(self, payload: MissionPayload):
    #        - decorated with @register("scan")
    #        - appends "scan" to self.history
    #        - prints f"  {self.station}: scanning {payload.target}"
    #    - async method recall(self, payload: MissionPayload):
    #        - decorated with @register("recall")
    #        - appends "recall" to self.history
    #        - prints f"  {self.station}: recalling from {payload.target}"
    #
    # 6. An async method dispatch(self, command_name: str, raw_payload: dict):
    #    - if command_name not in REGISTRY, print "  Unknown command: <name>" and return
    #    - validate raw_payload into MissionPayload
    #      - if ValidationError, raise InvalidMissionError(str(e))
    #    - call the unbound function passing self and the validated payload
    #    - append command_name to self.history is handled inside each method
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class MissionPayload(BaseModel):
        target: str
        priority: int

    class InvalidMissionError(Exception):
        pass

    _REGISTRY = {}

    def register(command_name):
        def decorator(func: Callable) -> Callable:
            _REGISTRY[command_name] = func
            return func

        return decorator

    class MissionControl:
        REGISTRY = _REGISTRY

        def __init__(self, station: str):
            self.station = station
            self.history = []

        @register("fire")
        async def fire(self, payload: MissionPayload):
            self.history.append("fire")
            print(
                f"  {self.station}: firing at {payload.target} (priority {payload.priority})"
            )

        @register("scan")
        async def scan(self, payload: MissionPayload):
            self.history.append("scan")
            print(f"  {self.station}: scanning {payload.target}")

        @register("recall")
        async def recall(self, payload: MissionPayload):
            self.history.append("recall")
            print(f"  {self.station}: recalling from {payload.target}")

        async def dispatch(self, command_name: str, raw_payload: dict):
            if command_name not in MissionControl.REGISTRY:
                print(f"  Unknown command: {command_name}")
                return
            route = MissionControl.REGISTRY[command_name]
            try:
                validated_payload = MissionPayload(**raw_payload)
            except ValidationError as e:
                raise InvalidMissionError(str(e))
            return await route(self, validated_payload)

    # --- TESTS (do not modify) ---
    station_a = MissionControl(station="Apollo")
    station_b = MissionControl(station="Artemis")

    print("Test 1: Valid fire command")
    await station_a.dispatch("fire", {"target": "Sector 7", "priority": 1})

    print("\nTest 2: Valid scan command")
    await station_a.dispatch("scan", {"target": "Sector 9", "priority": 2})

    print("\nTest 3: Valid recall on station B")
    await station_b.dispatch("recall", {"target": "Base Alpha", "priority": 3})

    print("\nTest 4: Unknown command")
    await station_a.dispatch("self_destruct", {"target": "X", "priority": 0})

    print("\nTest 5: Invalid payload — raises InvalidMissionError")
    try:
        await station_a.dispatch("fire", {"target": "X", "priority": "high"})
    except InvalidMissionError:
        print("  Caught InvalidMissionError")

    print("\nTest 6: Registry is shared")
    print(f"  Same registry: {station_a.REGISTRY is station_b.REGISTRY}")

    print("\nTest 7: History is per instance")
    print(f"  station_a history: {station_a.history}")
    print(f"  station_b history: {station_b.history}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid fire command
    #   Apollo: firing at Sector 7 (priority 1)
    #
    # Test 2: Valid scan command
    #   Apollo: scanning Sector 9
    #
    # Test 3: Valid recall on station B
    #   Artemis: recalling from Base Alpha
    #
    # Test 4: Unknown command
    #   Unknown command: self_destruct
    #
    # Test 5: Invalid payload — raises InvalidMissionError
    #   Caught InvalidMissionError
    #
    # Test 6: Registry is shared
    #   Same registry: True
    #
    # Test 7: History is per instance
    #   station_a history: ['fire', 'scan']
    #   station_b history: ['recall']
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_58())
