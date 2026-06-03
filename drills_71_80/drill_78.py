import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_78():
    # =========================================================================
    # SCENARIO: The Fire Station
    # =========================================================================
    # A fire station dispatch system accepts emergency calls and queues them
    # for processing. The dispatcher returns immediately after queuing the call
    # — it does not wait for the incident to be resolved. A background worker
    # picks up each call from the queue and processes it independently.
    #
    # NEW CONCEPT: async queue — background task pattern
    # - asyncio.Queue is a thread-safe async FIFO queue
    # - Producers put work on the queue and return immediately
    # - A consumer worker runs as a background task via asyncio.create_task()
    # - The worker loops: get item → process → task_done
    # - queue.join() blocks until all queued items have been processed
    # - This is the foundation of FastAPI's BackgroundTasks
    #
    # REQUIREMENTS:
    #
    # 1. A Pydantic model EmergencyCall:
    #    - call_id: str
    #    - location: str
    #    - severity: int (ge=1, le=5)
    #
    # 2. A shared list: processed = []
    #    - the worker appends results here so tests can inspect them
    #
    # 3. An async worker function process_calls(queue: asyncio.Queue):
    #    - loops forever with while True
    #    - gets the next EmergencyCall from the queue
    #    - appends to processed:
    #      f"[{call.call_id}] {call.location} — severity {call.severity} dispatched"
    #    - calls queue.task_done()
    #
    # 4. A registry: ROUTES = {}
    #
    # 5. A decorator @route(action: str):
    #    - stores handler in ROUTES under action
    #    - returns func unchanged
    #
    # 6. An async handler queue_call(call: EmergencyCall, queue: asyncio.Queue) -> dict:
    #    - decorated with @route("queue")
    #    - puts the call onto the queue
    #    - returns immediately with:
    #      {"call_id": call.call_id, "status": "queued", "position": queue.qsize()}
    #    - NOTE: position is the queue size AFTER putting — read it after put
    #
    # 7. An async dispatch(action: str, raw_payload: dict, queue: asyncio.Queue) -> dict:
    #    - if action not in ROUTES, return {"error": f"unknown action: {action}"}
    #    - validate raw_payload into EmergencyCall
    #      - if ValidationError, return {"error": "invalid call"}
    #    - call and await the handler passing the validated call and queue
    #    - return the result
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class EmergencyCall(BaseModel):
        call_id: str
        location: str
        severity: int = Field(ge=1, le=5)

    processed = []

    async def process_calls(queue: asyncio.Queue):
        while True:
            call = await queue.get()
            processed.append(
                f"[{call.call_id}] {call.location} — severity {call.severity} dispatched"
            )
            queue.task_done()

    ROUTES = {}

    def route(action: str):
        def decorator(func: Callable):
            ROUTES[action] = func
            return func

        return decorator

    @route("queue")
    async def queue_call(call: EmergencyCall, queue: asyncio.Queue):
        await queue.put(call)
        return {"call_id": call.call_id, "status": "queued", "position": queue.qsize()}

    async def dispatch(action: str, raw_payload: dict, queue: asyncio.Queue):
        if action not in ROUTES:
            return {"error": f"unknown action: {action}"}
        try:
            valid_call = EmergencyCall(**raw_payload)
        except ValidationError:
            return {"error": "invalid call"}
        return await ROUTES[action](valid_call, queue)

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    queue = asyncio.Queue()
    worker_task = asyncio.create_task(process_calls(queue))  # noqa: F821

    print("Test 1: queue a valid call — returns immediately")
    result = await dispatch(
        "queue", {"call_id": "F-001", "location": "Main St", "severity": 3}, queue
    )  # noqa: F821
    print(f"  {result}")
    assert result["call_id"] == "F-001"
    assert result["status"] == "queued"
    print("  PASS")

    print("\nTest 2: queue two more calls")
    await dispatch(
        "queue", {"call_id": "F-002", "location": "Oak Ave", "severity": 5}, queue
    )  # noqa: F821
    await dispatch(
        "queue", {"call_id": "F-003", "location": "Pine Rd", "severity": 1}, queue
    )  # noqa: F821
    print("  queued F-002 and F-003")
    print("  PASS")

    print("\nTest 3: wait for all calls to be processed")
    await queue.join()
    print(f"  processed: {processed}")  # noqa: F821
    assert len(processed) == 3  # noqa: F821
    assert any("F-001" in p for p in processed)  # noqa: F821
    assert any("F-002" in p for p in processed)  # noqa: F821
    assert any("F-003" in p for p in processed)  # noqa: F821
    print("  PASS")

    print("\nTest 4: processed entries have correct format")
    f001 = next(p for p in processed if "F-001" in p)  # noqa: F821
    print(f"  {f001!r}")
    assert f001 == "[F-001] Main St — severity 3 dispatched", f"Got {f001!r}"
    print("  PASS")

    print("\nTest 5: invalid payload")
    result = await dispatch(
        "queue", {"call_id": "F-004", "location": "X", "severity": 9}, queue
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "invalid call"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 6: unknown action")
    result = await dispatch(
        "cancel", {"call_id": "F-001", "location": "X", "severity": 1}, queue
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "unknown action: cancel"}, f"Got {result!r}"
    print("  PASS")

    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: queue a valid call — returns immediately
    #   {'call_id': 'F-001', 'status': 'queued', 'position': 0 or 1}
    #   PASS
    #
    # Test 2: queue two more calls
    #   queued F-002 and F-003
    #   PASS
    #
    # Test 3: wait for all calls to be processed
    #   processed: ['[F-001] Main St — severity 3 dispatched',
    #               '[F-002] Oak Ave — severity 5 dispatched',
    #               '[F-003] Pine Rd — severity 1 dispatched']
    #   PASS
    #
    # Test 4: processed entries have correct format
    #   '[F-001] Main St — severity 3 dispatched'
    #   PASS
    #
    # Test 5: invalid payload
    #   {'error': 'invalid call'}
    #   PASS
    #
    # Test 6: unknown action
    #   {'error': 'unknown action: cancel'}
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_78())
