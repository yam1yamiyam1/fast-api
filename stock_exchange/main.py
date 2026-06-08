from exceptions import NotFoundException
from models import (
    ListingCollectionResponse,
    ListingCreate,
    ListingResponse,
    OrderCollectionResponse,
    OrderCreate,
    OrderResponse,
)
from router import Router

listing_store: dict[int, dict] = {}
listing_counter: dict[str, int] = {"value": 1}
order_store: dict[int, dict] = {}
order_counter: dict[str, int] = {"value": 1}

router = Router()


async def create_listing(body: ListingCreate):
    auto_id = listing_counter["value"]
    listing_counter["value"] += 1
    listing = {"id": auto_id, **body.model_dump()}
    listing_store[auto_id] = listing
    return listing_store[auto_id]


async def get_all_listings():
    return {"items": list(listing_store.values())}


async def get_listing(id: int):
    if id not in listing_store:
        raise NotFoundException("Listing not found")
    return listing_store[id]


async def delete_listing(id: int):
    if id not in listing_store:
        raise NotFoundException("Listing not found")
    return listing_store.pop(id)


async def create_order(body: OrderCreate):
    if body.listing_id not in listing_store:
        raise NotFoundException("Listing not found")
    auto_id = order_counter["value"]
    order_counter["value"] += 1
    order = {"id": auto_id, **body.model_dump()}
    order_store[auto_id] = order
    return order_store[auto_id]


async def get_all_orders():
    return {"items": list(order_store.values())}


async def get_order(id: int):
    if id not in order_store:
        raise NotFoundException("Order not found")
    return order_store[id]


router.register("POST", "/listings", create_listing, ListingCreate, ListingResponse)
router.register("GET", "/listings", get_all_listings, None, ListingCollectionResponse)
router.register("GET", "/listings/{id}", get_listing, None, ListingResponse)
router.register("DELETE", "/listings/{id}", delete_listing, None, ListingResponse)
router.register("POST", "/orders", create_order, OrderCreate, OrderResponse)
router.register("GET", "/orders", get_all_orders, None, OrderCollectionResponse)
router.register("GET", "/orders/{id}", get_order, None, OrderResponse)
