# Python → FastAPI Translation Map

## Models & Validation
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| class M(BaseModel): field: type             | same — FastAPI uses Pydantic natively     |
| Field(gt=, min_length=, max_length=)        | same                                      |
| try/except ValidationError                  | FastAPI catches automatically → 422       |
| model.model_dump()                          | same                                      |
| Optional[str] = None                        | same                                      |
| Nested models                               | same                                      |

## Routing & Dispatch
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| ROUTES = []; path_to_regex(); dispatch()    | @app.get("/path"), @app.post("/path")     |
| {param} in path + match.groupdict()         | @app.get("/items/{id}") → def f(id: int) |
| method routing (GET/POST check in dispatch) | separate decorators: @app.get, @app.post  |
| 404 → raise NotFoundException               | raise HTTPException(status_code=404)      |
| 405 → raise MethodNotAllowedException       | FastAPI handles automatically             |
| return handler result dict                  | return dict or Pydantic model instance    |
| response model validation (D69)             | @app.get("/", response_model=MyModel)     |

## Request Body
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| dispatch(method, path, body: dict)          | def endpoint(body: MyModel) — auto parsed |
| Model(**body) to validate                   | FastAPI validates automatically           |
| pass validated model to handler             | model instance injected directly          |

## Dependency Injection
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| deps = {"key": async_fn}; await fn(token)   | Depends(fn) — injected as default arg     |
| chained deps: dep2 takes dep1 result (D68)  | def dep2(d1=Depends(dep1))                |
| parallel deps: asyncio.gather(d1, d2, d3)  | FastAPI resolves concurrently via Depends |

## Middleware
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| middleware list; loop + await each          | @app.middleware("http")                   |
| call_next pattern (D83)                     | async def mw(request, call_next)          |
| add_middleware(fn)                          | app.add_middleware(MyMiddleware)           |

## Lifespan
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| @asynccontextmanager + yield (D67)          | @asynccontextmanager + lifespan= arg      |
| APP_STATE = {} shared dict                  | same pattern                              |
| before yield = startup, finally = shutdown  | same                                      |

## Background Tasks
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| asyncio.create_task(fn()) (D78)             | BackgroundTasks; background.add_task(fn)  |
| asyncio.Queue + worker                      | BackgroundTasks (simpler, no queue)       |

## Concurrency
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| asyncio.Semaphore(n) in decorator (D79)     | same — still used manually when needed   |
| asyncio.gather for parallel deps (D75)      | Depends() handles this automatically      |

## Exceptions
| Pure Python (drills)                        | FastAPI equivalent                        |
| ------------------------------------------- | ----------------------------------------- |
| AppError hierarchy (D76)                    | HTTPException(status_code=, detail=)      |
| global error handler registry (D65)         | @app.exception_handler(ExcType)           |
| raise in middleware → abort dispatch        | raise HTTPException in middleware         |

## No Pure Python Equivalent (genuinely new)
- uvicorn.run() — ASGI server, no toy version
- httpx.AsyncClient — test client for real HTTP
- OAuth2PasswordBearer — token extraction from Authorization header
- JWT encode/decode (python-jose)
- SQLAlchemy async session + Alembic
- query params — ?key=value parsed automatically by FastAPI
