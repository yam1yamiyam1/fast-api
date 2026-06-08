import pytest
import pytest_asyncio

from app.router import Router
from app.models import GuestCreate, GuestResponse
from app.exceptions import NotFoundException
import app.routes.guests as guest_routes
import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reset_store():
    main.guest_store.clear()
    main.room_store.clear()
    main.guest_id_counter["value"] = 1
    main.room_id_counter["value"] = 1


@pytest_asyncio.fixture(autouse=True)
async def clean_store():
    reset_store()
    yield
    reset_store()


# ---------------------------------------------------------------------------
# Middleware — before hooks
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_middleware_runs_before_handler():
    log = []

    async def logger_middleware(method, path, body):
        log.append(f"before:{method}:{path}")

    r = Router()
    r.add_middleware(logger_middleware)
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    assert log == ["before:POST:/guests"]


@pytest.mark.asyncio
async def test_multiple_middleware_run_in_order():
    log = []

    async def mw1(method, path, body):
        log.append("mw1")

    async def mw2(method, path, body):
        log.append("mw2")

    r = Router()
    r.add_middleware(mw1)
    r.add_middleware(mw2)
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    assert log == ["mw1", "mw2"]


@pytest.mark.asyncio
async def test_middleware_receives_correct_args():
    received = {}

    async def capture_middleware(method, path, body):
        received["method"] = method
        received["path"] = path
        received["body"] = body

    r = Router()
    r.add_middleware(capture_middleware)
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    assert received["method"] == "POST"
    assert received["path"] == "/guests"
    assert received["body"] == {"name": "Amara Osei", "email": "a@hotel.com"}


@pytest.mark.asyncio
async def test_middleware_runs_even_on_not_found():
    log = []

    async def logger_middleware(method, path, body):
        log.append(f"before:{path}")

    r = Router()
    r.add_middleware(logger_middleware)

    with pytest.raises(NotFoundException):
        await r.dispatch("GET", "/nonexistent", None)

    assert log == ["before:/nonexistent"]


@pytest.mark.asyncio
async def test_sync_middleware_supported():
    log = []

    def sync_mw(method, path, body):
        log.append("sync")

    r = Router()
    r.add_middleware(sync_mw)
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    assert log == ["sync"]


# ---------------------------------------------------------------------------
# Middleware — abort by raising
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_middleware_can_abort_request():
    from app.exceptions import AppException

    async def reject_all(method, path, body):
        raise AppException("blocked")

    r = Router()
    r.add_middleware(reject_all)
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    with pytest.raises(AppException) as exc_info:
        await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    assert "blocked" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Dependencies — injected into handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dependency_result_passed_to_handler():
    received = {}

    async def get_hotel_name():
        return "Grand Harbour"

    async def handler(hotel_name, **kwargs):
        received["hotel_name"] = hotel_name

    r = Router()
    r.register("GET", "/info", handler, None, None,
               deps={"hotel_name": get_hotel_name})

    await r.dispatch("GET", "/info", None)
    assert received["hotel_name"] == "Grand Harbour"


@pytest.mark.asyncio
async def test_multiple_dependencies_all_injected():
    received = {}

    async def dep_a():
        return "A"

    async def dep_b():
        return "B"

    async def handler(val_a, val_b, **kwargs):
        received["a"] = val_a
        received["b"] = val_b

    r = Router()
    r.register("GET", "/info", handler, None, None,
               deps={"val_a": dep_a, "val_b": dep_b})

    await r.dispatch("GET", "/info", None)
    assert received["a"] == "A"
    assert received["b"] == "B"


@pytest.mark.asyncio
async def test_sync_dependency_supported():
    received = {}

    def get_floor_count():
        return 20

    async def handler(floors, **kwargs):
        received["floors"] = floors

    r = Router()
    r.register("GET", "/info", handler, None, None,
               deps={"floors": get_floor_count})

    await r.dispatch("GET", "/info", None)
    assert received["floors"] == 20


@pytest.mark.asyncio
async def test_dependency_runs_per_request():
    counter = {"n": 0}

    async def incrementing_dep():
        counter["n"] += 1
        return counter["n"]

    async def handler(call_number, **kwargs):
        pass

    r = Router()
    r.register("GET", "/info", handler, None, None,
               deps={"call_number": incrementing_dep})

    await r.dispatch("GET", "/info", None)
    await r.dispatch("GET", "/info", None)
    assert counter["n"] == 2


@pytest.mark.asyncio
async def test_chained_dependency():
    """A dependency that calls another dependency."""

    async def get_base_rate():
        return 100

    async def get_discounted_rate():
        base = await get_base_rate()
        return base * 0.9

    async def handler(rate, **kwargs):
        pass

    received = {}

    async def capturing_handler(rate, **kwargs):
        received["rate"] = rate

    r = Router()
    r.register("GET", "/rate", capturing_handler, None, None,
               deps={"rate": get_discounted_rate})

    await r.dispatch("GET", "/rate", None)
    assert received["rate"] == 90.0


# ---------------------------------------------------------------------------
# Middleware + Dependencies together
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_middleware_runs_before_dependencies():
    log = []

    async def mw(method, path, body):
        log.append("middleware")

    async def dep():
        log.append("dependency")
        return "value"

    async def handler(val, **kwargs):
        log.append("handler")

    r = Router()
    r.add_middleware(mw)
    r.register("GET", "/info", handler, None, None, deps={"val": dep})

    await r.dispatch("GET", "/info", None)
    assert log == ["middleware", "dependency", "handler"]


@pytest.mark.asyncio
async def test_full_pipeline_with_existing_routes():
    """Middleware + deps wired alongside the existing guest routes."""
    log = []

    async def audit_log(method, path, body):
        log.append(f"{method} {path}")

    async def get_desk_agent():
        return "Agent_007"

    r = Router()
    r.add_middleware(audit_log)
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    result = await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    assert result["name"] == "Amara Osei"
    assert log == ["POST /guests"]
