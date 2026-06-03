import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_76():
    # =========================================================================
    # SCENARIO: The Stock Exchange
    # =========================================================================
    # A stock exchange order system raises different errors for different
    # failure modes. Instead of raising raw ValueError everywhere, the system
    # uses a hierarchy of custom exceptions — each carrying meaning.
    # The dispatch layer catches at the right level and maps exceptions
    # to HTTP-style error responses.
    #
    # NEW CONCEPT: custom exception hierarchy — base → domain → HTTP-mappable
    # - Define a base exception class that all domain errors inherit from
    # - Define specific domain exceptions that inherit from the base
    # - Catching the BASE catches ALL subclasses — useful for a global handler
    # - Catching a SPECIFIC subclass lets you handle it differently
    # - HTTP-mappable means each exception carries a status_code so the
    #   dispatch layer can build a response without knowing the specific type
    # - Shape:
    #     class AppError(Exception):          ← base
    #         def __init__(self, msg, status_code):
    #             super().__init__(msg)
    #             self.status_code = status_code
    #     class NotFoundError(AppError): ...  ← domain
    #     class ForbiddenError(AppError): ... ← domain
    #
    # REQUIREMENTS:
    #
    # 1. A base exception AppError(Exception):
    #    - __init__(self, message: str, status_code: int)
    #    - stores both as instance attributes
    #    - calls super().__init__(message)
    #
    # 2. Three domain exceptions, all inheriting from AppError:
    #    - NotFoundError: always uses status_code=404
    #      __init__(self, message: str) — hardcodes status_code
    #    - ForbiddenError: always uses status_code=403
    #    - InsufficientFundsError: always uses status_code=422
    #
    # 3. A Pydantic model TradeOrder:
    #    - symbol: str
    #    - quantity: int (gt=0)
    #    - price: float (gt=0)
    #
    # 4. A registry: ROUTES = {}
    #
    # 5. A decorator @route(action: str):
    #    - stores handler in ROUTES under action
    #    - returns func unchanged
    #
    # 6. Three async handlers:
    #    - async def buy(order: TradeOrder) -> dict:
    #        - if order.symbol == "UNKNOWN", raise NotFoundError("Symbol not found")
    #        - if order.symbol == "RESTRICTED", raise ForbiddenError("Trading restricted")
    #        - if order.quantity > 100, raise InsufficientFundsError("Order too large")
    #        - otherwise return {"action": "buy", "symbol": order.symbol,
    #                            "quantity": order.quantity, "status": "executed"}
    #    - async def sell(order: TradeOrder) -> dict:
    #        - if order.symbol == "UNKNOWN", raise NotFoundError("Symbol not found")
    #        - otherwise return {"action": "sell", "symbol": order.symbol,
    #                            "quantity": order.quantity, "status": "executed"}
    #    - async def cancel(order: TradeOrder) -> dict:
    #        - if order.symbol == "RESTRICTED", raise ForbiddenError("Cannot cancel restricted")
    #        - otherwise return {"action": "cancel", "symbol": order.symbol, "status": "cancelled"}
    #
    # 7. Apply @route:
    #    - @route("buy") → buy
    #    - @route("sell") → sell
    #    - @route("cancel") → cancel
    #
    # 8. An async dispatch(action: str, raw_payload: dict) -> dict:
    #    - if action not in ROUTES, return {"error": "unknown action", "status_code": 404}
    #    - validate raw_payload into TradeOrder
    #      - if ValidationError, return {"error": "invalid order", "status_code": 422}
    #    - call and await the handler
    #    - catch AppError (the base) and return:
    #      {"error": str(e), "status_code": e.status_code}
    #    - return the result on success
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class AppError(Exception):
        def __init__(self, message: str, status_code: int):
            super().__init__(message)
            self.status_code = status_code

    class NotFoundError(AppError):
        def __init__(self, message):
            super().__init__(message, status_code=404)

    class ForbiddenError(AppError):
        def __init__(self, message):
            super().__init__(message, status_code=403)

    class InsufficientFundsError(AppError):
        def __init__(self, message):
            super().__init__(message, status_code=422)

    class TradeOrder(BaseModel):
        symbol: str
        quantity: int = Field(gt=0)
        price: float = Field(gt=0)

    ROUTES = {}

    def route(action: str):
        def decorator(func: Callable):
            ROUTES[action] = func
            return func

        return decorator

    @route(action="buy")
    async def buy(order: TradeOrder):
        if order.symbol == "UNKNOWN":
            raise NotFoundError("Symbol not found")
        if order.symbol == "RESTRICTED":
            raise ForbiddenError("Trading restricted")
        if order.quantity > 100:
            raise InsufficientFundsError("Order too large")
        return {
            "action": "buy",
            "symbol": order.symbol,
            "quantity": order.quantity,
            "status": "executed",
        }

    @route(action="sell")
    async def sell(order: TradeOrder):
        if order.symbol == "UNKNOWN":
            raise NotFoundError("Symbol not found")
        return {
            "action": "sell",
            "symbol": order.symbol,
            "quantity": order.quantity,
            "status": "executed",
        }

    @route(action="cancel")
    async def cancel(order: TradeOrder):
        if order.symbol == "RESTRICTED":
            raise ForbiddenError("Cannot cancel restricted")
        return {"action": "cancel", "symbol": order.symbol, "status": "cancelled"}

    async def dispatch(action: str, raw_payload: dict):
        if action not in ROUTES:
            return {"error": "unknown action", "status_code": 404}
        try:
            valid_pd = TradeOrder(**raw_payload)
            result = await ROUTES[action](valid_pd)
        except ValidationError:
            return {"error": "invalid order", "status_code": 422}
        except AppError as e:
            return {"error": str(e), "status_code": e.status_code}
        return result

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    print("Test 1: valid buy order")
    result = await dispatch("buy", {"symbol": "AAPL", "quantity": 10, "price": 150.0})  # noqa: F821
    print(f"  {result}")
    assert result == {
        "action": "buy",
        "symbol": "AAPL",
        "quantity": 10,
        "status": "executed",
    }, f"Got {result!r}"
    print("  PASS")

    print("\nTest 2: valid sell order")
    result = await dispatch("sell", {"symbol": "TSLA", "quantity": 5, "price": 200.0})  # noqa: F821
    print(f"  {result}")
    assert result == {
        "action": "sell",
        "symbol": "TSLA",
        "quantity": 5,
        "status": "executed",
    }, f"Got {result!r}"
    print("  PASS")

    print("\nTest 3: buy unknown symbol — NotFoundError (404)")
    result = await dispatch("buy", {"symbol": "UNKNOWN", "quantity": 1, "price": 10.0})  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "Symbol not found", "status_code": 404}, (
        f"Got {result!r}"
    )
    print("  PASS")

    print("\nTest 4: buy restricted symbol — ForbiddenError (403)")
    result = await dispatch(
        "buy", {"symbol": "RESTRICTED", "quantity": 1, "price": 10.0}
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "Trading restricted", "status_code": 403}, (
        f"Got {result!r}"
    )
    print("  PASS")

    print("\nTest 5: buy too large — InsufficientFundsError (422)")
    result = await dispatch("buy", {"symbol": "AAPL", "quantity": 200, "price": 150.0})  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "Order too large", "status_code": 422}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 6: cancel restricted — ForbiddenError caught at base level")
    result = await dispatch(
        "cancel", {"symbol": "RESTRICTED", "quantity": 1, "price": 10.0}
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "Cannot cancel restricted", "status_code": 403}, (
        f"Got {result!r}"
    )
    print("  PASS")

    print("\nTest 7: invalid payload — quantity <= 0")
    result = await dispatch("buy", {"symbol": "AAPL", "quantity": 0, "price": 150.0})  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "invalid order", "status_code": 422}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 8: unknown action")
    result = await dispatch("short", {"symbol": "AAPL", "quantity": 1, "price": 150.0})  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "unknown action", "status_code": 404}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 9: exception hierarchy — NotFoundError is an AppError")
    err = NotFoundError("test")  # noqa: F821
    assert isinstance(err, AppError), "NotFoundError must inherit from AppError"  # noqa: F821
    assert err.status_code == 404
    assert str(err) == "test"
    print(f"  NotFoundError status_code: {err.status_code}")
    print("  PASS")

    print("\nTest 10: exception hierarchy — catching base catches all")
    caught = []
    for exc in [NotFoundError("a"), ForbiddenError("b"), InsufficientFundsError("c")]:  # noqa: F821
        try:
            raise exc
        except AppError as e:  # noqa: F821
            caught.append(e.status_code)
    print(f"  caught status_codes: {caught}")
    assert caught == [404, 403, 422], f"Got {caught!r}"
    print("  PASS")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: valid buy order
    #   {'action': 'buy', 'symbol': 'AAPL', 'quantity': 10, 'status': 'executed'}
    #   PASS
    #
    # Test 2: valid sell order
    #   {'action': 'sell', 'symbol': 'TSLA', 'quantity': 5, 'status': 'executed'}
    #   PASS
    #
    # Test 3: buy unknown symbol — NotFoundError (404)
    #   {'error': 'Symbol not found', 'status_code': 404}
    #   PASS
    #
    # Test 4: buy restricted symbol — ForbiddenError (403)
    #   {'error': 'Trading restricted', 'status_code': 403}
    #   PASS
    #
    # Test 5: buy too large — InsufficientFundsError (422)
    #   {'error': 'Order too large', 'status_code': 422}
    #   PASS
    #
    # Test 6: cancel restricted — ForbiddenError caught at base level
    #   {'error': 'Cannot cancel restricted', 'status_code': 403}
    #   PASS
    #
    # Test 7: invalid payload — quantity <= 0
    #   {'error': 'invalid order', 'status_code': 422}
    #   PASS
    #
    # Test 8: unknown action
    #   {'error': 'unknown action', 'status_code': 404}
    #   PASS
    #
    # Test 9: exception hierarchy — NotFoundError is an AppError
    #   NotFoundError status_code: 404
    #   PASS
    #
    # Test 10: exception hierarchy — catching base catches all
    #   caught status_codes: [404, 403, 422]
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_76())
