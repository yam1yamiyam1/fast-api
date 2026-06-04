import pytest
import pytest_asyncio

from app.router import Router
from app.models import GuestCreate, GuestUpdate, GuestResponse, RoomCreate, RoomResponse
from app.exceptions import NotFoundException, MethodNotAllowedException, ValidationException
import app.routes.guests as guest_routes
import app.routes.rooms as room_routes
import main  # imports store


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


def make_router() -> Router:
    r = Router()
    r.register("POST",   "/guests",      guest_routes.create_guest,  GuestCreate,  GuestResponse)
    r.register("GET",    "/guests/{id}", guest_routes.get_guest,     None,         GuestResponse)
    r.register("PATCH",  "/guests/{id}", guest_routes.update_guest,  GuestUpdate,  GuestResponse)
    r.register("DELETE", "/guests/{id}", guest_routes.delete_guest,  None,         None)
    r.register("POST",   "/rooms",       room_routes.create_room,    RoomCreate,   RoomResponse)
    r.register("GET",    "/rooms/{id}",  room_routes.get_room,       None,         RoomResponse)
    return r


# ---------------------------------------------------------------------------
# Router — path matching
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_not_found():
    r = make_router()
    with pytest.raises(NotFoundException) as exc_info:
        await r.dispatch("GET", "/nonexistent", None)
    assert "Not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_dispatch_method_not_allowed():
    r = make_router()
    # POST a guest first so /guests/1 exists as a path pattern
    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@b.com"})
    with pytest.raises(MethodNotAllowedException) as exc_info:
        await r.dispatch("PUT", "/guests/1", None)
    assert "Method not allowed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_dispatch_validation_error():
    r = make_router()
    with pytest.raises(ValidationException) as exc_info:
        await r.dispatch("POST", "/guests", {"name": "", "email": "bad"})
    assert "Invalid request body" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Guest — POST /guests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_guest_returns_response():
    r = make_router()
    result = await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "amara@hotel.com"})
    assert result["id"] == 1
    assert result["name"] == "Amara Osei"
    assert result["email"] == "amara@hotel.com"
    assert result["checked_in"] is False
    assert result["room_number"] is None


@pytest.mark.asyncio
async def test_create_two_guests_increments_id():
    r = make_router()
    r1 = await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "a@hotel.com"})
    r2 = await r.dispatch("POST", "/guests", {"name": "Ben Kwame", "email": "b@hotel.com"})
    assert r1["id"] == 1
    assert r2["id"] == 2


# ---------------------------------------------------------------------------
# Guest — GET /guests/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_guest_returns_correct_guest():
    r = make_router()
    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "amara@hotel.com"})
    result = await r.dispatch("GET", "/guests/1", None)
    assert result["id"] == 1
    assert result["name"] == "Amara Osei"


@pytest.mark.asyncio
async def test_get_guest_not_found():
    r = make_router()
    with pytest.raises(NotFoundException) as exc_info:
        await r.dispatch("GET", "/guests/99", None)
    assert "Guest 99 not found" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Guest — PATCH /guests/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patch_guest_updates_name_only():
    r = make_router()
    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "amara@hotel.com"})
    result = await r.dispatch("PATCH", "/guests/1", {"name": "Amara Updated"})
    assert result["name"] == "Amara Updated"
    assert result["email"] == "amara@hotel.com"  # unchanged


@pytest.mark.asyncio
async def test_patch_guest_checked_in():
    r = make_router()
    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "amara@hotel.com"})
    result = await r.dispatch("PATCH", "/guests/1", {"checked_in": True})
    assert result["checked_in"] is True


@pytest.mark.asyncio
async def test_patch_guest_not_found():
    r = make_router()
    with pytest.raises(NotFoundException):
        await r.dispatch("PATCH", "/guests/99", {"name": "X"})


# ---------------------------------------------------------------------------
# Guest — DELETE /guests/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_guest_returns_confirmation():
    r = make_router()
    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "amara@hotel.com"})
    result = await r.dispatch("DELETE", "/guests/1", None)
    assert result["deleted"] is True
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_delete_guest_removes_from_store():
    r = make_router()
    await r.dispatch("POST", "/guests", {"name": "Amara Osei", "email": "amara@hotel.com"})
    await r.dispatch("DELETE", "/guests/1", None)
    with pytest.raises(NotFoundException):
        await r.dispatch("GET", "/guests/1", None)


@pytest.mark.asyncio
async def test_delete_guest_not_found():
    r = make_router()
    with pytest.raises(NotFoundException):
        await r.dispatch("DELETE", "/guests/99", None)


# ---------------------------------------------------------------------------
# Room — POST /rooms
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_room_returns_response():
    r = make_router()
    result = await r.dispatch("POST", "/rooms", {"number": 101, "floor": 1, "capacity": 2})
    assert result["id"] == 1
    assert result["number"] == 101
    assert result["floor"] == 1
    assert result["capacity"] == 2
    assert result["occupied"] is False


@pytest.mark.asyncio
async def test_create_two_rooms_increments_id():
    r = make_router()
    r1 = await r.dispatch("POST", "/rooms", {"number": 101, "floor": 1, "capacity": 2})
    r2 = await r.dispatch("POST", "/rooms", {"number": 102, "floor": 1, "capacity": 3})
    assert r1["id"] == 1
    assert r2["id"] == 2


# ---------------------------------------------------------------------------
# Room — GET /rooms/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_room_returns_correct_room():
    r = make_router()
    await r.dispatch("POST", "/rooms", {"number": 101, "floor": 1, "capacity": 2})
    result = await r.dispatch("GET", "/rooms/1", None)
    assert result["id"] == 1
    assert result["number"] == 101


@pytest.mark.asyncio
async def test_get_room_not_found():
    r = make_router()
    with pytest.raises(NotFoundException) as exc_info:
        await r.dispatch("GET", "/rooms/99", None)
    assert "Room 99 not found" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Response model validation — router enforces shape
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_response_model_enforced():
    """A handler that returns a raw dict gets validated against response_model."""
    r = Router()

    async def bad_handler(**kwargs):
        # Returns a dict missing required fields — should fail response validation
        return {"id": 1}

    r.register("GET", "/test", bad_handler, None, GuestResponse)
    with pytest.raises(Exception):  # ValidationError from Pydantic
        await r.dispatch("GET", "/test", None)
