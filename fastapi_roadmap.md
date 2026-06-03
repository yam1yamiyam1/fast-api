# Roadmap

| Stage          | Focus                                           | When                    |
| -------------- | ----------------------------------------------- | ----------------------- |
| Drills 51–80   | OOP decorators + dynamic dispatch + first mixes | Now (done)              |
| Project 1      | CRUD API + auth + deploy + README               | After drill 80          |
| Apply          | Start after Project 1 ships                     | After Project 1         |
| Drills 81–100  | Gap filling after Project 1                     | Parallel with Project 1 |
| Drills 101–130 | Real FastAPI (core + auth + DB)                 | After Project 1         |
| Project 2      | Production API + tests + Docker + deploy        | After drill 130         |
| Drills 131–160 | Testing + infra hardening                       | Parallel with Project 2 |
| Portfolio      | 2 projects, live URLs                           | Before applying broadly |

# Drill Map

| Range   | Topic                                       | Status |
| ------- | ------------------------------------------- | ------ |
| 01–10   | Pydantic fundamentals                       | ✅     |
| 11–20   | Async/Await fundamentals                    | ✅     |
| 21–30   | Wrapper decorators                          | ✅     |
| 31–40   | Registry decorators                         | ✅     |
| 41–50   | Toy dispatch + toy middleware + toy DI      | ✅     |
| 51–60   | OOP decorators                              | ✅     |
| 61–70   | Dynamic dispatch deep dive                  | ✅     |
| 71–80   | First mixes (2 concepts)                    | ✅     |
| 81–100  | Harder combos — gap filling after Project 1 | ⬜     |
| 101–130 | Real FastAPI (core + auth + DB)             | ⬜     |
| 131–160 | Production hardening (testing + infra)      | ⬜     |
| 161–199 | Speed drills + synthesis                    | ⬜     |
| 200     | Final boss                                  | ⬜     |

---

## Phase 2: Real FastAPI (Drills 101–130)

> **Start Project 1 at drill 80, start applying after it ships**

### Core FastAPI (101–110)

- `@app.get`, `uvicorn.run`, test with `httpx`
- path params + query params + type coercion
- request body with Pydantic model
- `response_model=` — validate output
- `HTTPException` + status codes
- `Depends()` — single injected dependency
- `Depends()` chained — one dep calls another
- `Depends()` with class — stateful dependency
- `BackgroundTasks` — fire and forget
- lifespan — startup/shutdown with `asynccontextmanager`

### Auth (111–120)

- `OAuth2PasswordBearer` — extract token from header
- JWT decode — verify signature and expiry with `python-jose`
- current user dependency — token → User object
- role-based access — admin vs regular user
- refresh token pattern
- API key auth — header + query param
- `HTTPBasic` auth
- scopes — fine-grained permissions
- auth middleware — global vs per-route
- final boss — JWT + roles + scopes in one system

### Database (121–130)

- SQLAlchemy async setup — engine, session factory
- first table + Alembic migration
- CRUD — create, read, update, delete
- `get_db()` session as a dependency
- relationships — one-to-many, eager vs lazy load
- transactions — commit, rollback
- repository pattern — separate DB logic from routes
- pagination — limit/offset + cursor-based
- filters + search
- final boss — full CRUD API with auth + DB

---

## Phase 3: Production (Drills 131–160)

> **Start Project 2 at drill 131**

### Testing (131–140)

- `pytest` + `httpx.AsyncClient` — test FastAPI routes
- fixtures — test DB, test user, test token
- dependency override — swap real DB for test DB
- factory pattern for test data
- parametrized tests — one test, many cases
- mock external services with `respx`
- test auth flows end-to-end
- enforce 90%+ coverage
- load test with `locust`
- final boss — full test suite

### Production Patterns (141–155)

- `pydantic-settings` — env vars, `.env` files
- structured logging with `structlog`
- request ID middleware — trace across logs
- rate limiting — token bucket with Redis
- Redis cache layer
- background workers with `arq`
- WebSockets — real-time updates
- file upload — stream to S3
- health check + readiness endpoint
- graceful shutdown
- CORS — production config
- exception handler hierarchy — domain → HTTP
- OpenAPI customization
- API versioning — `/v1/` prefix
- final boss — production-ready API

### Infrastructure (156–160)

- Docker — containerize the app
- Docker Compose — app + DB + Redis
- GitHub Actions — CI on push
- deploy to Railway / Render / Fly.io
- final boss — full deploy pipeline

---

## Projects (non-negotiable)

### Project 1 — after drill 80

- FastAPI CRUD API
- users, posts, JWT auth
- deployed, live URL, GitHub README
- **start applying for jobs here**

### Project 2 — after drill 130

- your choice of domain
- full test suite, Docker, deployed
- something you'd show in an interview without hesitation
