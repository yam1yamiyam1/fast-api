import asyncio
import pytest
import pytest_asyncio

from app.router import Router
from app.models import GuestCreate, GuestResponse
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
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_startup_runs_before_dispatch():
    log = []

    async def on_startup():
        log.append("startup")

    r = Router()
    r.set_lifespan(on_startup=on_startup)
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    await r.start()
    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    assert log == ["startup"]


@pytest.mark.asyncio
async def test_shutdown_runs_after_stop():
    log = []

    async def on_shutdown():
        log.append("shutdown")

    r = Router()
    r.set_lifespan(on_shutdown=on_shutdown)

    await r.start()
    await r.stop()
    assert log == ["shutdown"]


@pytest.mark.asyncio
async def test_startup_and_shutdown_both_run():
    log = []

    async def on_startup():
        log.append("startup")

    async def on_shutdown():
        log.append("shutdown")

    r = Router()
    r.set_lifespan(on_startup=on_startup, on_shutdown=on_shutdown)

    await r.start()
    await r.stop()
    assert log == ["startup", "shutdown"]


@pytest.mark.asyncio
async def test_startup_sets_shared_state():
    state = {}

    async def on_startup():
        state["db"] = "connected"

    r = Router()
    r.set_lifespan(on_startup=on_startup)

    await r.start()
    assert state["db"] == "connected"


@pytest.mark.asyncio
async def test_shutdown_cleans_shared_state():
    state = {"db": "connected"}

    async def on_shutdown():
        state["db"] = None

    r = Router()
    r.set_lifespan(on_shutdown=on_shutdown)

    await r.start()
    await r.stop()
    assert state["db"] is None


@pytest.mark.asyncio
async def test_no_lifespan_start_stop_dont_crash():
    r = Router()
    await r.start()
    await r.stop()


# ---------------------------------------------------------------------------
# Background tasks
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_background_task_runs_after_dispatch():
    log = []

    async def audit(guest_name: str):
        log.append(f"audit:{guest_name}")

    r = Router()
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    result = await r.dispatch(
        "POST", "/guests",
        {"name": "Amara Osei", "email": "a@hotel.com"},
        background=[("audit_log", audit, {"guest_name": "Amara Osei"})]
    )

    await asyncio.sleep(0.05)
    assert log == ["audit:Amara Osei"]


@pytest.mark.asyncio
async def test_multiple_background_tasks_all_run():
    log = []

    async def task_a():
        log.append("A")

    async def task_b():
        log.append("B")

    r = Router()
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    await r.dispatch(
        "POST", "/guests",
        {"name": "Amara Osei", "email": "a@hotel.com"},
        background=[
            ("task_a", task_a, {}),
            ("task_b", task_b, {}),
        ]
    )

    await asyncio.sleep(0.05)
    assert "A" in log
    assert "B" in log


@pytest.mark.asyncio
async def test_background_task_does_not_block_response():
    async def slow_task():
        await asyncio.sleep(10)

    r = Router()
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    result = await r.dispatch(
        "POST", "/guests",
        {"name": "Amara Osei", "email": "a@hotel.com"},
        background=[("slow", slow_task, {})]
    )

    assert result["name"] == "Amara Osei"


@pytest.mark.asyncio
async def test_no_background_tasks_dispatch_unchanged():
    r = Router()
    r.register("POST", "/guests", guest_routes.create_guest, GuestCreate, GuestResponse)

    result = await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    assert result["id"] == 1


# ---------------------------------------------------------------------------
# Concurrency limiting
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrency_limit_allows_up_to_limit():
    log = []

    async def handler(**kwargs):
        log.append("start")
        await asyncio.sleep(0.05)
        log.append("end")
        return {}

    r = Router(concurrency_limit=2)
    r.register("GET", "/slow", handler, None, None)

    tasks = [r.dispatch("GET", "/slow", None) for _ in range(2)]
    await asyncio.gather(*tasks)

    assert log.count("start") == 2
    assert log.count("end") == 2


@pytest.mark.asyncio
async def test_concurrency_limit_blocks_excess():
    active = {"count": 0, "max_seen": 0}

    async def handler(**kwargs):
        active["count"] += 1
        active["max_seen"] = max(active["max_seen"], active["count"])
        await asyncio.sleep(0.05)
        active["count"] -= 1
        return {}

    r = Router(concurrency_limit=2)
    r.register("GET", "/slow", handler, None, None)

    tasks = [r.dispatch("GET", "/slow", None) for _ in range(4)]
    await asyncio.gather(*tasks)

    assert active["max_seen"] <= 2


@pytest.mark.asyncio
async def test_no_concurrency_limit_by_default():
    log = []

    async def handler(**kwargs):
        log.append("ran")
        return {}

    r = Router()
    r.register("GET", "/fast", handler, None, None)

    tasks = [r.dispatch("GET", "/fast", None) for _ in range(10)]
    await asyncio.gather(*tasks)

    assert log.count("ran") == 10
