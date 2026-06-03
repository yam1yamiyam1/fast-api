import asyncio  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_69():
    # =========================================================================
    # SCENARIO: The Stock Exchange
    # =========================================================================
    # A stock exchange API validates not just the input but also the OUTPUT
    # of every handler. If a handler returns data that doesn't match the
    # expected response shape, it's caught before it reaches the caller.
    #
    # This is the response model pattern — validate what goes OUT, not just
    # what comes IN.
    #
    # REQUIREMENTS:
    #
    # 1. Two Pydantic models:
    #    - class StockRequest(BaseModel):
    #        - symbol: str
    #        - quantity: int
    #    - class StockResponse(BaseModel):
    #        - symbol: str
    #        - price: float
    #        - total: float
    #        - status: str
    #
    # 2. A custom exception: InvalidResponseError(Exception)
    #
    # 3. A registry: ROUTES = {}
    #    - each entry: {"handler": func, "response_model": PydanticModel}
    #
    # 4. A decorator @route(path: str, response_model):
    #    - stores {"handler": func, "response_model": response_model} in ROUTES
    #    - returns func unchanged
    #
    # 5. Two async handlers (you write these):
    #    - async def buy_stock(request: StockRequest) -> dict:
    #        - returns {
    #            "symbol": request.symbol,
    #            "price": 150.0,
    #            "total": 150.0 * request.quantity,
    #            "status": "bought"
    #          }
    #    - async def broken_stock(request: StockRequest) -> dict:
    #        - returns {
    #            "symbol": request.symbol,
    #            "price": "not a float",  ← intentionally wrong type
    #            "total": 150.0 * request.quantity,
    #            "status": "bought"
    #          }
    #
    # 6. Apply @route:
    #    - @route("/stocks/buy",    response_model=StockResponse) -> buy_stock
    #    - @route("/stocks/broken", response_model=StockResponse) -> broken_stock
    #
    # 7. An async dispatch(path: str, raw_payload: dict) -> dict | None:
    #    - if path not found, return {"error": "not found"}
    #    - validate raw_payload into StockRequest
    #      - if ValidationError, return {"error": "invalid request", "detail": str(e)}
    #    - call and await the handler passing the validated request
    #    - validate the handler's return value against the response_model
    #      - if ValidationError, raise InvalidResponseError(str(e))
    #    - return the validated response as a dict using .model_dump()
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class StockRequest(BaseModel):
        symbol: str
        quantity: int

    class StockResponse(BaseModel):
        symbol: str
        price: float
        total: float
        status: str

    class InvalidResponseError(Exception):
        pass

    ROUTES = {}

    def route(path: str, response_model):
        def decorator(func: Callable):
            ROUTES[path] = {"handler": func, "response_model": response_model}
            return func

        return decorator

    @route(path="/stocks/buy", response_model=StockResponse)
    async def buy_stock(request: StockRequest):
        return {
            "symbol": request.symbol,
            "price": 150.0,
            "total": 150.0 * request.quantity,
            "status": "bought",
        }

    @route(path="/stocks/broken", response_model=StockResponse)
    async def broken_stock(request: StockRequest):
        return {
            "symbol": request.symbol,
            "price": "not a float",
            "total": 150.0 * request.quantity,
            "status": "bought",
        }

    async def dispatch(path: str, raw_payload: dict):
        if path not in ROUTES:
            return {"error": "not found"}
        route = ROUTES[path]
        try:
            valid_pd = StockRequest(**raw_payload)
        except ValidationError as e:
            return {"error": "invalid request", "detail": str(e)}
        try:
            response = await route["handler"](valid_pd)
            valid_rs = route["response_model"](**response)
            return valid_rs.model_dump()

        except ValidationError as e:
            raise InvalidResponseError(str(e))

    # --- TESTS (do not modify) ---
    print("Test 1: Valid request — response validated")
    result = await dispatch("/stocks/buy", {"symbol": "AAPL", "quantity": 3})
    print(f"  Result: {result}")

    print("\nTest 2: Invalid request payload")
    result = await dispatch("/stocks/buy", {"symbol": "AAPL", "quantity": "three"})
    print(f"  Result: {result}")

    print("\nTest 3: Handler returns wrong response shape — InvalidResponseError")
    try:
        await dispatch("/stocks/broken", {"symbol": "AAPL", "quantity": 3})
    except InvalidResponseError:
        print("  Caught InvalidResponseError")

    print("\nTest 4: Unknown path")
    result = await dispatch("/stocks/sell", {"symbol": "AAPL", "quantity": 1})
    print(f"  Result: {result}")

    print("\nTest 5: Response is a proper dict not a Pydantic object")
    result = await dispatch("/stocks/buy", {"symbol": "TSLA", "quantity": 2})
    assert isinstance(result, dict)
    assert result["symbol"] == "TSLA"
    assert result["total"] == 300.0
    print("  All assertions passed")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid request — response validated
    #   Result: {'symbol': 'AAPL', 'price': 150.0, 'total': 450.0, 'status': 'bought'}
    #
    # Test 2: Invalid request payload
    #   Result: {'error': 'invalid request', 'detail': '...'}
    #
    # Test 3: Handler returns wrong response shape — InvalidResponseError
    #   Caught InvalidResponseError
    #
    # Test 4: Unknown path
    #   Result: {'error': 'not found'}
    #
    # Test 5: Response is a proper dict not a Pydantic object
    #   All assertions passed
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_69())
