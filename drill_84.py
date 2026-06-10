import asyncio  # noqa: F401
from typing import Any, Optional  # noqa: F401


def run_drill_84():
    """
    SCENARIO: Shipping Port
    =======================
    A shipping port must open its gates before cargo can move and close
    them cleanly when operations end. The port lifecycle is managed by a
    context manager — gates open on enter, manifest is cleared on exit.
    While the port is open, vessels can dock and log their cargo.

    NEW CONCEPT: Async context manager (class-based)
    -------------------------------------------------
    A class becomes an async context manager by implementing two methods:
      async def __aenter__(self)  — runs on  `async with port as p:`
      async def __aexit__(self, exc_type, exc_val, exc_tb)  — runs on block exit
    Use `async with` to enter; the value returned by __aenter__ is bound
    to the `as` target. __aexit__ receives exception info (all None if clean).
    Rule: never use plain `with` for an async context manager — always `async with`.

    REQUIREMENTS
    ============

    1. PortManifest
       - A class representing the running cargo log kept at the gate.
       - __init__(self):
           - self.entries: list — the list of cargo strings logged during
             the session; initialised as an empty list using = [], never
             a type annotation alone.
           - self.is_open: bool — whether the port gates are currently open;
             initialised to False using = False, never a type annotation alone.
       - async def open_gates(self) -> None
           - Sets self.is_open to True. No return value.
       - async def close_gates(self) -> None
           - Sets self.is_open to False and clears self.entries to [].
             No return value.
       - def log(self, cargo: str) -> None
           - cargo: str — a description of the goods being recorded at the gate.
           - Appends cargo to self.entries only if self.is_open is True.
             Does nothing if gates are closed.

    2. Port
       - A class that wraps PortManifest as an async context manager.
       - __init__(self):
           - self.manifest: Optional[PortManifest] — the manifest instance
             used during this session; initialised to None using = None,
             never a type annotation alone.
       - async def __aenter__(self) -> PortManifest
           - Creates a new PortManifest, assigns it to self.manifest,
             calls await self.manifest.open_gates(), then returns self.manifest.
       - async def __aexit__(self, exc_type, exc_val, exc_tb) -> None
           - Calls await self.manifest.close_gates(). No return value.

    TESTS
    =====
    """

    # --- YOUR CODE HERE ---

    async def main():
        # Test 1: gates open on __aenter__, manifest returned as context value
        port = Port()
        async with port as manifest:
            print("Test 1: gates open inside context")
            print(f"  is_open={manifest.is_open}")
            assert manifest.is_open is True
            print("  PASS")

        # Test 2: gates close and entries cleared on __aexit__
        print("Test 2: gates closed after context exits")
        print(f"  is_open={manifest.is_open}")
        print(f"  entries={manifest.entries}")
        assert manifest.is_open is False
        assert manifest.entries == []
        print("  PASS")

        # Test 3: log() records cargo while open
        async with Port() as manifest2:
            manifest2.log("steel coils")
            manifest2.log("timber")
            print("Test 3: cargo logged while open")
            print(f"  entries={manifest2.entries}")
            assert manifest2.entries == ["steel coils", "timber"]
            print("  PASS")

        # Test 4: log() ignored when gates are closed
        manifest2.log("contraband")
        print("Test 4: log ignored after gates close")
        print(f"  entries={manifest2.entries}")
        assert manifest2.entries == []
        print("  PASS")

        # Test 5: entries default not shared between PortManifest instances
        m1 = PortManifest()
        m2 = PortManifest()
        m1.entries.append("container A")
        print("Test 5: entries mutable default isolation")
        print(f"  m1.entries={m1.entries}")
        print(f"  m2.entries={m2.entries}")
        assert m1.entries == ["container A"]
        assert m2.entries == []
        print("  PASS")

        # Test 6: each Port session gets a fresh manifest
        port2 = Port()
        async with port2 as m3:
            m3.log("grain")
        async with port2 as m4:
            print("Test 6: fresh manifest on each session")
            print(f"  m4.entries={m4.entries}")
            assert m4.entries == []
            print("  PASS")

    asyncio.run(main())


run_drill_84()


# EXPECTED OUTPUT
# ===============
# Test 1: gates open inside context
#   is_open=True
#   PASS
# Test 2: gates closed after context exits
#   is_open=False
#   entries=[]
#   PASS
# Test 3: cargo logged while open
#   entries=['steel coils', 'timber']
#   PASS
# Test 4: log ignored after gates close
#   entries=[]
#   PASS
# Test 5: entries mutable default isolation
#   m1.entries=['container A']
#   m2.entries=[]
#   PASS
# Test 6: fresh manifest on each session
#   m4.entries=[]
#   PASS
