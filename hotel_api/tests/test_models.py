import pytest
from pydantic import ValidationError

from app.models import GuestCreate, GuestUpdate, GuestResponse, RoomCreate, RoomResponse


# ---------------------------------------------------------------------------
# GuestCreate
# ---------------------------------------------------------------------------

def test_guest_create_valid():
    g = GuestCreate(name="Amara Osei", email="amara@hotel.com")
    assert g.name == "Amara Osei"
    assert g.email == "amara@hotel.com"
    assert g.room_number is None


def test_guest_create_with_room():
    g = GuestCreate(name="Amara Osei", email="amara@hotel.com", room_number=5)
    assert g.room_number == 5


def test_guest_create_empty_name_rejected():
    with pytest.raises(ValidationError):
        GuestCreate(name="", email="amara@hotel.com")


def test_guest_create_invalid_email_rejected():
    with pytest.raises(ValidationError):
        GuestCreate(name="Amara Osei", email="not-an-email")


def test_guest_create_negative_room_rejected():
    with pytest.raises(ValidationError):
        GuestCreate(name="Amara Osei", email="amara@hotel.com", room_number=-1)


# ---------------------------------------------------------------------------
# GuestUpdate
# ---------------------------------------------------------------------------

def test_guest_update_all_optional():
    u = GuestUpdate()
    assert u.name is None
    assert u.email is None
    assert u.room_number is None
    assert u.checked_in is None


def test_guest_update_partial():
    u = GuestUpdate(name="New Name")
    assert u.name == "New Name"
    assert u.email is None


def test_guest_update_empty_name_rejected():
    with pytest.raises(ValidationError):
        GuestUpdate(name="")


# ---------------------------------------------------------------------------
# GuestResponse
# ---------------------------------------------------------------------------

def test_guest_response_valid():
    g = GuestResponse(id=1, name="Amara Osei", email="amara@hotel.com",
                      room_number=None, checked_in=False)
    assert g.id == 1
    assert g.checked_in is False


def test_guest_response_negative_id_rejected():
    with pytest.raises(ValidationError):
        GuestResponse(id=0, name="Amara Osei", email="amara@hotel.com",
                      room_number=None, checked_in=False)


# ---------------------------------------------------------------------------
# RoomCreate
# ---------------------------------------------------------------------------

def test_room_create_valid():
    r = RoomCreate(number=101, floor=1, capacity=2)
    assert r.number == 101
    assert r.floor == 1
    assert r.capacity == 2


def test_room_create_floor_zero_rejected():
    with pytest.raises(ValidationError):
        RoomCreate(number=101, floor=0, capacity=2)


def test_room_create_floor_21_rejected():
    with pytest.raises(ValidationError):
        RoomCreate(number=101, floor=21, capacity=2)


def test_room_create_capacity_zero_rejected():
    with pytest.raises(ValidationError):
        RoomCreate(number=101, floor=1, capacity=0)


def test_room_create_capacity_7_rejected():
    with pytest.raises(ValidationError):
        RoomCreate(number=101, floor=1, capacity=7)


# ---------------------------------------------------------------------------
# RoomResponse
# ---------------------------------------------------------------------------

def test_room_response_valid():
    r = RoomResponse(id=1, number=101, floor=1, capacity=2, occupied=False)
    assert r.id == 1
    assert r.occupied is False


def test_room_response_negative_id_rejected():
    with pytest.raises(ValidationError):
        RoomResponse(id=-1, number=101, floor=1, capacity=2, occupied=False)
