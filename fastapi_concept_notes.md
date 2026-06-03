# Concept Notes

## asynccontextmanager / async with / yield (introduced drill 67)

What it solves: run setup, then work, then guaranteed teardown.

Shape:

```python
@asynccontextmanager
async def lifespan():
    db = await connect()
    try:
        yield
    finally:
        await db.disconnect()

async with lifespan():
    await do_work()
```

Rules:
- Everything before yield = startup
- Everything after yield = shutdown
- Always wrap yield in try/finally
- async with = async context manager
- FastAPI uses this via the lifespan= parameter

Toy vs real FastAPI:
- Toy: APP_STATE = {} dict shared with handlers
- Real: app.state.db = ...
