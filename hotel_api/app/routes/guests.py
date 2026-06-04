from exceptions import NotFoundException
from main import guest_id_counter, guest_store
from models import GuestCreate, GuestResponse, GuestUpdate


async def create_guest(body: GuestCreate):
    auto_id = guest_id_counter["value"]
    guest_id_counter["value"] += 1
    guest_store[auto_id] = GuestResponse(
        **body.model_dump(), id=auto_id, checked_in=False
    )
    return guest_store[auto_id]


async def get_guest(id):
    if id not in guest_store:
        raise NotFoundException(f"Guest {id} not found")
    return guest_store[str(id)]


async def update_guest(id, body: GuestUpdate):
    if id not in guest_store:
        raise NotFoundException(f"Guest {id} not found")
    guest_store[str(id)] = {**guest_store[str(id)], **body.model_dump()}


async def delete_guest(id):
    if id not in guest_store:
        raise NotFoundException(f"Guest {id} not found")
    del guest_store[str(id)]
    return {"deleted": True, "id": id}
