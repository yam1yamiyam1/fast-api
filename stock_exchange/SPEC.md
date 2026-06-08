# Project 2 — Stage 1 Spec
## Stock Exchange — Core Router + Models

---

## In-Memory Stores

Two stores: one for stock listings, one for orders.
IDs are integers, auto-incremented, never reused, never reset.

---

## Validation responsibility

Request body validation is always the request model's job — Field constraints only,
no logic in the handler. The router catches Pydantic ValidationError and returns 422.
Handlers never call .validate() or catch ValidationError themselves.

---

## Stock Listings

### POST /listings
- Request body required. Validated by ListingCreate.
- ticker: non-empty string. price: greater than 0. company: non-empty string.
- Constraint violations return {"error": ..., "status_code": 422}.
- Returns the created listing validated through ListingResponse.

### GET /listings
- No request body.
- Returns {"items": [{...}, {...}, ...]}.
- Each item is a ListingResponse-shaped dict.
- Response model validates the full {"items": [...]} shape.

### GET /listings/{id}
- No request body.
- Returns the listing validated through ListingResponse.
- Raises NotFoundException if id not in listing_store.

### DELETE /listings/{id}
- No request body.
- Removes the listing from the store.
- Returns the deleted listing validated through ListingResponse.
- Raises NotFoundException if id not in listing_store.

---

## Orders

### POST /orders
- Request body required. Validated by OrderCreate.
- listing_id: positive int. side: exactly "buy" or "sell". quantity: greater than 0. price: greater than 0.
- Constraint violations return {"error": ..., "status_code": 422}.
- listing_id is checked against listing_store in the handler — if not found, raises NotFoundException.
  This check is handler logic, not model validation.
- Returns the created order validated through OrderResponse.

### GET /orders
- No request body.
- Returns {"items": [{...}, {...}, ...]}.
- Each item is an OrderResponse-shaped dict.
- Response model validates the full {"items": [...]} shape.

### GET /orders/{id}
- No request body.
- Returns the order validated through OrderResponse.
- Raises NotFoundException if id not in order_store.

---

## Routing rules

- Path matching uses {param} syntax. Extracted param is always cast to int.
- If the path matches no registered route at all: raises NotFoundException (status_code 404).
- If the path matches but the HTTP method does not: raises MethodNotAllowedException (status_code 405).

---

## Exception rules

All custom exceptions carry a string message.
One base exception. NotFoundException, MethodNotAllowedException, and ValidationException
each inherit from it.

The router is the only place that catches exceptions. It catches them internally
and returns a dict — exceptions never propagate to the caller.

Caught exception → return dict:
- NotFoundException           → {"error": <message>, "status_code": 404}
- MethodNotAllowedException   → {"error": <message>, "status_code": 405}
- Pydantic ValidationError    → {"error": <message>, "status_code": 422}

---

## Response model validation

Every route declares a response model.
Before returning to the caller, the router validates the handler's return value
through that model. If validation fails, raises ValidationException.
ValidationException is also caught by the router and returned as {"error": ..., "status_code": 422}.

---

## Handler rules

- Handlers are plain async functions registered on the router.
- Handlers receive the extracted path param (if any) as a keyword argument named by the param (e.g. id).
- Handlers receive the validated request body (if any) as a keyword argument named body.
- Handlers return plain dicts.
- Handlers never catch exceptions — that is the router's job.
