from main import guest_id_counter, guest_store

from app.exceptions import NotFoundException
from app.models import GuestCreate, GuestResponse, GuestUpdate


async def create_guest(body: GuestCreate):
    auto_id = guest_id_counter["value"]
    guest_id_counter["value"] += 1
    guest_store[auto_id] = GuestResponse(
        **body.model_dump(), id=auto_id, checked_in=False
    )
    return guest_store[auto_id]


async def get_guest(id):
    guest_id = int(id)
    if guest_id not in guest_store:
        raise NotFoundException(f"Guest {id} not found")
    return guest_store[guest_id]


async def update_guest(id, body: GuestUpdate):
    guest_id = int(id)
    if guest_id not in guest_store:
        raise NotFoundException(f"Guest {id} not found")
    guest_data = guest_store[int(id)]
    guest_store[guest_id] = GuestResponse(
        **{**guest_data.model_dump(), **body.model_dump(exclude_unset=True)}
    )
    return guest_store[guest_id]


async def delete_guest(id):
    guest_id = int(id)
    if guest_id not in guest_store:
        raise NotFoundException(f"Guest {id} not found")
    del guest_store[guest_id]
    return {"deleted": True, "id": guest_id}
