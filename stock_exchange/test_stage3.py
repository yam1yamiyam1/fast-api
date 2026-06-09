import asyncio  # noqa: F401
import pytest  # noqa: F401
import pytest_asyncio  # noqa: F401
from main import router, APP_STATE  # noqa: F401


async def dispatch(method, path, body=None, background_tasks=None):
    return await router.dispatch(method, path, body, background_tasks=background_tasks)


# --- Lifespan ---

@pytest.mark.asyncio
async def test_lifespan_start_sets_app_state():
    await router.start()
    assert APP_STATE.get("status") == "open"


@pytest.mark.asyncio
async def test_lifespan_stop_updates_app_state():
    await router.start()
    await router.stop()
    assert APP_STATE.get("status") == "closed"


@pytest.mark.asyncio
async def test_lifespan_start_stop_cycle():
    await router.start()
    assert APP_STATE["status"] == "open"
    await router.stop()
    assert APP_STATE["status"] == "closed"
    await router.start()
    assert APP_STATE["status"] == "open"
    await router.stop()


# --- Semaphore ---

@pytest.mark.asyncio
async def test_semaphore_allows_concurrent_requests():
    await router.start()
    results = await asyncio.gather(
        dispatch("GET", "/listings"),
        dispatch("GET", "/listings"),
        dispatch("GET", "/listings"),
    )
    assert all("items" in r for r in results)
    await router.stop()


@pytest.mark.asyncio
async def test_semaphore_limit_is_respected():
    from router import Router
    r = Router(max_concurrency=2)
    active = []
    peak = []

    async def slow_handler(**kwargs):
        active.append(1)
        peak.append(len(active))
        await asyncio.sleep(0.05)
        active.pop()
        return {"items": []}

    from models import ListingCollectionResponse
    r.register("GET", "/slow", slow_handler, None, ListingCollectionResponse)
    await asyncio.gather(*[r.dispatch("GET", "/slow", None) for _ in range(5)])
    assert max(peak) <= 2


# --- Background Tasks ---

@pytest.mark.asyncio
async def test_async_background_task_runs():
    await router.start()
    log = []
    async def task():
        await asyncio.sleep(0.01)
        log.append("done")
    await dispatch("GET", "/listings", background_tasks=[task])
    await asyncio.sleep(0.05)
    assert "done" in log
    await router.stop()


@pytest.mark.asyncio
async def test_sync_background_task_runs():
    await router.start()
    log = []
    def task():
        log.append("sync_done")
    await dispatch("GET", "/listings", background_tasks=[task])
    await asyncio.sleep(0.05)
    assert "sync_done" in log
    await router.stop()


@pytest.mark.asyncio
async def test_multiple_background_tasks_all_run():
    await router.start()
    log = []
    async def t1(): log.append("t1")
    async def t2(): log.append("t2")
    await dispatch("GET", "/listings", background_tasks=[t1, t2])
    await asyncio.sleep(0.05)
    assert "t1" in log
    assert "t2" in log
    await router.stop()


@pytest.mark.asyncio
async def test_background_tasks_run_after_response():
    await router.start()
    order = []
    async def task():
        await asyncio.sleep(0.01)
        order.append("task")
    result = await dispatch("GET", "/listings", background_tasks=[task])
    order.append("response_received")
    await asyncio.sleep(0.05)
    assert order[0] == "response_received"
    assert "task" in order
    await router.stop()


@pytest.mark.asyncio
async def test_no_background_tasks_still_works():
    await router.start()
    result = await dispatch("GET", "/listings")
    assert "items" in result
    await router.stop()
