import inspect  # noqa: F401

import pytest  # noqa: F401
import pytest_asyncio  # noqa: F401
from main import router  # noqa: F401


async def dispatch(method, path, body=None):
    return await router.dispatch(method, path, body)


# --- Middleware ---


@pytest.mark.asyncio
async def test_sync_middleware_runs():
    log = []

    def mw(ctx):
        log.append(ctx["method"])

    router.add_middleware(mw)
    await dispatch("GET", "/listings")
    assert "GET" in log
    router.middleware_list.clear()


@pytest.mark.asyncio
async def test_async_middleware_runs():
    log = []

    async def mw(ctx):
        log.append(ctx["path"])

    router.add_middleware(mw)
    await dispatch("GET", "/listings")
    assert "/listings" in log
    router.middleware_list.clear()


@pytest.mark.asyncio
async def test_middleware_runs_in_order():
    order = []

    def mw1(ctx):
        order.append(1)

    def mw2(ctx):
        order.append(2)

    router.add_middleware(mw1)
    router.add_middleware(mw2)
    await dispatch("GET", "/listings")
    assert order == [1, 2]
    router.middleware_list.clear()


@pytest.mark.asyncio
async def test_middleware_receives_context():
    received = {}

    def mw(ctx):
        received.update(ctx)

    router.add_middleware(mw)
    await dispatch("GET", "/listings")
    assert "method" in received
    assert "path" in received
    assert "body" in received
    router.middleware_list.clear()


@pytest.mark.asyncio
async def test_middleware_runs_before_handler():
    order = []

    def mw(ctx):
        order.append("middleware")

    router.add_middleware(mw)
    await dispatch(
        "POST", "/listings", {"ticker": "MW", "price": 1.0, "company": "MiddlewareCo"}
    )
    order.append("handler_done")
    assert order[0] == "middleware"
    router.middleware_list.clear()


# --- Dependencies ---


@pytest.mark.asyncio
async def test_sync_dep_injected():
    def get_role():
        return "admin"

    listing = await dispatch(
        "POST", "/listings", {"ticker": "DEP", "price": 1.0, "company": "DepCo"}
    )
    listing_id = listing["id"]

    received = {}

    async def handler_with_dep(id, role):
        received["role"] = role
        return {"id": id, "ticker": "X", "price": 1.0, "company": "X"}

    from models import ListingResponse
    from router import Router

    r = Router()
    r.register(
        "GET",
        "/test/{id}",
        handler_with_dep,
        None,
        ListingResponse,
        deps={"role": get_role},
    )
    result = await r.dispatch("GET", f"/test/{listing_id}", None)
    assert received["role"] == "admin"


@pytest.mark.asyncio
async def test_async_dep_injected():
    async def get_user():
        return "alice"

    received = {}

    async def handler_with_dep(id, user):
        received["user"] = user
        return {"id": id, "ticker": "X", "price": 1.0, "company": "X"}

    from models import ListingResponse
    from router import Router

    r = Router()
    r.register(
        "GET",
        "/test/{id}",
        handler_with_dep,
        None,
        ListingResponse,
        deps={"user": get_user},
    )
    listing = await dispatch(
        "POST", "/listings", {"ticker": "AD", "price": 1.0, "company": "AsyncDepCo"}
    )
    result = await r.dispatch("GET", f"/test/{listing['id']}", None)
    assert received["user"] == "alice"


@pytest.mark.asyncio
async def test_multiple_deps_all_injected():
    def get_a():
        return "A"

    def get_b():
        return "B"

    received = {}

    async def handler_with_deps(id, a, b):
        received["a"] = a
        received["b"] = b
        return {"id": id, "ticker": "X", "price": 1.0, "company": "X"}

    from models import ListingResponse
    from router import Router

    r = Router()
    r.register(
        "GET",
        "/test/{id}",
        handler_with_deps,
        None,
        ListingResponse,
        deps={"a": get_a, "b": get_b},
    )
    listing = await dispatch(
        "POST", "/listings", {"ticker": "MD", "price": 1.0, "company": "MultiDepCo"}
    )
    await r.dispatch("GET", f"/test/{listing['id']}", None)
    assert received == {"a": "A", "b": "B"}


@pytest.mark.asyncio
async def test_no_deps_still_works():
    result = await dispatch("GET", "/listings")
    assert "items" in result


@pytest.mark.asyncio
async def test_deps_injected_alongside_path_param():
    def get_tag():
        return "tagged"

    received = {}

    async def handler(id, tag):
        received["id"] = id
        received["tag"] = tag
        return {"id": id, "ticker": "X", "price": 1.0, "company": "X"}

    from models import ListingResponse
    from router import Router

    r = Router()
    r.register(
        "GET", "/test/{id}", handler, None, ListingResponse, deps={"tag": get_tag}
    )
    listing = await dispatch(
        "POST", "/listings", {"ticker": "TP", "price": 1.0, "company": "TagPathCo"}
    )
    await r.dispatch("GET", f"/test/{listing['id']}", None)
    assert received["tag"] == "tagged"
    assert received["id"] == listing["id"]
