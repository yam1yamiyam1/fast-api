# drill_83.py
import asyncio
from dataclasses import dataclass
from typing import Any, Callable  # noqa: F401


async def run_drill_83():
    """
    Scenario: Shipping Port
    A shipping port processes cargo manifests through a validation pipeline.
    Each cargo type has a registered inspector. The system enforces a concurrency
    limit so no more than 2 inspections run simultaneously.

    Requirements:
    - InspectorEntry dataclass: cargo_type (str), inspector (Callable).
      No mutable defaults.
    - PortRegistry class:
        - Internal dict named entries, initialized safely.
        - register(cargo_type, inspector) — stores entry in entries by cargo_type key.
        - get(cargo_type) — returns the InspectorEntry, raises
          ValueError("unknown cargo") if not found.
        - inspect_cargo(cargo_type, manifest, semaphore) — pipeline:
            1. Use async with semaphore to bound the block below.
            2. Look up the entry via get().
            3. Call inspector(manifest) — sync or async, handle both.
            4. Return inspector result.
    - run_port(registry, jobs) — accepts a PortRegistry and a list of (cargo_type, manifest) tuples.
        - Creates a single asyncio.Semaphore(2).
        - Launches all jobs concurrently via asyncio.create_task.
        - Awaits all tasks and returns results as a list, in original job order.
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class InspectorEntry:
        cargo_type: str
        inspector: Callable

    class PortRegistry:
        def __init__(self):
            self.entries = {}

        def register(self, cargo_type, inspector):
            self.entries[cargo_type] = InspectorEntry(cargo_type, inspector)

        def get(self, cargo_type):
            if cargo_type not in self.entries:
                raise ValueError("unknown cargo")
            return self.entries[cargo_type]

    # Tests
    active = 0
    peak = 0

    async def track(manifest):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return f"cleared:{manifest}"

    def sync_inspector(manifest):
        return f"sync:{manifest}"

    registry = PortRegistry()
    registry.register("electronics", track)
    registry.register("perishables", track)
    registry.register("chemicals", sync_inspector)

    print("Test 1: get returns correct entry")
    entry = registry.get("electronics")
    assert entry.cargo_type == "electronics", entry
    print(f"  cargo_type: {entry.cargo_type}")
    print("  PASS")

    print("Test 2: unknown cargo raises ValueError")
    try:
        registry.get("weapons")
        assert False, "should have raised"
    except ValueError as e:
        assert str(e) == "unknown cargo", str(e)
        print(f"  error: {e}")
        print("  PASS")

    print("Test 3: sync inspector works")
    sem = asyncio.Semaphore(2)
    result = await registry.inspect_cargo("chemicals", "barrel-99", sem)
    assert result == "sync:barrel-99", result
    print(f"  result: {result}")
    print("  PASS")

    print("Test 4: async inspector works")
    sem = asyncio.Semaphore(2)
    result = await registry.inspect_cargo("electronics", "crate-7", sem)
    assert result == "cleared:crate-7", result
    print(f"  result: {result}")
    print("  PASS")

    print("Test 5: run_port returns results in order")
    jobs = [
        ("electronics", "box-1"),
        ("perishables", "box-2"),
        ("electronics", "box-3"),
    ]
    results = await run_port(registry, jobs)
    assert results == ["cleared:box-1", "cleared:box-2", "cleared:box-3"], results
    print(f"  results: {results}")
    print("  PASS")

    print("Test 6: concurrency capped at 2")
    active = 0
    peak = 0
    jobs = [("electronics", f"m{i}") for i in range(5)]
    await run_port(registry, jobs)
    assert peak <= 2, f"peak was {peak}"
    print(f"  peak concurrency: {peak}")
    print("  PASS")

    print("Test 7: two registries are independent")
    r2 = PortRegistry()
    r2.register("timber", sync_inspector)
    assert "timber" not in registry.entries
    assert len(r2.entries) == 1
    print(f"  r2 entries: {list(r2.entries.keys())}")
    print("  PASS")


asyncio.run(run_drill_83())


# Expected output:
# Test 1: get returns correct entry
#   cargo_type: electronics
#   PASS
# Test 2: unknown cargo raises ValueError
#   error: unknown cargo
#   PASS
# Test 3: sync inspector works
#   result: sync:barrel-99
#   PASS
# Test 4: async inspector works
#   result: cleared:crate-7
#   PASS
# Test 5: run_port returns results in order
#   results: ['cleared:box-1', 'cleared:box-2', 'cleared:box-3']
#   PASS
# Test 6: concurrency capped at 2
#   peak concurrency: 2
#   PASS
# Test 7: two registries are independent
#   r2 entries: ['timber']
#   PASS
