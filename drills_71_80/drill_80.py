import asyncio  # noqa: F401
from contextvars import ContextVar  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_80():
    # =========================================================================
    # SCENARIO: The Casino
    # =========================================================================
    # A casino floor management system handles bet placements. This is the
    # final boss — no new concepts. You combine everything from drills 71–79
    # from a blank page.
    #
    # WHAT YOU ARE BUILDING:
    # - Custom exception hierarchy (drill 76)
    # - Nested Pydantic models (drill 74)
    # - A class-based Router with its own registry and dispatch (drill 73)
    # - An OOP decorator that validates a raw kwarg into a Pydantic model (drill 71)
    # - Parallel dependency resolution with gather (drill 75)
    # - A semaphore inside a decorator to limit concurrency (drill 79)
    # - A ContextVar to carry request_id through the call chain (drill 77)
    # - A background audit queue + worker (drill 78)
    #
    # REQUIREMENTS:
    #
    # 1. Exception hierarchy:
    #    - Base: CasinoError(Exception) — carries status_code
    #    - BetLimitError(CasinoError)   — status_code 422
    #    - PlayerBannedError(CasinoError) — status_code 403
    #    - TableClosedError(CasinoError) — status_code 503
    #
    # 2. Nested Pydantic models:
    #    - Player: player_id (str), name (str)
    #    - Chip: denomination (int, gt=0), count (int, gt=0)
    #    - BetSlip: player (Player), chips (list[Chip]), table (str)
    #    - BetResult: player_id (str), table (str), total_bet (int), status (str)
    #
    # 3. A ContextVar request_id_var: ContextVar[str] with default "none"
    #
    # 4. A shared audit_log = []
    #
    # 5. An async audit worker process_audit(queue: asyncio.Queue):
    #    - loops forever
    #    - gets item (a string) from the queue
    #    - appends it to audit_log
    #    - calls task_done()
    #
    # 6. A decorator validate_slip(func):
    #    - OOP decorator (reads args[0] as instance)
    #    - expects kwargs["raw"] to be a raw dict
    #    - validates kwargs["raw"] into BetSlip
    #    - if ValidationError: raise CasinoError("Invalid bet slip", 400)
    #    - replaces kwargs["raw"] with the validated BetSlip
    #    - calls and awaits func
    #
    # 7. A decorator limit_table(max_players: int):
    #    - semaphore factory — caps concurrent calls to that method
    #    - semaphore lives in the closure
    #
    # 8. Two async dependency functions:
    #    - async def verify_player(player_id: str) -> dict:
    #        - sleeps 0.02s
    #        - if player_id == "banned", raise PlayerBannedError("Player is banned")
    #        - returns {"player_id": player_id, "verified": True}
    #    - async def verify_table(table: str) -> dict:
    #        - sleeps 0.02s
    #        - if table == "closed", raise TableClosedError("Table is closed")
    #        - returns {"table": table, "open": True}
    #
    # 9. A class CasinoRouter:
    #    - __init__(self, name: str):
    #        - self.name = name
    #        - self.routes = {}
    #    - method register(self, action: str): decorator factory → stores in self.routes
    #    - async method dispatch(self, action: str, raw: dict, queue: asyncio.Queue) -> dict:
    #        - if action not in self.routes:
    #            return {"error": "unknown action", "status_code": 404}
    #        - validate raw into BetSlip
    #            - if ValidationError: return {"error": "invalid slip", "status_code": 400}
    #        - resolve verify_player and verify_table IN PARALLEL with gather
    #            - if CasinoError: return {"error": str(e), "status_code": e.status_code}
    #        - set request_id_var to slip.player.player_id, save token
    #        - call and await the handler passing slip, player, table_info, queue
    #        - reset request_id_var in finally
    #        - return result
    #
    # 10. A CasinoRouter instance: floor = CasinoRouter(name="Main Floor")
    #
    # 11. An async handler place_bet(self_unused, *, raw, player, table_info, queue):
    #     - NOTE: this is a standalone async function registered via @floor.register
    #       it is NOT a class method — self_unused will be None, ignore it
    #     - decorated with @floor.register("place_bet") AND @limit_table(max_players=3)
    #       AND @validate_slip
    #     - raw is already a validated BetSlip when it arrives (validate_slip ran first)
    #     - compute total_bet = sum(chip.denomination * chip.count for chip in raw.chips)
    #     - if total_bet > 1000: raise BetLimitError("Bet exceeds table limit")
    #     - put audit string on queue:
    #       f"[{request_id_var.get()}] {raw.player.name} bet {total_bet} at {raw.table}"
    #     - return BetResult(
    #           player_id=raw.player.player_id,
    #           table=raw.table,
    #           total_bet=total_bet,
    #           status="accepted"
    #       ).model_dump()
    #
    # NOTE on decorator order for place_bet:
    #   @floor.register("place_bet")   ← outermost: stores in registry
    #   @limit_table(max_players=3)    ← middle: semaphore
    #   @validate_slip                 ← innermost: runs first, validates raw
    #   async def place_bet(...): ...
    #
    # NOTE on dispatch calling the handler:
    #   handler = self.routes["place_bet"]
    #   result = await handler(None, raw=slip, player=player, table_info=table_info, queue=queue)
    #   pass None as first positional arg (self_unused)
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class CasinoError(Exception):
        def __init__(self, msg, status_code):
            super().__init__(msg)
            self.status_code = status_code

    class BetLimitError(CasinoError):
        def __init__(self, msg):
            super().__init__(msg, status_code=422)

    class PlayerBannedError(CasinoError):
        def __init__(self, msg):
            super().__init__(msg, status_code=403)

    class TableClosedError(CasinoError):
        def __init__(self, msg):
            super().__init__(msg, status_code=503)

    class Player(BaseModel):
        player_id: str
        name: str

    class Chip(BaseModel):
        denomination: int = Field(gt=0)
        count: int = Field(gt=0)

    class BetSlip(BaseModel):
        player: Player
        chips: list[Chip]
        table: str

    class BetResult(BaseModel):
        player_id: str
        table: str
        total_bet: int
        status: str

    request_id_var: ContextVar[str] = ContextVar("request_id", default="none")

    audit_log = []

    async def process_audit(queue: asyncio.Queue):
        while True:
            item = await queue.get()
            audit_log.append(item)
            queue.task_done()

    def validate_slip(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            instance = args[0]
            try:
                raw = kwargs["raw"]
                if not isinstance(raw, BetSlip):
                    raw = BetSlip(**raw)
                kwargs["raw"] = raw
                return await func(*args, **kwargs)
            except ValidationError:
                raise CasinoError("Invalid bet slip", 400)

        return wrapper

    def limit_table(max_players: int):
        sem = asyncio.Semaphore(max_players)

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with sem:
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    async def verify_player(player_id: str):
        await asyncio.sleep(0.02)
        if player_id.lower() == "banned":
            raise PlayerBannedError("Player is banned")
        return {"player_id": player_id, "verified": True}

    async def verify_table(table: str):
        await asyncio.sleep(0.02)
        if table.lower() == "closed":
            raise TableClosedError("Table is closed")
        return {"table": table, "open": True}

    class CasinoRouter:
        def __init__(self, name: str):
            self.name = name
            self.routes = {}

        def register(self, action: str):
            def decorator(func: Callable):
                self.routes[action] = func
                return func

            return decorator

        async def dispatch(self, action: str, raw: dict, queue: asyncio.Queue):
            if action not in self.routes:
                return {"error": "unknown action", "status_code": 404}
            try:
                valid_slip = BetSlip(**raw)
                await asyncio.gather(
                    verify_player(valid_slip.player.player_id),
                    verify_table(valid_slip.table),
                )
            except ValidationError:
                return {"error": "invalid slip", "status_code": 400}
            except CasinoError as e:
                return {"error": str(e), "status_code": e.status_code}
            token = request_id_var.set(valid_slip.player.player_id)
            try:
                return await self.routes[action](
                    None,
                    raw=valid_slip,
                    player=valid_slip.player,
                    table_info=valid_slip.table,
                    queue=queue,
                )
            except CasinoError as e:
                return {"error": str(e), "status_code": e.status_code}
            finally:
                request_id_var.reset(token)

    floor = CasinoRouter(name="Main Floor")

    @floor.register("place_bet")
    @limit_table(max_players=3)
    @validate_slip
    async def place_bet(self_unused, *, raw, player, table_info, queue):
        total_bet = sum(chip.denomination * chip.count for chip in raw.chips)
        if total_bet > 1000:
            raise BetLimitError("Bet exceeds table limit")
        await queue.put(
            f"[{request_id_var.get()}] {player.name} bet {total_bet} at {table_info}"
        )
        return BetResult(
            player_id=player.player_id,
            table=table_info,
            total_bet=total_bet,
            status="accepted",
        ).model_dump()

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    audit_queue = asyncio.Queue()
    worker_task = asyncio.create_task(process_audit(audit_queue))  # noqa: F821

    valid_raw = {
        "player": {"player_id": "P-001", "name": "Alice"},
        "chips": [{"denomination": 100, "count": 3}],
        "table": "blackjack-1",
    }

    print("Test 1: valid bet — full pipeline")
    result = await floor.dispatch("place_bet", valid_raw, audit_queue)  # noqa: F821
    print(f"  {result}")
    assert result == {
        "player_id": "P-001",
        "table": "blackjack-1",
        "total_bet": 300,
        "status": "accepted",
    }, f"Got {result!r}"
    print("  PASS")

    print("\nTest 2: audit log populated after queue.join()")
    await audit_queue.join()
    print(f"  audit_log: {audit_log}")  # noqa: F821
    assert len(audit_log) == 1  # noqa: F821
    assert "Alice" in audit_log[0]  # noqa: F821
    assert "300" in audit_log[0]  # noqa: F821
    print("  PASS")

    print("\nTest 3: banned player — PlayerBannedError (403)")
    banned_raw = {
        "player": {"player_id": "banned", "name": "Bad Guy"},
        "chips": [{"denomination": 50, "count": 2}],
        "table": "poker-1",
    }
    result = await floor.dispatch("place_bet", banned_raw, audit_queue)  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "Player is banned", "status_code": 403}, (
        f"Got {result!r}"
    )
    print("  PASS")

    print("\nTest 4: closed table — TableClosedError (503)")
    closed_raw = {
        "player": {"player_id": "P-002", "name": "Bob"},
        "chips": [{"denomination": 25, "count": 4}],
        "table": "closed",
    }
    result = await floor.dispatch("place_bet", closed_raw, audit_queue)  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "Table is closed", "status_code": 503}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 5: bet over limit — BetLimitError (422)")
    big_raw = {
        "player": {"player_id": "P-003", "name": "Carol"},
        "chips": [{"denomination": 500, "count": 3}],
        "table": "vip-1",
    }
    result = await floor.dispatch("place_bet", big_raw, audit_queue)  # noqa: F821
    print(f"  {result}")
    assert result["error"] == "Bet exceeds table limit"
    assert result["status_code"] == 422
    print("  PASS")

    print("\nTest 6: invalid slip — missing player field")
    result = await floor.dispatch("place_bet", {"chips": [], "table": "x"}, audit_queue)  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "invalid slip", "status_code": 400}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 7: unknown action")
    result = await floor.dispatch("cash_out", valid_raw, audit_queue)  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "unknown action", "status_code": 404}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 8: request_id_var resets after dispatch")
    current = request_id_var.get()  # noqa: F821
    print(f"  request_id_var: {current!r}")
    assert current == "none", f"Expected 'none', got {current!r}"
    print("  PASS")

    print("\nTest 9: semaphore — 5 concurrent bets all complete (cap=3)")
    import time  # noqa: F401

    audit_log.clear()  # noqa: F821
    t0 = time.monotonic()
    raw_batch = [
        {
            "player": {"player_id": f"P-{i:03}", "name": f"Player{i}"},
            "chips": [{"denomination": 10, "count": 5}],
            "table": "roulette-1",
        }
        for i in range(5)
    ]
    results = await asyncio.gather(
        *[floor.dispatch("place_bet", r, audit_queue) for r in raw_batch]
    )  # noqa: F821
    elapsed = time.monotonic() - t0
    print(f"  elapsed: {elapsed:.3f}s")
    assert all(r["status"] == "accepted" for r in results), f"Got {results!r}"
    print("  PASS")

    print("\nTest 10: exception hierarchy — all are CasinoError")
    for exc in [BetLimitError("x"), PlayerBannedError("x"), TableClosedError("x")]:  # noqa: F821
        assert isinstance(exc, CasinoError), f"{type(exc)} not CasinoError"  # noqa: F821
    print("  all inherit from CasinoError")
    print("  PASS")

    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: valid bet — full pipeline
    #   {'player_id': 'P-001', 'table': 'blackjack-1', 'total_bet': 300, 'status': 'accepted'}
    #   PASS
    #
    # Test 2: audit log populated after queue.join()
    #   audit_log: ['[P-001] Alice bet 300 at blackjack-1']
    #   PASS
    #
    # Test 3: banned player — PlayerBannedError (403)
    #   {'error': 'Player is banned', 'status_code': 403}
    #   PASS
    #
    # Test 4: closed table — TableClosedError (503)
    #   {'error': 'Table is closed', 'status_code': 503}
    #   PASS
    #
    # Test 5: bet over limit — BetLimitError (422)
    #   {'error': 'Bet exceeds table limit', 'status_code': 422}
    #   PASS
    #
    # Test 6: invalid slip — missing player field
    #   {'error': 'invalid slip', 'status_code': 400}
    #   PASS
    #
    # Test 7: unknown action
    #   {'error': 'unknown action', 'status_code': 404}
    #   PASS
    #
    # Test 8: request_id_var resets after dispatch
    #   request_id_var: 'none'
    #   PASS
    #
    # Test 9: semaphore — 5 concurrent bets all complete (cap=3)
    #   elapsed: 0.0XXs
    #   PASS
    #
    # Test 10: exception hierarchy — all are CasinoError
    #   all inherit from CasinoError
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_80())
