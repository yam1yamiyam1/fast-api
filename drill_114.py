# =============================================================================
# CONCEPT INTRO — get_db() Session as a Dependency (deeper look)
# =============================================================================
#
# WHAT IT SOLVES:
#   You've been writing get_db() since D111. This drill makes it the focus —
#   understanding exactly what it does, why it yields, and what happens if
#   you skip it and manage sessions manually instead.
#
# YOU ALREADY KNOW THE PATTERN:
#
#   async def get_db():
#       async with SessionLocal() as session:
#           yield session
#
# WHY yield AND NOT return?
#
#   FastAPI treats any dependency that uses yield as a context manager.
#   After the route finishes, FastAPI resumes the dependency past the yield,
#   which exits the async with block and closes the session automatically.
#   If you used return, the session would never be closed.
#
#   Timeline:
#       1. Request arrives
#       2. FastAPI calls get_db()
#       3. get_db() opens a session, yields it
#       4. Route runs with the session
#       5. Route returns its response
#       6. FastAPI resumes get_db() past yield
#       7. async with block exits → session closed
#
# WHY NOT CREATE THE SESSION DIRECTLY IN THE ROUTE?
#
#   You could do this:
#       @app.get("/items")
#       async def list_items():
#           async with SessionLocal() as db:
#               result = await db.execute(select(Item))
#               return result.scalars().all()
#
#   It works — but every route duplicates the session management logic.
#   get_db() centralises it: one place to change if SessionLocal changes,
#   one place to add error handling or logging, testable via dependency override.
#
# WHAT'S NEW THIS DRILL — dependency override for testing:
#
#   In real projects you override get_db() in tests to use a test DB.
#   The pattern:
#
#   app.dependency_overrides[get_db] = override_get_db
#
#   Where override_get_db is another async generator that yields a session
#   connected to a different (e.g. in-memory) database.
#
#   SIGNATURE:
#       app.dependency_overrides : dict[Callable, Callable]
#           A dict on the FastAPI app instance. Keys are the original
#           dependency functions. Values are replacement functions.
#           FastAPI checks this dict before calling any dependency.
#
#   This drill uses dependency_overrides to swap the file DB for an
#   in-memory DB in the test block — so no .db file is created at all.
#
# IN-MEMORY SQLITE URL:
#   "sqlite+aiosqlite:///:memory:"
#   No file on disk. Wiped when the engine is disposed.
#   Each engine instance gets its own isolated in-memory DB.
#
# IMPORTANT — in-memory DB needs check_same_thread=False and
# StaticPool to work correctly with SQLAlchemy async:
#
#   from sqlalchemy.pool import StaticPool
#
#   TEST_ENGINE = create_async_engine(
#       "sqlite+aiosqlite:///:memory:",
#       connect_args={"check_same_thread": False},
#       poolclass=StaticPool,
#   )
#
#   StaticPool — reuses a single connection for the entire engine lifetime.
#               Required for in-memory SQLite because each new connection
#               would get a fresh empty DB, losing all your data.
#
#   check_same_thread=False — SQLite normally restricts a connection to the
#               thread that created it. Async code moves across threads,
#               so this restriction must be disabled.
#
# FULL TEST WIRING WITH OVERRIDE:
#
#   TEST_ENGINE = create_async_engine(
#       "sqlite+aiosqlite:///:memory:",
#       connect_args={"check_same_thread": False},
#       poolclass=StaticPool,
#   )
#   TestSessionLocal = async_sessionmaker(TEST_ENGINE, expire_on_commit=False)
#
#   async def override_get_db():
#       async with TestSessionLocal() as session:
#           yield session
#
#   async def run_tests():
#       async with TEST_ENGINE.begin() as conn:
#           await conn.run_sync(Base.metadata.create_all)
#
#       app.dependency_overrides[get_db] = override_get_db
#
#       async with ASGITransport(app=app) as transport:
#           async with AsyncClient(transport=transport, base_url="http://test") as client:
#               ...
#
#       app.dependency_overrides.clear()
#       await TEST_ENGINE.dispose()
#
# =============================================================================


# =============================================================================
# DRILL 114 — Satellite Control Room
# =============================================================================
#
# SCENARIO:
#   A satellite control room tracks active satellites in its database.
#   Operators can register satellites, list them, fetch one by ID,
#   and decommission (delete) them.
#   Tests use an in-memory SQLite DB via dependency_overrides —
#   no file is written to disk.
#
# REQUIREMENTS (ordered by dependency):
#
#   1. ENGINE + SESSION FACTORY (module level — file DB for production)
#
#      ENGINE : AsyncEngine
#          URL: "sqlite+aiosqlite:///./satellite_control_test.db", echo=False.
#
#      SessionLocal : async_sessionmaker
#          async_sessionmaker(ENGINE, expire_on_commit=False).
#
#   2. ORM MODEL
#
#      Base : DeclarativeBase — the ORM base class.
#
#      Satellite : Base
#          ORM model for the "satellites" table.
#          id     : Mapped[int] — auto-increment primary key, uniquely
#                                 identifies each satellite in the registry.
#          name   : Mapped[str] — the satellite's designation, e.g. "SAT-7A".
#          orbit  : Mapped[str] — the satellite's orbital class,
#                                 e.g. "LEO", "GEO", "MEO".
#
#   3. PYDANTIC SCHEMAS
#
#      SatelliteIn : BaseModel
#          name  : str — the satellite designation submitted by the operator.
#          orbit : str — the orbital class submitted by the operator.
#
#      SatelliteOut : BaseModel
#          id    : int — the DB-assigned ID for this satellite record.
#          name  : str — the satellite's designation as stored.
#          orbit : str — the satellite's orbital class as stored.
#          model_config = ConfigDict(from_attributes=True)
#
#   4. LIFESPAN
#
#      lifespan(app) : async context manager
#          On startup : create all tables via Base.metadata.create_all.
#          On shutdown: drop all tables via Base.metadata.drop_all, then
#                       await ENGINE.dispose().
#
#   5. DATABASE DEPENDENCY
#
#      get_db() : async generator
#          Yields one AsyncSession per request via async with SessionLocal().
#
#   6. ROUTES
#
#      POST /satellites
#          body : SatelliteIn  — satellite data submitted by the operator.
#          db   : AsyncSession — DB session injected by Depends(get_db).
#          Behaviour: create Satellite, add, commit, refresh, return.
#          response_model : SatelliteOut
#          status_code    : 201
#
#      GET /satellites
#          db   : AsyncSession — DB session injected by Depends(get_db).
#          Behaviour: select all Satellite rows, return as list.
#          response_model : list[SatelliteOut]
#
#      GET /satellites/{satellite_id}
#          satellite_id : int  — the DB ID of the satellite to retrieve.
#          db : AsyncSession   — DB session injected by Depends(get_db).
#          Behaviour: fetch Satellite by satellite_id. If not found, 404.
#          response_model : SatelliteOut
#
#      DELETE /satellites/{satellite_id}
#          satellite_id : int  — the DB ID of the satellite to decommission.
#          db : AsyncSession   — DB session injected by Depends(get_db).
#          Behaviour: fetch Satellite by satellite_id. If not found, 404.
#                     Delete, commit, return {"detail": "decommissioned"}.
#
# =============================================================================


import asyncio  # noqa: F401
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
from sqlalchemy.pool import StaticPool  # noqa: F401

# --- YOUR CODE HERE ---
ENGINE = create_async_engine(
    url="sqlite+aiosqlite:///./satellite_control_test.db", echo=False
)
SessionLocal = async_sessionmaker(ENGINE, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Satellite(Base):
    __tablename__ = "satellites"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    orbit: Mapped[str] = mapped_column()


class SatelliteIn(BaseModel):
    name: str
    orbit: str


class SatelliteOut(BaseModel):
    id: int
    name: str
    orbit: str
    model_config = ConfigDict(from_attributes=True)


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


@app.post("/satellites", response_model=SatelliteOut, status_code=201)
async def add_satellite(body: SatelliteIn, db: AsyncSession = Depends(get_db)):
    satellite = Satellite(**body.model_dump())
    db.add(satellite)
    await db.commit()
    await db.refresh(satellite)
    return satellite


@app.get("/satellites", response_model=list[SatelliteOut])
async def get_satellites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Satellite))
    return result.scalars().all()


@app.get("/satellites/{satellite_id}", response_model=SatelliteOut)
async def get_satellite(satellite_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Satellite).where(Satellite.id == satellite_id))
    satellite = result.scalar_one_or_none()
    if satellite is None:
        raise HTTPException(status_code=404, detail="not found")
    return satellite


@app.delete("/satellites/{satellite_id}")
async def delete_satellite(satellite_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Satellite).where(Satellite.id == satellite_id))
    satellite = result.scalar_one_or_none()
    if satellite is None:
        raise HTTPException(status_code=404, detail="not found")
    await db.delete(satellite)
    await db.commit()
    return {"detail": "decommissioned"}


# =============================================================================
# TESTS — do not modify
# =============================================================================

TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(TEST_ENGINE, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


async def run_tests():
    # create tables in the in-memory test DB
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # noqa: F821

    # swap get_db with the test version
    app.dependency_overrides[get_db] = override_get_db  # noqa: F821

    async with ASGITransport(app=app) as transport:  # noqa: F821
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test 1: POST /satellites registers a satellite
            print("Test 1: POST /satellites registers a satellite")
            r = await client.post(
                "/satellites", json={"name": "SAT-7A", "orbit": "LEO"}
            )
            print(f"  status={r.status_code}, body={r.json()}")
            assert r.status_code == 201
            sat_id = r.json()["id"]
            assert r.json()["name"] == "SAT-7A"
            assert r.json()["orbit"] == "LEO"
            print("  PASS")

            # Test 2: POST a second satellite
            print("Test 2: POST /satellites registers a second satellite")
            r2 = await client.post(
                "/satellites", json={"name": "GEO-3B", "orbit": "GEO"}
            )
            print(f"  status={r2.status_code}, body={r2.json()}")
            assert r2.status_code == 201
            print("  PASS")

            # Test 3: GET /satellites returns both
            print("Test 3: GET /satellites returns all satellites")
            r3 = await client.get("/satellites")
            print(f"  status={r3.status_code}, count={len(r3.json())}")
            assert r3.status_code == 200
            assert len(r3.json()) == 2
            print("  PASS")

            # Test 4: GET /satellites/{id} returns correct satellite
            print("Test 4: GET /satellites/{id} returns the correct satellite")
            r4 = await client.get(f"/satellites/{sat_id}")
            print(f"  status={r4.status_code}, name={r4.json()['name']}")
            assert r4.status_code == 200
            assert r4.json()["name"] == "SAT-7A"
            print("  PASS")

            # Test 5: GET /satellites/{id} returns 404 for unknown id
            print("Test 5: GET /satellites/{id} returns 404 for unknown id")
            r5 = await client.get("/satellites/999")
            print(f"  status={r5.status_code}")
            assert r5.status_code == 404
            print("  PASS")

            # Test 6: DELETE /satellites/{id} decommissions the satellite
            print("Test 6: DELETE /satellites/{id} decommissions a satellite")
            r6 = await client.delete(f"/satellites/{sat_id}")
            print(f"  status={r6.status_code}, body={r6.json()}")
            assert r6.status_code == 200
            assert r6.json()["detail"] == "decommissioned"
            print("  PASS")

            # Test 7: GET /satellites after delete returns one
            print("Test 7: GET /satellites after delete returns one satellite")
            r7 = await client.get("/satellites")
            print(f"  status={r7.status_code}, count={len(r7.json())}")
            assert r7.status_code == 200
            assert len(r7.json()) == 1
            print("  PASS")

    app.dependency_overrides.clear()  # noqa: F821
    await TEST_ENGINE.dispose()


def run_drill_114():
    asyncio.run(run_tests())


if __name__ == "__main__":
    run_drill_114()


# =============================================================================
# EXPECTED OUTPUT:
# Test 1: POST /satellites registers a satellite
#   status=201, body={'id': 1, 'name': 'SAT-7A', 'orbit': 'LEO'}
#   PASS
# Test 2: POST /satellites registers a second satellite
#   status=201, body={'id': 2, 'name': 'GEO-3B', 'orbit': 'GEO'}
#   PASS
# Test 3: GET /satellites returns all satellites
#   status=200, count=2
#   PASS
# Test 4: GET /satellites/{id} returns the correct satellite
#   status=200, name=SAT-7A
#   PASS
# Test 5: GET /satellites/{id} returns 404 for unknown id
#   status=404
#   PASS
# Test 6: DELETE /satellites/{id} decommissions a satellite
#   status=200, body={'detail': 'decommissioned'}
#   PASS
# Test 7: GET /satellites after delete returns one satellite
#   status=200, count=1
#   PASS
# =============================================================================
