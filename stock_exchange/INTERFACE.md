# Project 2 — Stage 1 Interface Sheet
## Stock Exchange — Core Router + Models

---

## models.py

**ListingCreate** — Pydantic model
- Purpose: validates the request body when creating a stock listing
- ticker: str, non-empty
- price: float, must be greater than 0
- company: str, non-empty

**ListingResponse** — Pydantic model
- Purpose: shape of every listing returned to the caller
- id: int, positive
- ticker: str
- price: float
- company: str

**OrderCreate** — Pydantic model
- Purpose: validates the request body when creating an order
- listing_id: int, positive
- side: str, must be exactly "buy" or "sell" — enforce with a validator or Literal
- quantity: int, must be greater than 0
- price: float, must be greater than 0

**OrderResponse** — Pydantic model
- Purpose: shape of every order returned to the caller
- id: int, positive
- listing_id: int
- side: str
- quantity: int
- price: float

---

## exceptions.py

**AppException** — exception class, base
- Purpose: root of all custom exceptions; carries a message string; everything the system raises inherits from this
- __init__: takes message str

**NotFoundException** — exception, inherits AppException
- Purpose: raised when a requested resource does not exist in the store

**MethodNotAllowedException** — exception, inherits AppException
- Purpose: raised when the path exists in the registry but the HTTP method does not match

**ValidationException** — exception, inherits AppException
- Purpose: raised when response model validation fails

---

## router.py

**RouteEntry** — dataclass or plain class (your choice)
- Purpose: holds one registered route's data
- method: str
- path: str
- handler: async callable
- request_model: Pydantic model class or None
- response_model: Pydantic model class

**Router** — class
- Purpose: owns the route registry and drives the full dispatch pipeline
- __init__: no args beyond self; initializes the registry as an empty list

- register — method
  - Purpose: adds a RouteEntry to the registry
  - args: method str, path str, handler callable, request_model (None or model class), response_model (model class)
  - returns: nothing

- _match — method
  - Purpose: iterates registry, matches path via regex, extracts path params; raises NotFoundException or MethodNotAllowedException if no match
  - args: method str, path str
  - returns: tuple of (RouteEntry, dict)

- dispatch — async method
  - Purpose: full pipeline — match route, validate request body, call handler, validate response, return result dict or error dict
  - args: method str, path str, body dict or None
  - returns: dict

---

## main.py

**listing_store** — dict, int keys, dict values
- Purpose: holds all stock listings in memory; keys are listing IDs

**listing_counter** — dict, single key "value", starts at 1
- Purpose: source of truth for the next listing ID

**order_store** — dict, int keys, dict values
- Purpose: holds all orders in memory; keys are order IDs

**order_counter** — dict, single key "value", starts at 1
- Purpose: source of truth for the next order ID

**router** — Router instance
- Purpose: the single shared router for the whole app

**create_listing** — async handler
- Purpose: validates body, stores listing, returns it as dict
- kwargs: body (ListingCreate instance)
- returns: dict

**get_all_listings** — async handler
- Purpose: returns all listings as a list of dicts wrapped under key "items"
- returns: dict with key "items"

**get_listing** — async handler
- Purpose: looks up listing by id, raises NotFoundException if missing
- kwargs: id int
- returns: dict

**delete_listing** — async handler
- Purpose: removes listing by id, raises NotFoundException if missing, returns the deleted listing
- kwargs: id int
- returns: dict

**create_order** — async handler
- Purpose: validates body, checks listing_id exists in listing_store, stores order, returns it
- kwargs: body (OrderCreate instance)
- returns: dict

**get_all_orders** — async handler
- Purpose: returns all orders as a list of dicts wrapped under key "items"
- returns: dict with key "items"

**get_order** — async handler
- Purpose: looks up order by id, raises NotFoundException if missing
- kwargs: id int
- returns: dict
