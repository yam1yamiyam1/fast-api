import asyncio  # noqa: F401
import inspect  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_60():
    # =========================================================================
    # SCENARIO: The Nuclear Plant
    # =========================================================================
    # Final boss. No new concepts. You combine everything from drills 51-59
    # into one system from a blank page.
    #
    # REQUIREMENTS:
    #
    # 1. A Pydantic model ReactorCommand:
    #    - zone: str
    #    - power_level: int
    #
    # 2. A custom exception InvalidCommandError(Exception)
    #
    # 3. A decorator require_online(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - if instance.online is False, print "  Reactor offline" and return None
    #    - sets instance.operating = True before calling
    #    - uses try/finally to reset instance.operating = False after
    #    - handles both sync and async via inspect.iscoroutinefunction
    #
    # 4. A decorator register(command_name) defined OUTSIDE the class:
    #    - stores unbound function into NuclearPlant.REGISTRY
    #    - returns func unchanged
    #
    # 5. A class NuclearPlant:
    #    - REGISTRY = {} at class level
    #    - __init__(self, plant_id: str):
    #        - self.plant_id = plant_id
    #        - self.online = False
    #        - self.operating = False
    #        - self.history = []
    #        - self.audit_log = []
    #    - sync method boot(self):
    #        - NO decorator
    #        - sets self.online = True
    #        - prints f"  Plant {self.plant_id} online"
    #    - sync method get_status(self) -> str:
    #        - decorated with @require_online
    #        - appends "get_status" to self.history
    #        - returns f"Plant {self.plant_id}: online={self.online}"
    #    - async method increase_power(self, cmd: ReactorCommand):
    #        - decorated with @register("increase_power") AND @require_online
    #        - appends "increase_power" to self.history
    #        - appends f"increase:{cmd.zone}:{cmd.power_level}" to self.audit_log
    #        - prints f"  {self.plant_id}: increasing power in {cmd.zone} to {cmd.power_level}%"
    #    - async method reduce_power(self, cmd: ReactorCommand):
    #        - decorated with @register("reduce_power") AND @require_online
    #        - appends "reduce_power" to self.history
    #        - appends f"reduce:{cmd.zone}:{cmd.power_level}" to self.audit_log
    #        - prints f"  {self.plant_id}: reducing power in {cmd.zone} to {cmd.power_level}%"
    #    - async method emergency_shutdown(self, cmd: ReactorCommand):
    #        - decorated with @register("emergency_shutdown") AND @require_online
    #        - appends "emergency_shutdown" to self.history
    #        - appends f"shutdown:{cmd.zone}" to self.audit_log
    #        - sets self.online = False
    #        - prints f"  {self.plant_id}: EMERGENCY SHUTDOWN in {cmd.zone}"
    #    - async method dispatch(self, command_name: str, raw_payload: dict):
    #        - NO decorator
    #        - if command not found, print "  Unknown command: <name>" and return
    #        - validate raw_payload into ReactorCommand
    #          - if ValidationError, raise InvalidCommandError(str(e))
    #        - call unbound function passing self and validated command
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class ReactorCommand(BaseModel):
        zone: str
        power_level: int

    class InvalidCommandError(Exception):
        pass

    def require_online(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                instance = args[0]
                if instance.online is False:
                    print("  Reactor offline")
                    return None
                instance.operating = True
                try:
                    result = await func(*args, **kwargs)
                finally:
                    instance.operating = False
                return result

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                instance = args[0]
                if instance.online is False:
                    print("  Reactor offline")
                    return None
                instance.operating = True
                try:
                    result = func(*args, **kwargs)
                finally:
                    instance.operating = False
                return result

            return sync_wrapper

    _REGISTRY = {}

    def register(command_name):
        def decorator(func: Callable) -> Callable:
            _REGISTRY[command_name] = func
            return func

        return decorator

    class NuclearPlant:
        REGISTRY = _REGISTRY

        def __init__(self, plant_id: str):
            self.plant_id = plant_id
            self.online = False
            self.operating = False
            self.history = []
            self.audit_log = []

        def boot(self):
            self.online = True
            print(f"  Plant {self.plant_id} online")

        @require_online
        def get_status(self) -> str:
            self.history.append("get_status")
            return f"Plant {self.plant_id}: online={self.online}"

        @register("increase_power")
        @require_online
        async def increase_power(self, cmd: ReactorCommand):
            self.history.append("increase_power")
            self.audit_log.append(f"increase:{cmd.zone}:{cmd.power_level}")
            print(
                f"  {self.plant_id}: increasing power in {cmd.zone} to {cmd.power_level}%"
            )

        @register("reduce_power")
        @require_online
        async def reduce_power(self, cmd: ReactorCommand):
            self.history.append("reduce_power")
            self.audit_log.append(f"reduce:{cmd.zone}:{cmd.power_level}")
            print(
                f"  {self.plant_id}: reducing power in {cmd.zone} to {cmd.power_level}%"
            )

        @register("emergency_shutdown")
        @require_online
        async def emergency_shutdown(self, cmd: ReactorCommand):
            self.history.append("emergency_shutdown")
            self.audit_log.append(f"shutdown:{cmd.zone}")
            print(f"  {self.plant_id}: EMERGENCY SHUTDOWN in {cmd.zone}")
            self.online = False

        async def dispatch(self, command_name: str, raw_payload: dict):
            if command_name not in NuclearPlant.REGISTRY:
                print(f"  Unknown command: {command_name}")
                return
            route = NuclearPlant.REGISTRY[command_name]
            try:
                validated_payload = ReactorCommand(**raw_payload)
            except ValidationError as e:
                raise InvalidCommandError(str(e))

            return await route(self, validated_payload)

    # --- TESTS (do not modify) ---
    plant_a = NuclearPlant(plant_id="A1")
    plant_b = NuclearPlant(plant_id="B2")

    print("Test 1: Command before boot — blocked")
    await plant_a.dispatch("increase_power", {"zone": "Core-1", "power_level": 80})

    print("\nTest 2: Boot plant A")
    plant_a.boot()

    print("\nTest 3: Get status (sync method with decorator)")
    status = plant_a.get_status()
    print(f"  Status: {status}")

    print("\nTest 4: Increase power")
    await plant_a.dispatch("increase_power", {"zone": "Core-1", "power_level": 80})

    print("\nTest 5: Reduce power")
    await plant_a.dispatch("reduce_power", {"zone": "Core-2", "power_level": 40})

    print("\nTest 6: Plant B still offline")
    await plant_b.dispatch("increase_power", {"zone": "Core-1", "power_level": 50})

    print("\nTest 7: Invalid payload")
    try:
        await plant_a.dispatch(
            "increase_power", {"zone": "Core-1", "power_level": "max"}
        )
    except InvalidCommandError:
        print("  Caught InvalidCommandError")

    print("\nTest 8: Unknown command")
    await plant_a.dispatch("explode", {"zone": "Core-1", "power_level": 100})

    print("\nTest 9: Emergency shutdown")
    await plant_a.dispatch("emergency_shutdown", {"zone": "Core-1", "power_level": 0})

    print("\nTest 10: Command after shutdown — blocked")
    await plant_a.dispatch("increase_power", {"zone": "Core-1", "power_level": 80})

    print("\nTest 11: operating resets correctly")
    print(f"  plant_a operating: {plant_a.operating}")

    print("\nTest 12: Registry is shared")
    print(f"  Same registry: {plant_a.REGISTRY is plant_b.REGISTRY}")

    print("\nTest 13: History is per instance")
    print(f"  plant_a history: {plant_a.history}")
    print(f"  plant_b history: {plant_b.history}")

    print("\nTest 14: Audit log is per instance")
    print(f"  plant_a audit_log: {plant_a.audit_log}")
    print(f"  plant_b audit_log: {plant_b.audit_log}")

    print("\nTest 15: Confirm decorator preserved method names")
    print(f"  increase_power name: {plant_a.increase_power.__name__}")
    print(f"  get_status name: {plant_a.get_status.__name__}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Command before boot — blocked
    #   Reactor offline
    #
    # Test 2: Boot plant A
    #   Plant A1 online
    #
    # Test 3: Get status (sync method with decorator)
    #   Status: Plant A1: online=True
    #
    # Test 4: Increase power
    #   A1: increasing power in Core-1 to 80%
    #
    # Test 5: Reduce power
    #   A1: reducing power in Core-2 to 40%
    #
    # Test 6: Plant B still offline
    #   Reactor offline
    #
    # Test 7: Invalid payload
    #   Caught InvalidCommandError
    #
    # Test 8: Unknown command
    #   Unknown command: explode
    #
    # Test 9: Emergency shutdown
    #   A1: EMERGENCY SHUTDOWN in Core-1
    #
    # Test 10: Command after shutdown — blocked
    #   Reactor offline
    #
    # Test 11: operating resets correctly
    #   plant_a operating: False
    #
    # Test 12: Registry is shared
    #   Same registry: True
    #
    # Test 13: History is per instance
    #   plant_a history: ['get_status', 'increase_power', 'reduce_power', 'emergency_shutdown']
    #   plant_b history: []
    #
    # Test 14: Audit log is per instance
    #   plant_a audit_log: ['increase:Core-1:80', 'reduce:Core-2:40', 'shutdown:Core-1']
    #   plant_b audit_log: []
    #
    # Test 15: Confirm decorator preserved method names
    #   increase_power name: increase_power
    #   get_status name: get_status
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_60())
