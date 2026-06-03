import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_71():
    # =========================================================================
    # SCENARIO: The Hotel
    # =========================================================================
    # A hotel front desk system processes booking requests. Each booking
    # arrives as a raw dict from an untrusted client. The system must validate
    # the raw dict into a Pydantic model BEFORE any method sees it.
    #
    # Instead of validating inside every method, a decorator handles it
    # automatically. The method only ever receives a clean, validated object.
    # If validation fails, a domain exception is raised before the method runs.
    #
    # NEW CONCEPT: Pydantic validation inside an OOP decorator
    # - The decorator reads a raw kwarg from kwargs
    # - Validates it into a Pydantic model
    # - Replaces the raw dict in kwargs with the validated model
    # - The decorated method never sees a raw dict — only a clean object
    # - If validation fails, raise a domain exception (not ValidationError)
    #
    # REQUIREMENTS:
    #
    # 1. A Pydantic model BookingRequest:
    #    - guest_name: str (min_length=2)
    #    - nights: int (gt=0)
    #    - room_type: str  (one of: "single", "double", "suite")
    #      hint: use Field and a validator, or just leave as str — your call
    #
    # 2. A custom exception InvalidBookingError(Exception)
    #
    # 3. A decorator validate_booking(func):
    #    - wraps func
    #    - grabs instance from args[0]
    #    - expects the raw payload dict at kwargs["raw"]
    #    - validates kwargs["raw"] into BookingRequest
    #      - if ValidationError: raise InvalidBookingError("Bad booking data")
    #    - replaces kwargs["raw"] with the validated BookingRequest object
    #    - calls and awaits func normally
    #    - returns the result
    #
    # 4. A class HotelDesk:
    #    - __init__(self, hotel_name: str):
    #        - self.hotel_name = hotel_name
    #        - self.bookings = []   ← list of BookingRequest objects
    #    - async method book_room(self, *, raw):
    #        - decorated with @validate_booking
    #        - appends raw to self.bookings  (raw is now a BookingRequest object)
    #        - prints f"  Booked: {raw.guest_name}, {raw.nights} nights, {raw.room_type}"
    #        - returns raw.guest_name
    #    - async method upgrade_room(self, *, raw):
    #        - decorated with @validate_booking
    #        - prints f"  Upgraded: {raw.guest_name} to {raw.room_type}"
    #        - returns {"guest": raw.guest_name, "new_room": raw.room_type}
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class BookingRequest(BaseModel):
        guest_name: str = Field(min_length=2)
        nights: int = Field(gt=0)
        room_type: str

    class InvalidBookingError(Exception):
        pass

    def validate_booking(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            instance = args[0]
            raw_payload = kwargs["raw"]
            try:
                valid_pd = BookingRequest(**raw_payload)
            except ValidationError:
                raise InvalidBookingError("Bad booking data")
            kwargs["raw"] = valid_pd
            return await func(*args, **kwargs)

        return wrapper

    class HotelDesk:
        def __init__(self, hotel_name: str):
            self.hotel_name = hotel_name
            self.bookings = []

        @validate_booking
        async def book_room(self, *, raw):
            self.bookings.append(raw)
            print(f"  Booked: {raw.guest_name}, {raw.nights} nights, {raw.room_type}")
            return raw.guest_name

        @validate_booking
        async def upgrade_room(self, *, raw):
            print(f"  Upgraded: {raw.guest_name} to {raw.room_type}")
            return {"guest": raw.guest_name, "new_room": raw.room_type}

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    desk = HotelDesk(hotel_name="Grand Manila")  # noqa: F821

    print("Test 1: Valid booking")
    result = await desk.book_room(
        raw={"guest_name": "Alice", "nights": 3, "room_type": "suite"}
    )
    assert result == "Alice", f"Expected 'Alice', got {result!r}"
    assert len(desk.bookings) == 1
    assert desk.bookings[0].guest_name == "Alice"
    assert desk.bookings[0].nights == 3
    print("  PASS")

    print("\nTest 2: Valid upgrade")
    result = await desk.upgrade_room(
        raw={"guest_name": "Bob", "nights": 1, "room_type": "double"}
    )
    assert result == {"guest": "Bob", "new_room": "double"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 3: Invalid payload — nights is 0 (violates gt=0)")
    try:
        await desk.book_room(
            raw={"guest_name": "Carol", "nights": 0, "room_type": "single"}
        )
        assert False, "Should have raised"
    except InvalidBookingError as e:  # noqa: F821
        assert str(e) == "Bad booking data"
        print("  PASS")

    print("\nTest 4: Invalid payload — guest_name too short")
    try:
        await desk.book_room(
            raw={"guest_name": "X", "nights": 2, "room_type": "single"}
        )
        assert False, "Should have raised"
    except InvalidBookingError:  # noqa: F821
        print("  PASS")

    print("\nTest 5: Invalid payload — missing field")
    try:
        await desk.book_room(raw={"guest_name": "Dave"})
        assert False, "Should have raised"
    except InvalidBookingError:  # noqa: F821
        print("  PASS")

    print("\nTest 6: Failed booking does NOT add to self.bookings")
    assert len(desk.bookings) == 1, f"Expected 1 booking, got {len(desk.bookings)}"
    print("  PASS")

    print("\nTest 7: Decorator preserved method names")
    assert desk.book_room.__name__ == "book_room", f"Got {desk.book_room.__name__!r}"
    assert desk.upgrade_room.__name__ == "upgrade_room", (
        f"Got {desk.upgrade_room.__name__!r}"
    )
    print("  PASS")

    print("\nTest 8: Two separate HotelDesk instances have independent bookings")
    desk2 = HotelDesk(hotel_name="Seaside Inn")  # noqa: F821
    await desk2.book_room(raw={"guest_name": "Eve", "nights": 2, "room_type": "double"})
    assert len(desk.bookings) == 1
    assert len(desk2.bookings) == 1
    assert desk2.bookings[0].guest_name == "Eve"
    print("  PASS")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid booking
    #   Booked: Alice, 3 nights, suite
    #   PASS
    #
    # Test 2: Valid upgrade
    #   Upgraded: Bob to double
    #   PASS
    #
    # Test 3: Invalid payload — nights is 0 (violates gt=0)
    #   PASS
    #
    # Test 4: Invalid payload — guest_name too short
    #   PASS
    #
    # Test 5: Invalid payload — missing field
    #   PASS
    #
    # Test 6: Failed booking does NOT add to self.bookings
    #   PASS
    #
    # Test 7: Decorator preserved method names
    #   PASS
    #
    # Test 8: Two separate HotelDesk instances have independent bookings
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_71())
