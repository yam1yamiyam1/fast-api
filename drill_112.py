# =============================================================================
# CONCEPT INTRO — Alembic Migrations (NEW)
# =============================================================================
#
# WHAT IT SOLVES:
#   Tracks every change to your DB schema as versioned migration files.
#   Instead of dropping and recreating tables, you apply incremental changes
#   (add column, rename table, etc.) without losing existing data.
#
# INSTALL (run once):
#   pip install alembic
#
# --- BUT FOR DRILLS WE DON'T USE THE CLI ---
#
#   In production you run: alembic init, alembic revision, alembic upgrade head
#   In drills we simulate the same thing programmatically so tests are
#   self-contained and need no external files.
#
# NEW IMPORTS:
#
#   from alembic.runtime.migration import MigrationContext
#       MigrationContext.configure(conn) — wraps a live connection so
#       Alembic Operations can run against it
#
#   from alembic.operations import Operations
#       op = Operations(context)
#       op.create_table(...)   — create a table
#       op.add_column(...)     — add a column to an existing table
#       op.drop_table(...)     — drop a table
#
# SIGNATURE REFERENCE:
#
#   MigrationContext.configure(
#       connection: Connection,
#   ) -> MigrationContext
#
#   Operations(migration_context: MigrationContext) -> Operations
#
#   op.create_table(
#       table_name: str,
#       *columns: sa.Column,
#   ) -> Table
#
#   op.add_column(
#       table_name: str,
#       column: sa.Column,
#   ) -> None
#
#   op.drop_table(table_name: str) -> None
#
#   sa.Column(
#       name: str,
#       type_: sa.types,
#       primary_key: bool = False,
#       nullable: bool = True,
#   )
#
# HOW TO USE (programmatic, no CLI):
#
#   To define a migration:
#       def run_migrations(conn):
#           context = MigrationContext.configure(conn)
#           op = Operations(context)
#           op.create_table(
#               "patients",
#               sa.Column("id", sa.Integer, primary_key=True),
#               sa.Column("name", sa.String, nullable=False),
#               sa.Column("species", sa.String, nullable=False),
#           )
#
#   To define a rollback:
#       def run_rollback(conn):
#           context = MigrationContext.configure(conn)
#           op = Operations(context)
#           op.drop_table("patients")
#
#   To run them:
#       async with ENGINE.begin() as conn:
#           await conn.run_sync(run_migrations)
#
#       async with ENGINE.begin() as conn:
#           await conn.run_sync(run_rollback)
#
#   Two separate ENGINE.begin() blocks — one per operation.
#   Each block is a short-lived transaction: open → do work → close.
#   You cannot share one block across startup and shutdown.
#
# PURE PYTHON TRANSLATION:
#   D111 (create_all):                        D112 (Alembic programmatic):
#   await conn.run_sync(                      await conn.run_sync(run_migrations)
#       Base.metadata.create_all)             where run_migrations uses Operations
#   — recreates ALL tables at once            — one table at a time, reversible
#   — no version tracking                     — explicit, fine-grained control
#
# =============================================================================


# =============================================================================
# DRILL 112 — Veterinary Clinic
# =============================================================================
#
# SCENARIO:
#   A veterinary clinic is setting up its patient database.
#   The schema is managed via Alembic-style programmatic migrations —
#   no CLI, no migration files on disk.
#   On startup, a migration function creates the "patients" table.
#   On shutdown, a rollback function drops it.
#   Staff can register new animal patients and list all of them.
#
# REQUIREMENTS (ordered by dependency):
#
#   1. SQLALCHEMY IMPORTS
#
#      Import sqlalchemy as sa — used to declare column types inside
#      Alembic Operations calls (sa.Integer, sa.String, sa.Column).
#
#   2. ENGINE + SESSION FACTORY (module level)
#
#      ENGINE : AsyncEngine
#          Created with create_async_engine using the URL
#          "sqlite+aiosqlite:///./vet_clinic_test.db" and echo=False.
#
#      SessionLocal : async_sessionmaker
#          Created with async_sessionmaker(ENGINE, expire_on_commit=False).
#
#   3. ORM MODEL
#
#      Base : DeclarativeBase — the ORM base class.
#
#      Patient : Base
#          ORM model for the "patients" table.
#          id      : Mapped[int] — auto-increment primary key, uniquely
#                                  identifies each animal patient in the DB.
#          name    : Mapped[str] — the animal's name as registered by staff.
#          species : Mapped[str] — the animal's species, e.g. "cat" or "dog".
#
#   4. PYDANTIC SCHEMAS
#
#      PatientIn : BaseModel
#          name    : str — the animal's name submitted by the client.
#          species : str — the animal's species submitted by the client.
#
#      PatientOut : BaseModel
#          id      : int — the DB-assigned ID for this patient record.
#          name    : str — the animal's name as stored.
#          species : str — the animal's species as stored.
#          model_config = ConfigDict(from_attributes=True)
#
#   5. MIGRATION FUNCTIONS (sync — passed to conn.run_sync)
#
#      run_migrations(conn) -> None
#          conn : Connection — the live sync connection provided by run_sync.
#          Creates the "patients" table with columns:
#              id      : sa.Integer, primary_key=True
#              name    : sa.String,  nullable=False
#              species : sa.String,  nullable=False
#          Uses MigrationContext.configure(conn) and Operations.
#
#      run_rollback(conn) -> None
#          conn : Connection — the live sync connection provided by run_sync.
#          Drops the "patients" table using op.drop_table("patients").
#          Uses MigrationContext.configure(conn) and Operations.
#
#   6. LIFESPAN
#
#      lifespan(app) : async context manager
#          app : FastAPI — the application instance.
#          On startup : opens ENGINE.begin() and calls
#                       conn.run_sync(run_migrations).
#          On shutdown: opens ENGINE.begin() and calls
#                       conn.run_sync(run_rollback), then
#                       await ENGINE.dispose().
#          The FastAPI app must be created with lifespan=lifespan.
#
#   7. DATABASE DEPENDENCY
#
#      get_db() : async generator
#          Yields one AsyncSession per request via async with SessionLocal().
#
#   8. ROUTES
#
#      POST /patients
#          body : PatientIn      — registration data submitted by the client.
#          db   : AsyncSession   — DB session injected by Depends(get_db).
#          Behaviour: construct a Patient ORM object from body, add, commit,
#                     refresh, return.
#          response_model : PatientOut
#          status_code    : 201
#
#      GET /patients
#          db   : AsyncSession   — DB session injected by Depends(get_db).
#          Behaviour: execute select(Patient), return all rows as a list.
#          response_model : list[PatientOut]
#
# =============================================================================


import asyncio  # noqa: F401
import os  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401

import sqlalchemy as sa  # noqa: F401
from alembic.operations import Operations  # noqa: F401
from alembic.runtime.migration import MigrationContext  # noqa: F401
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
ENGINE = create_async_engine(url="sqlite+aiosqlite:///./vet_clinic_test.db", echo=False)

SessionLocal = async_sessionmaker(ENGINE, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    species: Mapped[str] = mapped_column()


class PatientIn(BaseModel):
    name: str
    species: str


class PatientOut(BaseModel):
    id: int
    name: str
    species: str
    model_config = ConfigDict(from_attributes=True)


def run_migrations(conn):
    context = MigrationContext.configure(conn)
    op = Operations(context)
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("species", sa.String, nullable=False),
    )


def run_rollback(conn):
    context = MigrationContext.configure(conn)
    op = Operations(context)
    op.drop_table("patients")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with ENGINE.begin() as conn:
        await conn.run_sync(run_migrations)
    yield
    async with ENGINE.begin() as conn:
        await conn.run_sync(run_rollback)
    await ENGINE.dispose()


async def get_db():
    async with SessionLocal() as session:
        yield session


app = FastAPI(lifespan=lifespan)


@app.post("/patients", response_model=PatientOut, status_code=201)
async def add_patient(body: PatientIn, db: AsyncSession = Depends(get_db)):
    patient = Patient(**body.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@app.get("/patients", response_model=list[PatientOut])
async def get_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient))
    return result.scalars().all()


# =============================================================================
# TESTS — do not modify
# =============================================================================


async def run_tests():
    # manually run migrations — ASGITransport does not fire lifespan
    async with ENGINE.begin() as conn:  # noqa: F821
        await conn.run_sync(run_migrations)  # noqa: F821

    async with ASGITransport(app=app) as transport:  # noqa: F821
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test 1: POST /patients returns 201 and correct fields
            print("Test 1: POST /patients registers a patient and returns 201")
            r = await client.post("/patients", json={"name": "Mochi", "species": "cat"})
            print(f"  status={r.status_code}, body={r.json()}")
            assert r.status_code == 201
            data = r.json()
            assert data["name"] == "Mochi"
            assert data["species"] == "cat"
            assert isinstance(data["id"], int)
            print("  PASS")

            # Test 2: POST a second patient
            print("Test 2: POST /patients registers a second patient")
            r2 = await client.post(
                "/patients", json={"name": "Bruno", "species": "dog"}
            )
            print(f"  status={r2.status_code}, body={r2.json()}")
            assert r2.status_code == 201
            assert r2.json()["name"] == "Bruno"
            print("  PASS")

            # Test 3: GET /patients returns both patients
            print("Test 3: GET /patients returns all registered patients")
            r3 = await client.get("/patients")
            print(f"  status={r3.status_code}, count={len(r3.json())}")
            assert r3.status_code == 200
            names = [p["name"] for p in r3.json()]
            assert "Mochi" in names
            assert "Bruno" in names
            print("  PASS")

            # Test 4: Each patient record has id, name, species
            print("Test 4: Each patient record has id, name, species")
            for patient in r3.json():
                assert "id" in patient
                assert "name" in patient
                assert "species" in patient
            print(f"  fields confirmed for {len(r3.json())} patients")
            print("  PASS")

    # dispose before file removal to release Windows file lock
    await ENGINE.dispose()  # noqa: F821
    if os.path.exists("vet_clinic_test.db"):
        os.remove("vet_clinic_test.db")


def run_drill_112():
    asyncio.run(run_tests())


if __name__ == "__main__":
    run_drill_112()


# =============================================================================
# EXPECTED OUTPUT:
# Test 1: POST /patients registers a patient and returns 201
#   status=201, body={'id': 1, 'name': 'Mochi', 'species': 'cat'}
#   PASS
# Test 2: POST /patients registers a second patient
#   status=201, body={'id': 2, 'name': 'Bruno', 'species': 'dog'}
#   PASS
# Test 3: GET /patients returns all registered patients
#   status=200, count=2
#   PASS
# Test 4: Each patient record has id, name, species
#   fields confirmed for 2 patients
#   PASS
# =============================================================================
