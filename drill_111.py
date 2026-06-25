# =============================================================================
# CONCEPT INTRO — SQLAlchemy Async Setup (NEW)
# =============================================================================
#
# WHAT IT SOLVES:
#   Lets FastAPI talk to a real SQL database without blocking the event loop.
#   Every DB call is awaited, so other requests run while the query executes.
#
# NEW IMPORTS:
#
#   from sqlalchemy.ext.asyncio import (
#       create_async_engine,   # builds the async engine from a DB URL
#       AsyncSession,          # the async session class (used in type hints)
#       async_sessionmaker,    # factory that produces AsyncSession instances
#   )
#   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
#       DeclarativeBase  — base class all ORM models inherit from
#       Mapped[T]        — type hint for a column, e.g. Mapped[int]
#       mapped_column()  — declares a column; accepts primary_key=True, etc.
#   from sqlalchemy import select
#       select(Model)    — builds a SELECT query; replaces raw SQL strings
#
# NEW FUNCTIONS / CLASSES:
#
#   create_async_engine(url, echo=False) -> AsyncEngine
#       url    : str  — DB connection string
#                       e.g. "sqlite+aiosqlite:///./app.db"
#       echo   : bool — if True, logs every SQL statement (debug)
#       returns an engine object; does NOT open a connection yet
#
#   async_sessionmaker(engine, expire_on_commit=False) -> sessionmaker
#       engine            : AsyncEngine — the engine created above
#       expire_on_commit  : bool — False keeps ORM objects usable after commit
#       returns a factory; call it with no args to get an AsyncSession
#
#   DeclarativeBase — inherit to define ORM table models:
#       class Base(DeclarativeBase): pass
#       class MyModel(Base):
#           __tablename__ = "my_table"
#           id: Mapped[int] = mapped_column(primary_key=True)
#           name: Mapped[str]
#
#   async with engine.begin() as conn:
#       await conn.run_sync(Base.metadata.create_all)  — create all tables
#
#   async with SessionLocal() as session:
#       await session.execute(select(Model))   — run a SELECT
#       session.add(instance)                  — stage an INSERT
#       await session.commit()                 — flush to DB
#       await session.refresh(instance)        — reload from DB after insert
#
#   result.scalars().all()         — query result → plain Python list
#   result.scalar_one_or_none()    — one row or None
#
# MINIMAL WIRING EXAMPLE:
#
#   ENGINE = create_async_engine("sqlite+aiosqlite:///./app.db", echo=False)
#   SessionLocal = async_sessionmaker(ENGINE, expire_on_commit=False)
#
#   class Base(DeclarativeBase): pass
#
#   class Item(Base):
#       __tablename__ = "items"
#       id: Mapped[int] = mapped_column(primary_key=True)
#       name: Mapped[str]
#
#   @asynccontextmanager
#   async def lifespan(app: FastAPI):
#       async with ENGINE.begin() as conn:
#           await conn.run_sync(Base.metadata.create_all)
#       yield
#       await ENGINE.dispose()
#
#   async def get_db():
#       async with SessionLocal() as session:
#           yield session
#
#   @app.get("/items")
#   async def list_items(db: AsyncSession = Depends(get_db)):
#       result = await db.execute(select(Item))
#       return result.scalars().all()
#
# PURE PYTHON TRANSLATION:
#   Pure Python lifespan (D67):          FastAPI + SQLAlchemy:
#   APP_STATE["db"] = connect()     →    async with ENGINE.begin() as conn:
#   yield                           →        await conn.run_sync(Base.metadata.create_all)
#   finally: APP_STATE.clear()      →    yield  /  finally: await ENGINE.dispose()
#
#   Pure Python dep factory:             FastAPI get_db():
#   async def get_dep():            →    async def get_db():
#       resource = acquire()        →        async with SessionLocal() as session:
#       return resource             →            yield session   # yield, not return
#
# INSTALL (run once before the drill):
#   pip install sqlalchemy aiosqlite
#
# =============================================================================


# =============================================================================
# DRILL 111 — Blood Bank
# =============================================================================
#
# SCENARIO:
#   A blood bank tracks donations in a SQLite database.
#   Donors register by submitting their name and blood type.
#   Staff can list all registered donors.
#   The database is created on startup and torn down on shutdown.
#
# REQUIREMENTS (ordered by dependency):
#
#   1. DATABASE MODELS
#
#      Base : DeclarativeBase
#          The ORM base class. All table models inherit from it.
#
#      Donor : Base
#          ORM model representing a donor record in the "donors" table.
#          id         : Mapped[int]  — auto-increment primary key, uniquely
#                                      identifies each donor in the database.
#          name       : Mapped[str]  — the donor's full name as stored in the DB.
#          blood_type : Mapped[str]  — the donor's ABO+Rh blood type, e.g. "O+".
#
#   2. PYDANTIC SCHEMAS
#
#      DonorIn : BaseModel
#          Request body for registering a new donor.
#          name       : str  — the donor's full name submitted by the client.
#          blood_type : str  — the blood type submitted by the client.
#
#      DonorOut : BaseModel
#          Response shape returned to the client after registration or listing.
#          id         : int  — the database-assigned ID for this donor record.
#          name       : str  — the donor's full name as stored.
#          blood_type : str  — the donor's blood type as stored.
#          model_config = ConfigDict(from_attributes=True)
#              Enables ORM mode so FastAPI can serialize Donor ORM objects
#              directly into DonorOut without calling .model_dump() first.
#
#   3. ENGINE + SESSION FACTORY (module level, outside run_drill_111)
#
#      ENGINE : AsyncEngine
#          Created with create_async_engine using the URL
#          "sqlite+aiosqlite:///./blood_bank_test.db" and echo=False.
#          Represents the async connection pool for the blood bank database.
#
#      SessionLocal : async_sessionmaker
#          Created with async_sessionmaker(ENGINE, expire_on_commit=False).
#          A factory that produces AsyncSession instances per request.
#
#   4. LIFESPAN
#
#      lifespan(app) : async context manager
#          app : FastAPI — the application instance (required by FastAPI's
#                          lifespan signature; not used directly inside).
#          On startup : opens a connection via ENGINE.begin() and calls
#                       conn.run_sync(Base.metadata.create_all) to create
#                       the donors table if it does not exist.
#          On shutdown: calls await ENGINE.dispose() to close the pool.
#          The FastAPI app must be created with lifespan=lifespan.
#
#   5. DATABASE DEPENDENCY
#
#      get_db() : async generator
#          Yields one AsyncSession per request via async with SessionLocal().
#          The session is automatically closed when the request ends.
#          Used as Depends(get_db) in route functions.
#
#   6. ROUTES
#
#      POST /donors
#          body : DonorIn       — registration data submitted by the client.
#          db   : AsyncSession  — the DB session injected by Depends(get_db).
#          Behaviour: construct a Donor ORM object from body fields, add it
#                     to the session, commit, refresh (to load DB-assigned id),
#                     return the Donor object.
#          response_model : DonorOut
#          status_code    : 201
#
#      GET /donors
#          db   : AsyncSession  — the DB session injected by Depends(get_db).
#          Behaviour: execute select(Donor), return all rows as a list.
#          response_model : list[DonorOut]
#
# =============================================================================


import asyncio  # noqa: F401
import os  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401

from fastapi import Depends, FastAPI  # noqa: F401
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
class Base(DeclarativeBase):
    pass


class Donor(Base):
    __tablename__ = "donors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    blood_type: Mapped[str] = mapped_column()


class DonorIn(BaseModel):
    name: str
    blood_type: str


class DonorOut(BaseModel):
    id: int
    name: str
    blood_type: str
    model_config = ConfigDict(from_attributes=True)


ENGINE = create_async_engine(url="sqlite+aiosqlite:///./blood_bank_test.db", echo=False)
SessionLocal = async_sessionmaker(ENGINE, expire_on_commit=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await ENGINE.dispose()


async def get_db():
    async with SessionLocal() as session:
        yield session


app = FastAPI(lifespan=lifespan)


@app.post("/donors", response_model=DonorOut, status_code=201)
async def add_donor(body: DonorIn, db: AsyncSession = Depends(get_db)):
    donor = Donor(**body.model_dump())
    db.add(donor)
    await db.commit()
    await db.refresh(donor)
    return donor


@app.get("/donors", response_model=list[DonorOut])
async def get_donors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Donor))
    return result.scalars().all()


# =============================================================================
# TESTS — do not modify
# =============================================================================


async def run_tests():
    async with ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with ASGITransport(app=app) as transport:  # noqa: F821
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test 1: POST /donors returns 201 and correct fields
            print("Test 1: POST /donors registers a donor and returns 201")
            r = await client.post(
                "/donors", json={"name": "Ana Reyes", "blood_type": "O+"}
            )
            print(f"  status={r.status_code}, body={r.json()}")
            assert r.status_code == 201
            data = r.json()
            assert data["name"] == "Ana Reyes"
            assert data["blood_type"] == "O+"
            assert isinstance(data["id"], int)
            print("  PASS")

            # Test 2: POST a second donor
            print("Test 2: POST /donors registers a second donor")
            r2 = await client.post(
                "/donors", json={"name": "Ben Cruz", "blood_type": "A-"}
            )
            print(f"  status={r2.status_code}, body={r2.json()}")
            assert r2.status_code == 201
            assert r2.json()["name"] == "Ben Cruz"
            print("  PASS")

            # Test 3: GET /donors returns both donors
            print("Test 3: GET /donors returns all registered donors")
            r3 = await client.get("/donors")
            print(f"  status={r3.status_code}, count={len(r3.json())}")
            assert r3.status_code == 200
            names = [d["name"] for d in r3.json()]
            assert "Ana Reyes" in names
            assert "Ben Cruz" in names
            print("  PASS")

            # Test 4: Each donor record has id, name, blood_type
            print("Test 4: Each donor record has id, name, blood_type")
            for donor in r3.json():
                assert "id" in donor
                assert "name" in donor
                assert "blood_type" in donor
            print(f"  fields confirmed for {len(r3.json())} donors")
            print("  PASS")

    # cleanup
    await ENGINE.dispose()
    if os.path.exists("blood_bank_test.db"):
        os.remove("blood_bank_test.db")


def run_drill_111():
    asyncio.run(run_tests())


if __name__ == "__main__":
    run_drill_111()


# =============================================================================
# EXPECTED OUTPUT:
# Test 1: POST /donors registers a donor and returns 201
#   status=201, body={'id': 1, 'name': 'Ana Reyes', 'blood_type': 'O+'}
#   PASS
# Test 2: POST /donors registers a second donor
#   status=201, body={'id': 2, 'name': 'Ben Cruz', 'blood_type': 'A-'}
#   PASS
# Test 3: GET /donors returns all registered donors
#   status=200, count=2
#   PASS
# Test 4: Each donor record has id, name, blood_type
#   fields confirmed for 2 donors
#   PASS
# =============================================================================
