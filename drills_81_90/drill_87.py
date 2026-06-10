import asyncio  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401
from dataclasses import dataclass, field  # noqa: F401
from typing import Any, AsyncGenerator, Callable, Optional  # noqa: F401


def run_drill_87():
    """
    SCENARIO: Embassy Visa Processing
    ==================================
    The embassy opens a processing session when an officer sits down and
    closes it when they leave. While the session is open, visa applications
    can be stamped. The session lifecycle is managed with a generator-based
    async context manager — setup before yield, teardown after.

    NEW CONCEPT: @asynccontextmanager
    ----------------------------------
    Decorating an async generator function with @asynccontextmanager turns
    it into an async context manager without writing a class.
    Pattern:
        @asynccontextmanager
        async def my_ctx(args) -> AsyncGenerator[YieldType, None]:
            # setup
            yield value        ← bound to `as` target
            # teardown
    Rule: exactly one yield. Everything before yield is __aenter__,
    everything after is __aexit__. Use `async with` to enter.

    REQUIREMENTS
    ============

    1. SessionLog
       - A dataclass representing the visa officer's active session record.
       - officer: str — the name of the officer who opened this session.
       - stamps: list — the list of visa application IDs stamped during
         the session; must use field(default_factory=list), never a
         mutable default.
       - is_active: bool — whether this session is currently open;
         default value False, written as a plain assignment in the
         dataclass field, not as a type annotation alone.

    2. EmbassyState
       - A class representing the embassy's shared runtime state.
       - __init__(self):
           - self.active_sessions: list — the list of currently open
             SessionLog objects; initialised as an empty list using
             = [], never a type annotation alone.
           - self.closed_count: int — the number of sessions that have
             been closed since startup; initialised to 0 using = 0,
             never a type annotation alone.
       - def open_session(self, log: SessionLog) -> None
           - log: SessionLog — the session record being opened.
           - Sets log.is_active to True and appends log to
             self.active_sessions.
       - def close_session(self, log: SessionLog) -> None
           - log: SessionLog — the session record being closed.
           - Sets log.is_active to False, removes log from
             self.active_sessions, and increments self.closed_count by 1.

    3. visa_session  (async context manager function, not a method)
       @asynccontextmanager
       async def visa_session(state: EmbassyState, officer: str)
                              -> AsyncGenerator[SessionLog, None]
           - state: EmbassyState — the embassy's shared state to update.
           - officer: str — the name of the officer opening the session.
           - Before yield: create a SessionLog(officer=officer), call
             state.open_session(log), then yield the log.
           - After yield: call state.close_session(log).

    TESTS
    =====
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class SessionLog:
        officer: str
        stamps: list = field(default_factory=list)
        is_active: bool = False

    class EmbassyState:
        def __init__(self):
            self.active_sessions = []
            self.closed_count = 0

        def open_session(self, log: SessionLog):
            log.is_active = True
            self.active_sessions.append(log)

        def close_session(self, log: SessionLog):
            log.is_active = False
            self.active_sessions.remove(log)
            self.closed_count += 1

    @asynccontextmanager
    async def visa_session(state: EmbassyState, officer: str):
        log = SessionLog(officer=officer)
        state.open_session(log)
        yield log
        state.close_session(log)

    async def main():
        state = EmbassyState()

        # Test 1: session is active inside context, log yielded correctly
        async with visa_session(state, "Officer Dela Cruz") as log:
            print("Test 1: session active inside context")
            print(f"  officer={log.officer!r}")
            print(f"  is_active={log.is_active}")
            print(f"  active_sessions={len(state.active_sessions)}")
            assert log.officer == "Officer Dela Cruz"
            assert log.is_active is True
            assert len(state.active_sessions) == 1
            print("  PASS")

        # Test 2: session closed after context exits
        print("Test 2: session closed after context")
        print(f"  is_active={log.is_active}")
        print(f"  active_sessions={len(state.active_sessions)}")
        print(f"  closed_count={state.closed_count}")
        assert log.is_active is False
        assert len(state.active_sessions) == 0
        assert state.closed_count == 1
        print("  PASS")

        # Test 3: stamps logged during session
        async with visa_session(state, "Officer Reyes") as log2:
            log2.stamps.append("APP-001")
            log2.stamps.append("APP-002")
            print("Test 3: stamps recorded during session")
            print(f"  stamps={log2.stamps}")
            assert log2.stamps == ["APP-001", "APP-002"]
            print("  PASS")

        # Test 4: two concurrent sessions tracked separately
        async with visa_session(state, "Officer A") as logA:
            async with visa_session(state, "Officer B") as logB:
                print("Test 4: two concurrent sessions")
                print(f"  active_sessions={len(state.active_sessions)}")
                assert len(state.active_sessions) == 2
                assert logA.is_active is True
                assert logB.is_active is True
                print("  PASS")

        # Test 5: stamps default not shared between SessionLog instances
        s1 = SessionLog(officer="A")
        s2 = SessionLog(officer="B")
        s1.stamps.append("APP-999")
        print("Test 5: stamps mutable default isolation")
        print(f"  s1.stamps={s1.stamps}")
        print(f"  s2.stamps={s2.stamps}")
        assert s1.stamps == ["APP-999"]
        assert s2.stamps == []
        print("  PASS")

    asyncio.run(main())


run_drill_87()


# EXPECTED OUTPUT
# ===============
# Test 1: session active inside context
#   officer='Officer Dela Cruz'
#   is_active=True
#   active_sessions=1
#   PASS
# Test 2: session closed after context
#   is_active=False
#   active_sessions=0
#   closed_count=1
#   PASS
# Test 3: stamps recorded during session
#   stamps=['APP-001', 'APP-002']
#   PASS
# Test 4: two concurrent sessions
#   active_sessions=2
#   PASS
# Test 5: stamps mutable default isolation
#   s1.stamps=['APP-999']
#   s2.stamps=[]
#   PASS
