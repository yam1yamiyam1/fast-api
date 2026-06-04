from main import room_id_counter, room_store

from app.exceptions import NotFoundException
from app.models import RoomCreate, RoomResponse


async def create_room(body: RoomCreate):
    auto_id = room_id_counter["value"]
    room_id_counter["value"] += 1
    room_store[auto_id] = RoomResponse(**body.model_dump(), id=auto_id, occupied=False)
    return room_store[auto_id]


async def get_room(id):
    room_id = int(id)
    if room_id not in room_store:
        raise NotFoundException(f"Room {id} not found")
    return room_store[room_id]
