import pytest  # noqa: F401
import pytest_asyncio  # noqa: F401
from main import router  # noqa: F401


async def dispatch(method, path, body=None):
    return await router.dispatch(method, path, body)


# --- Listings: create ---


@pytest.mark.asyncio
async def test_create_listing_returns_id():
    result = await dispatch(
        "POST", "/listings", {"ticker": "AAPL", "price": 150.0, "company": "Apple Inc"}
    )
    assert "id" in result
    assert result["ticker"] == "AAPL"
    assert result["price"] == 150.0
    assert result["company"] == "Apple Inc"


@pytest.mark.asyncio
async def test_create_listing_empty_ticker_returns_422():
    result = await dispatch(
        "POST", "/listings", {"ticker": "", "price": 150.0, "company": "Apple Inc"}
    )
    assert result["status_code"] == 422


@pytest.mark.asyncio
async def test_create_listing_zero_price_returns_422():
    result = await dispatch(
        "POST", "/listings", {"ticker": "GOOG", "price": 0, "company": "Alphabet"}
    )
    assert result["status_code"] == 422


@pytest.mark.asyncio
async def test_create_listing_negative_price_returns_422():
    result = await dispatch(
        "POST", "/listings", {"ticker": "GOOG", "price": -10.0, "company": "Alphabet"}
    )
    assert result["status_code"] == 422


# --- Listings: get all ---


@pytest.mark.asyncio
async def test_get_all_listings_returns_items_key():
    result = await dispatch("GET", "/listings")
    assert "items" in result
    assert isinstance(result["items"], list)


# --- Listings: get one ---


@pytest.mark.asyncio
async def test_get_listing_by_id():
    created = await dispatch(
        "POST", "/listings", {"ticker": "MSFT", "price": 300.0, "company": "Microsoft"}
    )
    listing_id = created["id"]
    result = await dispatch("GET", f"/listings/{listing_id}")
    assert result["id"] == listing_id
    assert result["ticker"] == "MSFT"


@pytest.mark.asyncio
async def test_get_listing_not_found_returns_404():
    result = await dispatch("GET", "/listings/999999")
    assert result["status_code"] == 404
    assert "error" in result


# --- Listings: delete ---


@pytest.mark.asyncio
async def test_delete_listing_returns_deleted():
    created = await dispatch(
        "POST", "/listings", {"ticker": "TSLA", "price": 700.0, "company": "Tesla"}
    )
    listing_id = created["id"]
    result = await dispatch("DELETE", f"/listings/{listing_id}")
    assert result["id"] == listing_id


@pytest.mark.asyncio
async def test_delete_listing_then_get_returns_404():
    created = await dispatch(
        "POST", "/listings", {"ticker": "NVDA", "price": 400.0, "company": "Nvidia"}
    )
    listing_id = created["id"]
    await dispatch("DELETE", f"/listings/{listing_id}")
    result = await dispatch("GET", f"/listings/{listing_id}")
    assert result["status_code"] == 404


@pytest.mark.asyncio
async def test_delete_listing_not_found_returns_404():
    result = await dispatch("DELETE", "/listings/888888")
    assert result["status_code"] == 404


# --- Orders: create ---


@pytest.mark.asyncio
async def test_create_order_buy():
    listing = await dispatch(
        "POST", "/listings", {"ticker": "AMD", "price": 120.0, "company": "AMD"}
    )
    result = await dispatch(
        "POST",
        "/orders",
        {"listing_id": listing["id"], "side": "buy", "quantity": 10, "price": 120.0},
    )
    assert "id" in result
    assert result["side"] == "buy"
    assert result["quantity"] == 10


@pytest.mark.asyncio
async def test_create_order_sell():
    listing = await dispatch(
        "POST", "/listings", {"ticker": "INTC", "price": 50.0, "company": "Intel"}
    )
    result = await dispatch(
        "POST",
        "/orders",
        {"listing_id": listing["id"], "side": "sell", "quantity": 5, "price": 50.0},
    )
    assert result["side"] == "sell"


@pytest.mark.asyncio
async def test_create_order_invalid_side_returns_422():
    listing = await dispatch(
        "POST", "/listings", {"ticker": "IBM", "price": 140.0, "company": "IBM"}
    )
    result = await dispatch(
        "POST",
        "/orders",
        {"listing_id": listing["id"], "side": "hold", "quantity": 1, "price": 140.0},
    )
    assert result["status_code"] == 422


@pytest.mark.asyncio
async def test_create_order_zero_quantity_returns_422():
    listing = await dispatch(
        "POST", "/listings", {"ticker": "META", "price": 200.0, "company": "Meta"}
    )
    result = await dispatch(
        "POST",
        "/orders",
        {"listing_id": listing["id"], "side": "buy", "quantity": 0, "price": 200.0},
    )
    assert result["status_code"] == 422


@pytest.mark.asyncio
async def test_create_order_nonexistent_listing_returns_404():
    result = await dispatch(
        "POST",
        "/orders",
        {"listing_id": 777777, "side": "buy", "quantity": 1, "price": 100.0},
    )
    assert result["status_code"] == 404


# --- Orders: get all ---


@pytest.mark.asyncio
async def test_get_all_orders_returns_items_key():
    result = await dispatch("GET", "/orders")
    assert "items" in result
    assert isinstance(result["items"], list)


# --- Orders: get one ---


@pytest.mark.asyncio
async def test_get_order_by_id():
    listing = await dispatch(
        "POST", "/listings", {"ticker": "SHOP", "price": 60.0, "company": "Shopify"}
    )
    order = await dispatch(
        "POST",
        "/orders",
        {"listing_id": listing["id"], "side": "buy", "quantity": 3, "price": 60.0},
    )
    result = await dispatch("GET", f"/orders/{order['id']}")
    assert result["id"] == order["id"]


@pytest.mark.asyncio
async def test_get_order_not_found_returns_404():
    result = await dispatch("GET", "/orders/999998")
    assert result["status_code"] == 404


# --- Routing ---


@pytest.mark.asyncio
async def test_unknown_path_returns_404():
    result = await dispatch("GET", "/nonexistent")
    assert result["status_code"] == 404


@pytest.mark.asyncio
async def test_method_not_allowed_returns_405():
    result = await dispatch("PATCH", "/listings")
    assert result["status_code"] == 405


# --- IDs never repeat ---


@pytest.mark.asyncio
async def test_listing_ids_are_unique():
    a = await dispatch(
        "POST", "/listings", {"ticker": "A1", "price": 1.0, "company": "A One"}
    )
    b = await dispatch(
        "POST", "/listings", {"ticker": "A2", "price": 2.0, "company": "A Two"}
    )
    assert a["id"] != b["id"]


@pytest.mark.asyncio
async def test_order_ids_are_unique():
    listing = await dispatch(
        "POST", "/listings", {"ticker": "OO", "price": 10.0, "company": "OO Corp"}
    )
    a = await dispatch(
        "POST",
        "/orders",
        {"listing_id": listing["id"], "side": "buy", "quantity": 1, "price": 10.0},
    )
    b = await dispatch(
        "POST",
        "/orders",
        {"listing_id": listing["id"], "side": "sell", "quantity": 2, "price": 10.0},
    )
    assert a["id"] != b["id"]
