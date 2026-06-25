# =============================================================================
# CONCEPT INTRO — CRUD (Create, Read, Update, Delete)
# =============================================================================
#
# WHAT IT SOLVES:
#   The four fundamental DB operations every API needs.
#   You already know Create (POST) and Read (GET) from D111–D112.
#   This drill adds Update (PUT) and Delete (DELETE).
#
# NO NEW IMPORTS — everything comes from sqlalchemy and fastapi already seen.
#
# NEW OPERATIONS:
#
# --- UPDATE ---
#
#   To update a row:
#       1. fetch the row first (get by id)
#       2. mutate the ORM object's fields directly
#       3. commit
#       4. refresh
#
#   result = await db.execute(select(Model).where(Model.id == id))
#   obj = result.scalar_one_or_none()
#   if obj is None:
#       raise HTTPException(status_code=404, detail="not found")
#   obj.field = new_value          # mutate in place — no db.add() needed
#   await db.commit()
#   await db.refresh(obj)
#   return obj
#
#   Why no db.add()? The object is already tracked by the session
#   (you loaded it from the DB). Mutating it marks it dirty automatically.
#   db.add() is only needed for new objects not yet in the session.
#
# --- DELETE ---
#
#   To delete a row:
#       1. fetch the row first
#       2. call await db.delete(obj)
#       3. commit
#
#   result = await db.execute(select(Model).where(Model.id == id))
#   obj = result.scalar_one_or_none()
#   if obj is None:
#       raise HTTPException(status_code=404, detail="not found")
#   await db.delete(obj)           # coroutine — must await
#   await db.commit()
#   return {"detail": "deleted"}
#
# SIGNATURE REFERENCE:
#
#   await db.delete(instance: DeclarativeBase) -> None
#       Stages the object for deletion. Must be followed by await db.commit().
#
#   result.scalar_one_or_none() -> Model | None
#       Returns the single ORM object from the result, or None if not found.
#
#   select(Model).where(Model.field == value) -> Select
#       Adds a WHERE clause to the SELECT query.
#
# FULL CRUD SUMMARY:
#
#   Create : db.add(obj) → await db.commit() → await db.refresh(obj)
#   Read   : await db.execute(select(Model)) → result.scalars().all()
#   Read 1 : await db.execute(select(Model).where(...)) → scalar_one_or_none()
#   Update : fetch → mutate fields → await db.commit() → await db.refresh()
#   Delete : fetch → await db.delete(obj) → await db.commit()
#
# =============================================================================


# =============================================================================
# DRILL 113 — Broadcast Studio
# =============================================================================
#
# SCENARIO:
#   A broadcast studio manages its show schedule in a database.
#   Producers can add new shows, list all shows, update a show's title
#   or time slot, and remove cancelled shows.
#   Full CRUD on a single "shows" table.
#
# REQUIREMENTS (ordered by dependency):
#
#   1. ENGINE + SESSION FACTORY (module level)
#
#      ENGINE : AsyncEngine
#          URL: "sqlite+aiosqlite:///./broadcast_studio_test.db", echo=False.
#
#      SessionLocal : async_sessionmaker
#          async_sessionmaker(ENGINE, expire_on_commit=False).
#
#   2. ORM MODEL
#
#      Base : DeclarativeBase — the ORM base class.
#
#      Show : Base
#          ORM model for the "shows" table.
#          id       : Mapped[int] — auto-increment primary key, uniquely
#                                   identifies each show in the schedule.
#          title    : Mapped[str] — the show's broadcast title.
#          timeslot : Mapped[str] — the show's scheduled air time,
#                                   e.g. "Mon 20:00".
#
#   3. PYDANTIC SCHEMAS
#
#      ShowIn : BaseModel
#          title    : str — the show title submitted by the producer.
#          timeslot : str — the scheduled air time submitted by the producer.
#
#      ShowUpdate : BaseModel
#          title    : str | None = None — updated title, if provided.
#          timeslot : str | None = None — updated timeslot, if provided.
#          Only fields that are not None should be applied to the record.
#
#      ShowOut : BaseModel
#          id       : int — the DB-assigned ID for this show.
#          title    : str — the show's title as stored.
#          timeslot : str — the show's timeslot as stored.
#          model_config = ConfigDict(from_attributes=True)
#
#   4. LIFESPAN
#
#      lifespan(app) : async context manager
#          On startup : create all tables via
#                       conn.run_sync(Base.metadata.create_all).
#          On shutdown: drop all tables via
#                       conn.run_sync(Base.metadata.drop_all), then
#                       await ENGINE.dispose().
#
#   5. DATABASE DEPENDENCY
#
#      get_db() : async generator
#          Yields one AsyncSession per request via async with SessionLocal().
#
#   6. ROUTES
#
#      POST /shows
#          body : ShowIn       — show data submitted by the producer.
#          db   : AsyncSession — DB session injected by Depends(get_db).
#          Behaviour: create Show, add, commit, refresh, return.
#          response_model : ShowOut
#          status_code    : 201
#
#      GET /shows
#          db   : AsyncSession — DB session injected by Depends(get_db).
#          Behaviour: select all Show rows, return as list.
#          response_model : list[ShowOut]
#
#      GET /shows/{show_id}
#          show_id : int       — the DB ID of the show to retrieve.
#          db      : AsyncSession — DB session injected by Depends(get_db).
#          Behaviour: fetch Show by show_id. If not found, raise 404.
#          response_model : ShowOut
#
#      PUT /shows/{show_id}
#          show_id : int       — the DB ID of the show to update.
#          body    : ShowUpdate — fields to update; only non-None fields applied.
#          db      : AsyncSession — DB session injected by Depends(get_db).
#          Behaviour: fetch Show by show_id. If not found, raise 404.
#                     Apply non-None fields from body to the ORM object.
#                     Commit, refresh, return.
#          response_model : ShowOut
#
#      DELETE /shows/{show_id}
#          show_id : int       — the DB ID of the show to delete.
#          db      : AsyncSession — DB session injected by Depends(get_db).
#          Behaviour: fetch Show by show_id. If not found, raise 404.
#                     Delete, commit, return {"detail": "deleted"}.
#
# =============================================================================


import asyncio  # noqa: F401
import os  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401

from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
from httpx import ASGITransport, AsyncClient  # noqa: F401
from pydantic import BaseModel, ConfigDict  # noqa: F401
from sqlalchemy import select  # noqa: F401
from sqlalchemy.ext.asyncio import (  # noqa: F401
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # noqa: F401

# --- YOUR CODE HERE ---
ENGINE = create_async_engine(
    url="sqlite+aiosqlite:///./broadcast_studio_test.db", echo=False
)
SessionLocal = async_sessionmaker(ENGINE, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Show(Base):
    __tablename__ = "shows"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    timeslot: Mapped[str] = mapped_column()


class ShowIn(BaseModel):
    title: str
    timeslot: str


class ShowUpdate(BaseModel):
    title: str | None = None
    timeslot: str | None = None


class ShowOut(BaseModel):
    id: int
    title: str
    timeslot: str
    model_config = ConfigDict(from_attributes=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await ENGINE.dispose()


async def get_db():
    async with SessionLocal() as session:
        yield session


app = FastAPI(lifespan=lifespan)


@app.post("/shows", response_model=ShowOut, status_code=201)
async def add_show(body: ShowIn, db: AsyncSession = Depends(get_db)):
    show = Show(**body.model_dump())
    db.add(show)
    await db.commit()
    await db.refresh(show)
    return show


@app.get("/shows", response_model=list[ShowOut])
async def get_shows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Show))
    return result.scalars().all()


@app.get("/shows/{show_id}", response_model=ShowOut)
async def get_show(show_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if show is None:
        raise HTTPException(status_code=404, detail="not found")
    return show


@app.put("/shows/{show_id}", response_model=ShowOut)
async def update_show(
    show_id: int, body: ShowUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if show is None:
        raise HTTPException(status_code=404, detail="not found")
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(show, k, v)
    await db.commit()
    await db.refresh(show)
    return show


@app.delete("/shows/{show_id}")
async def delete_show(show_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if show is None:
        raise HTTPException(status_code=404, detail="not found")
    await db.delete(show)
    await db.commit()
    return {"detail": "deleted"}


# =============================================================================
# TESTS — do not modify
# =============================================================================


async def run_tests():
    # manually run migrations — ASGITransport does not fire lifespan
    async with ENGINE.begin() as conn:  # noqa: F821
        await conn.run_sync(Base.metadata.create_all)  # noqa: F821

    async with ASGITransport(app=app) as transport:  # noqa: F821
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test 1: POST /shows creates a show
            print("Test 1: POST /shows creates a show")
            r = await client.post(
                "/shows", json={"title": "Morning News", "timeslot": "Mon 07:00"}
            )
            print(f"  status={r.status_code}, body={r.json()}")
            assert r.status_code == 201
            show_id = r.json()["id"]
            assert r.json()["title"] == "Morning News"
            assert r.json()["timeslot"] == "Mon 07:00"
            print("  PASS")

            # Test 2: POST a second show
            print("Test 2: POST /shows creates a second show")
            r2 = await client.post(
                "/shows", json={"title": "Evening Drama", "timeslot": "Tue 20:00"}
            )
            print(f"  status={r2.status_code}, body={r2.json()}")
            assert r2.status_code == 201
            print("  PASS")

            # Test 3: GET /shows returns both shows
            print("Test 3: GET /shows returns all shows")
            r3 = await client.get("/shows")
            print(f"  status={r3.status_code}, count={len(r3.json())}")
            assert r3.status_code == 200
            assert len(r3.json()) == 2
            print("  PASS")

            # Test 4: GET /shows/{id} returns correct show
            print("Test 4: GET /shows/{id} returns the correct show")
            r4 = await client.get(f"/shows/{show_id}")
            print(f"  status={r4.status_code}, title={r4.json()['title']}")
            assert r4.status_code == 200
            assert r4.json()["title"] == "Morning News"
            print("  PASS")

            # Test 5: GET /shows/{id} returns 404 for missing show
            print("Test 5: GET /shows/{id} returns 404 for unknown id")
            r5 = await client.get("/shows/999")
            print(f"  status={r5.status_code}")
            assert r5.status_code == 404
            print("  PASS")

            # Test 6: PUT /shows/{id} updates title only
            print("Test 6: PUT /shows/{id} updates title only")
            r6 = await client.put(f"/shows/{show_id}", json={"title": "Morning Update"})
            print(f"  status={r6.status_code}, body={r6.json()}")
            assert r6.status_code == 200
            assert r6.json()["title"] == "Morning Update"
            assert r6.json()["timeslot"] == "Mon 07:00"
            print("  PASS")

            # Test 7: DELETE /shows/{id} removes the show
            print("Test 7: DELETE /shows/{id} removes the show")
            r7 = await client.delete(f"/shows/{show_id}")
            print(f"  status={r7.status_code}, body={r7.json()}")
            assert r7.status_code == 200
            assert r7.json()["detail"] == "deleted"
            print("  PASS")

            # Test 8: GET /shows after delete returns only one show
            print("Test 8: GET /shows after delete returns one show")
            r8 = await client.get("/shows")
            print(f"  status={r8.status_code}, count={len(r8.json())}")
            assert r8.status_code == 200
            assert len(r8.json()) == 1
            print("  PASS")

    # dispose before file removal to release Windows file lock
    await ENGINE.dispose()  # noqa: F821
    if os.path.exists("broadcast_studio_test.db"):
        os.remove("broadcast_studio_test.db")


def run_drill_113():
    asyncio.run(run_tests())


if __name__ == "__main__":
    run_drill_113()


# =============================================================================
# EXPECTED OUTPUT:
# Test 1: POST /shows creates a show
#   status=201, body={'id': 1, 'title': 'Morning News', 'timeslot': 'Mon 07:00'}
#   PASS
# Test 2: POST /shows creates a second show
#   status=201, body={'id': 2, 'title': 'Evening Drama', 'timeslot': 'Tue 20:00'}
#   PASS
# Test 3: GET /shows returns all shows
#   status=200, count=2
#   PASS
# Test 4: GET /shows/{id} returns the correct show
#   status=200, title=Morning News
#   PASS
# Test 5: GET /shows/{id} returns 404 for unknown id
#   status=404
#   PASS
# Test 6: PUT /shows/{id} updates title only
#   status=200, body={'id': 1, 'title': 'Morning Update', 'timeslot': 'Mon 07:00'}
#   PASS
# Test 7: DELETE /shows/{id} removes the show
#   status=200, body={'detail': 'deleted'}
#   PASS
# Test 8: GET /shows after delete returns one show
#   status=200, count=1
#   PASS
# =============================================================================
