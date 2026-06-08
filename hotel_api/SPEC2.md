# Hotel API — SPEC.md
# Stage 1: Core Router + Models

## Scenario

You are building the internal dispatch system for the Grand Harbour Hotel.
The front desk software needs to register routes, validate incoming requests,
dispatch them to the correct handler, and return validated responses.

There is no web server. There is no HTTP. Requests are plain Python dicts.
The system receives a method string ("GET", "POST", "PATCH", "DELETE"),
a path string ("/guests/3"), and an optional body dict. It dispatches to
the correct handler and returns a response dict.

Everything is async. All handlers are async functions.

---

## Component 1: Request and Response Models
### File: `app/models.py`

The system uses Pydantic models to validate every incoming body and every
outgoing response. You define the models; the router uses them.

### Guest models

A guest has:
- id: a positive integer
- name: a non-empty string
- email: a string that must be a valid email format (contains @)
- room_number: an optional positive integer, default None
- checked_in: a bool, default False

GuestCreate is used for POST /guests — it has name, email, room_number (optional).
GuestUpdate is used for PATCH /guests/{id} — all fields optional except none are
required. Any field that is present replaces the stored value.
GuestResponse is the response model — it includes all five fields.

### Room models

A room has:
- id: a positive integer
- number: a positive integer
- floor: an integer between 1 and 20 inclusive
- capacity: an integer between 1 and 6 inclusive
- occupied: a bool, default False

RoomCreate is used for POST /rooms — it has number, floor, capacity.
RoomResponse is the response model — all five fields.

---

## Component 2: In-memory store
### File: `main.py`

The system keeps two plain Python dicts as its store — one for guests,
one for rooms. Keys are integer IDs. IDs auto-increment starting from 1.
The store lives at module level in main.py with exactly these names:

    guest_store        — dict, keys are int IDs
    room_store         — dict, keys are int IDs
    guest_id_counter   — dict with a single key "value", starts at 1
    room_id_counter    — dict with a single key "value", starts at 1

The tests import and reset these directly between cases.

---

## Component 3: Router
### File: `app/router.py`

The Router class maintains a registry of routes. A route entry stores:
- the HTTP method (string)
- the path pattern (string, may contain {param} placeholders)
- the handler (async function)
- the request model (a Pydantic model class, or None)
- the response model (a Pydantic model class, or None)

### Registration

The Router exposes a register() method that accepts method, path, handler,
request_model, and response_model. Route handlers are registered explicitly —
no decorator syntax required for Stage 1.

### Dispatch

The Router exposes an async dispatch() method. It accepts method (str),
path (str), and body (dict or None).

Dispatch does the following in order:

1. Find the matching route by comparing method and path against the registry.
   Path matching must support {param} placeholders. A path like /guests/{id}
   must match /guests/3 and extract {"id": "3"}.

2. If no route matches the path pattern at all: raise a NotFoundException with
   the message "Not found: {path}".

3. If a route matches the path but not the method: raise a
   MethodNotAllowedException with the message
   "Method not allowed: {method} {path}".

4. If a request_model is set for the route: validate the body dict against it.
   If validation fails, raise a ValidationException with the message
   "Invalid request body".

5. Call the handler. Pass path params as keyword arguments. If the route has
   a request_model, also pass the validated model instance as a keyword
   argument named "body".

6. If a response_model is set for the route: validate the handler's return
   value against it. If the return value is a dict, construct the model from it.
   If it is already a model instance, validate it. Return the model's dict.

7. If no response_model: return the handler's return value as-is.

---

## Component 4: Route handlers

### File: `app/routes/guests.py` — guest handlers
### File: `app/routes/rooms.py` — room handlers

All handlers are async functions.

### Guest routes

POST /guests
- Body: GuestCreate
- Creates a new guest with auto-incremented id, checked_in=False
- Returns: GuestResponse

GET /guests/{id}
- No body
- Returns the guest with that id
- If not found: raise NotFoundException("Guest {id} not found")

PATCH /guests/{id}
- Body: GuestUpdate
- Updates only the fields present in the body
- If not found: raise NotFoundException("Guest {id} not found")
- Returns: GuestResponse

DELETE /guests/{id}
- No body
- Removes the guest from the store
- If not found: raise NotFoundException("Guest {id} not found")
- Returns: {"deleted": True, "id": id}

### Room routes

POST /rooms
- Body: RoomCreate
- Creates a new room with auto-incremented id, occupied=False
- Returns: RoomResponse

GET /rooms/{id}
- No body
- Returns the room with that id
- If not found: raise NotFoundException("Room {id} not found")

---

## Component 5: Custom exceptions
### File: `app/exceptions.py`

Define these four exception classes:

- AppException: base, inherits from Exception, carries a message string
- NotFoundException: inherits from AppException
- MethodNotAllowedException: inherits from AppException
- ValidationException: inherits from AppException

These are raised by the router and by handlers. They are not caught inside
the router in Stage 1 — they propagate to the caller.

---

## Constraints

- No FastAPI, no uvicorn, no httpx, no Starlette, no web framework of any kind.
- Standard library + Pydantic only.
- All handlers must be async functions.
- All dispatch calls must be awaited.
- The store must be resettable — tests will clear it between cases.
- Path param values extracted from URLs are strings. Handlers are responsible
  for converting them to int where needed.
- GuestUpdate fields are all Optional. Do not replace a field with None if the
  caller did not include it — only update fields that were explicitly passed.

---

# Stage 2 Addendum: Middleware + Dependencies

## Component 6: Middleware
### File: `app/middleware.py` (your middleware functions live here)
### Modify: `app/router.py`

The Router gains a middleware list and an `add_middleware()` method.
Middleware functions are called on every dispatch, before route matching,
before validation, before the handler. They receive method, path, and body
as arguments. They return nothing. If a middleware raises, dispatch stops
and the exception propagates — the handler is never called.

Both sync and async middleware functions must be supported. Use
`inspect.iscoroutinefunction` to branch.

The pipeline order for every dispatch call is:
1. All middleware, in registration order
2. Route matching + method check
3. Request body validation
4. Dependencies resolved
5. Handler called

`add_middleware()` accepts a single callable and appends it to the list.

---

## Component 7: Dependencies
### File: `app/dependencies.py` (your dependency functions live here)
### Modify: `app/router.py`

`register()` gains an optional `deps` keyword argument. It is a dict
mapping keyword argument names to callables. Each callable is a dependency
function that returns a value. That value is passed to the handler under
the corresponding keyword name.

Dependencies are resolved after middleware and after request validation,
immediately before the handler is called. Each dependency is called once
per dispatch. Both sync and async dependency functions must be supported.

A dependency may itself call another async function internally — this is
normal async Python and requires no special handling in the router.

If a route has no `deps`, the argument defaults to an empty dict and
the handler is called as before.
