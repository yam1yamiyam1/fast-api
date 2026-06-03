import asyncio  # noqa: F401
import time  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Any, Callable, List, Optional  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401

# =============================================================================
# RECIPE BOOK (Syntax Reference)
# =============================================================================
# --- CHUNK 1: PYDANTIC & ASYNC ---
# Model:         class MyModel(BaseModel): ...
# Unpack/Dump:   obj = MyModel(**data_dict)  ->  data_dict = obj.model_dump()
# Async/Gather:  await my_func()  ->  await asyncio.gather(f1(), f2())
#
# --- CHUNK 2: WRAPPERS (MIDDLEWARE) ---
# Basic Wrapper:
#   def my_decorator(func: Callable) -> Callable:
#       @wraps(func)
#       async def wrapper(*args, **kwargs):
#           # ... pre-processing ...
#           result = await func(*args, **kwargs)
#           # ... post-processing ...
#           return result
#       return wrapper
#
# Decorator Factory (Passing args to decorator):
#   def my_factory(my_arg: str):
#       def decorator(func: Callable):
#           async def wrapper(*args, **kwargs): ...
#           return wrapper
#       return decorator
#
# --- CHUNK 2: REGISTRIES (ROUTERS) ---
# Basic Registry:
#   ROUTES = {}
#   def register(func: Callable):
#       ROUTES[func.__name__] = func
#       return func   # No wrapper needed! Just saving memory addresses.
# =============================================================================


# =============================================================================
# DRILL 21 — Scenario: The Basic Async Middleware
# =============================================================================
async def run_drill_21():
    # SCENARIO: You want to log exactly when database queries start and end.

    # ACCEPTANCE CRITERIA:
    # 1. Write an async decorator `query_logger`.
    # 2. The wrapper should print "START", await the function, and print "END".
    # 3. Apply it to an async function `fetch_users()` that prints "fetching...".
    # 4. Await `fetch_users()`.

    # --- WRITE YOUR CODE BELOW ---
    def query_logger(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            print("START")
            result = await func(*args, **kwargs)
            print("END")
            return result

        return wrapper

    @query_logger
    async def fetch_users():
        print("fetching...")

    await fetch_users()
    # EXPECTED OUTPUT:
    # START
    # fetching...
    # END
    pass


# =============================================================================
# DRILL 22 — Scenario: Modifying the Return Value (Dict to Model)
# =============================================================================
async def run_drill_22():
    # SCENARIO: Your database driver returns a raw Python dictionary, but your
    # system expects a Pydantic model. You want a decorator to automatically
    # convert the return value.

    # ACCEPTANCE CRITERIA:
    # 1. Define a Pydantic `User` model with `username` (str).
    # 2. Write a decorator `return_as_model`.
    # 3. The wrapper should await the function, capture the returned dict,
    #    unpack it into the `User` model, and return the Pydantic instance.
    # 4. Decorate `get_db_user()` which returns `{"username": "alice"}`.
    # 5. Await `get_db_user()` and print the result.

    # --- WRITE YOUR CODE BELOW ---
    class User(BaseModel):
        username: str

    def return_as_model(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            raw_dict = await func(*args, **kwargs)
            result = User(**raw_dict)
            return result

        return wrapper

    @return_as_model
    async def get_db_user():
        return {"username": "alice"}

    print(await get_db_user())

    # EXPECTED OUTPUT:
    # username='alice'
    pass


# =============================================================================
# DRILL 23 — Scenario: Intercepting and Validating kwargs
# =============================================================================
async def run_drill_23():
    # SCENARIO: A client sends a raw dict into your function. You want a decorator
    # to intercept `kwargs["payload"]`, validate it with Pydantic, and replace
    # the dict with the safe Pydantic object before the function runs.

    # ACCEPTANCE CRITERIA:
    # 1. Define a `Config` model with `retries` (int).
    # 2. Write decorator `validate_payload`.
    # 3. Inside the wrapper, extract `kwargs["payload"]`, convert it to a `Config`
    #    object, put the object back into `kwargs["payload"]`, and await the func.
    # 4. Decorate `connect(**kwargs)` which prints `kwargs["payload"].retries`.
    # 5. Await `connect(payload={"retries": 3})`.

    # --- WRITE YOUR CODE BELOW ---
    class Config(BaseModel):
        retries: int

    def validate_payload(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            raw_payload = kwargs["payload"]
            validated_object = Config(**raw_payload)
            kwargs["payload"] = validated_object
            return await func(*args, **kwargs)

        return wrapper

    @validate_payload
    async def connect(**kwargs):
        print(kwargs["payload"].retries)

    await connect(payload={"retries": 3})
    # EXPECTED OUTPUT:
    # 3
    pass


# =============================================================================
# DRILL 24 — Scenario: Graceful Exception Catching in Middleware
# =============================================================================
async def run_drill_24():
    # SCENARIO: Sometimes your validation wrapper fails. You want a higher-level
    # wrapper to catch Pydantic errors globally.

    # ACCEPTANCE CRITERIA:
    # 1. Write an async decorator `catch_validation_errors`.
    # 2. Inside the wrapper, try to await the function. Except ValidationError,
    #    and print "Bad data intercepted".
    # 3. Decorate `process_data()` which explicitly raises a Pydantic
    #    ValidationError. (Hint: `raise ValidationError.from_exception_data("err", [])`)
    # 4. Await `process_data()`.

    # --- WRITE YOUR CODE BELOW ---
    def catch_validation_errors(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                await func(*args, **kwargs)
            except ValidationError:
                print("Bad data intercepted")

        return wrapper

    @catch_validation_errors
    async def process_data():
        raise ValidationError.from_exception_data("err", [])

    await process_data()
    # EXPECTED OUTPUT:
    # Bad data intercepted
    pass


# =============================================================================
# DRILL 25 — Scenario: Preserving Function Metadata (@wraps)
# =============================================================================
async def run_drill_25():
    # SCENARIO: Your API documentation generator (like Swagger) relies on function
    # names. If you use a decorator without `@wraps`, every function is named "wrapper".

    # ACCEPTANCE CRITERIA:
    # 1. Write a basic async decorator `dummy_decorator` that does nothing
    #    but await the function.
    # 2. You MUST use `@wraps(func)` directly above `async def wrapper...`
    # 3. Decorate `fetch_inventory()`.
    # 4. Print `fetch_inventory.__name__`.

    # --- WRITE YOUR CODE BELOW ---
    def dummy_decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await func(*args, **kwargs)
            print(func.__name__)

        return wrapper

    @dummy_decorator
    async def fetch_inventory():

        pass

    await fetch_inventory()

    # EXPECTED OUTPUT:
    # fetch_inventory
    pass


# =============================================================================
# DRILL 26 — Scenario: Decorator Factory (Passing Arguments)
# =============================================================================
async def run_drill_26():
    # SCENARIO: You want a decorator that delays execution, but you want to
    # specify *how long* to delay on a per-function basis.

    # ACCEPTANCE CRITERIA:
    # 1. Write a factory `delay(seconds: float)`.
    # 2. Inside it, define the decorator and the async wrapper.
    # 3. The wrapper should `await asyncio.sleep(seconds)`, then await the func.
    # 4. Decorate `quick_ping()` with `@delay(seconds=0.1)`. (Have it print "pong").
    # 5. Await `quick_ping()`.

    # --- WRITE YOUR CODE BELOW ---
    def delay(seconds: float):
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                await asyncio.sleep(seconds)
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    @delay(seconds=0.1)
    async def quick_ping():
        print("pong")

    await quick_ping()
    # EXPECTED OUTPUT:
    # (Waits 0.1s)
    # pong
    pass


# =============================================================================
# DRILL 27 — Scenario: Factory + Pydantic Injection
# =============================================================================
async def run_drill_27():
    # SCENARIO: You want to inject a specific user profile into an endpoint.

    # ACCEPTANCE CRITERIA:
    # 1. Define `User` model with `username` (str).
    # 2. Write a factory `inject_user(name: str)`.
    # 3. Inside the wrapper, instantiate the `User` model using `name`.
    # 4. Add it to `kwargs["user"]`, then await the func.
    # 5. Decorate `dashboard(**kwargs)` which prints `kwargs["user"].username`.
    # 6. Apply `@inject_user("admin")` and await `dashboard()`.

    # --- WRITE YOUR CODE BELOW ---
    class User(BaseModel):
        username: str

    def inject_user(name: str):
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                kwargs["user"] = User(username=name)
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    @inject_user(name="admin")
    async def dashboard(**kwargs):
        print(kwargs["user"].username)

    await dashboard()
    # EXPECTED OUTPUT:
    # admin
    pass


# =============================================================================
# DRILL 28 — Scenario: Stateful Wrappers (Call Counting)
# =============================================================================
async def run_drill_28():
    # SCENARIO: You want to track how many times a specific function is called
    # without using global variables.

    # ACCEPTANCE CRITERIA:
    # 1. Write a decorator `call_counter`.
    # 2. Set `wrapper.calls = 0` BEFORE returning the wrapper.
    # 3. Inside the wrapper, increment `wrapper.calls += 1`, then await func.
    # 4. Decorate `ping()` (does nothing).
    # 5. Await `ping()` twice. Print `ping.calls`.

    # --- WRITE YOUR CODE BELOW ---
    def call_counter(func: Callable) -> Callable:

        async def wrapper(*args, **kwargs):

            wrapper.calls += 1
            return await func(*args, **kwargs)

        wrapper.calls = 0
        return wrapper

    @call_counter
    async def ping():
        pass

    await ping()
    await ping()
    print(ping.calls)

    # EXPECTED OUTPUT:
    # 2
    pass


# =============================================================================
# DRILL 29 — Scenario: The Basic Registry (No Wrappers Needed)
# =============================================================================
async def run_drill_29():
    # SCENARIO: You are building a CLI tool. You want to store functions in a
    # dictionary so you can look them up by name and run them dynamically.

    # ACCEPTANCE CRITERIA:
    # 1. Create an empty dict `CLI_COMMANDS`.
    # 2. Write a simple decorator `register_cmd` that assigns the func to
    #    `CLI_COMMANDS[func.__name__]` and returns the func directly.
    # 3. Decorate async `status_check()` which prints "System OK".
    # 4. Retrieve the function from `CLI_COMMANDS["status_check"]` and await it.

    # --- WRITE YOUR CODE BELOW ---
    CLI_COMMANDS = {}

    def register_cmd(func: Callable) -> Callable:
        CLI_COMMANDS[func.__name__] = func
        return func

    @register_cmd
    async def status_check():
        print("System OK")

    to_run = CLI_COMMANDS["status_check"]
    await to_run()
    # EXPECTED OUTPUT:
    # System OK
    pass


# =============================================================================
# DRILL 30 — Scenario: Registry + Pydantic Payload
# =============================================================================
async def run_drill_30():
    # SCENARIO: A registered event handler needs to receive structured data.

    # ACCEPTANCE CRITERIA:
    # 1. Define `Event` model with `event_id` (int).
    # 2. Create `HANDLERS = {}` and a `register` decorator.
    # 3. Decorate async `on_click(event: Event)` which prints `event.event_id`.
    # 4. Instantiate an Event with ID 99.
    # 5. Retrieve `on_click` from `HANDLERS` and await it, passing the event object.

    # --- WRITE YOUR CODE BELOW ---
    class Event(BaseModel):
        event_id: int

    HANDLERS = {}

    def register(func: Callable) -> Callable:
        HANDLERS[func.__name__] = func
        return func

    @register
    async def on_click(event: Event):
        print(event.event_id)

    my_event = Event(event_id=99)

    handler_func = HANDLERS["on_click"]
    await handler_func(my_event)

    # EXPECTED OUTPUT:
    # 99
    pass


# =============================================================================
# DRILL 31 — Scenario: Registry Factory (Custom String Keys)
# =============================================================================
async def run_drill_31():
    # SCENARIO: You are building a web router. You want to register functions
    # to specific URL paths, not their python function names.

    # ACCEPTANCE CRITERIA:
    # 1. Create `APP_ROUTES = {}`.
    # 2. Write a factory `route(path: str)`.
    # 3. The inner decorator saves the func to `APP_ROUTES[path]`. Return func.
    # 4. Decorate async `get_home()` with `@route("/home")`.
    # 5. Print the `.keys()` of `APP_ROUTES`.

    # --- WRITE YOUR CODE BELOW ---
    APP_ROUTES = {}

    def route(path: str):
        def decorator(func: Callable) -> Callable:

            APP_ROUTES[path] = func
            return func

        return decorator

    @route("/home")
    async def get_home():
        print("Welcome HOme")

    print(APP_ROUTES.keys())
    # EXPECTED OUTPUT:
    # dict_keys(['/home'])
    pass


# =============================================================================
# DRILL 32 — Scenario: Dynamic Dispatcher (The Core Web Framework Pattern)
# =============================================================================
async def run_drill_32():
    # SCENARIO: This is how FastAPI works. You receive a raw URL and a raw JSON
    # dictionary. You must look up the correct route, validate the data, and run it.

    # ACCEPTANCE CRITERIA:
    # 1. Create `API = {}` and a `@route(path)` factory decorator.
    # 2. Define `Item` model with `id` (int).
    # 3. Decorate `delete_item(payload: Item)` with `@route("/delete")`. Have it print `payload.id`.
    # 4. Write an async function `dispatch(path: str, raw_json: dict)`.
    # 5. Inside `dispatch`, look up the path in `API`. Instantiate `Item(**raw_json)`. Await the route func.
    # 6. Await `dispatch("/delete", {"id": 42})`.

    # --- WRITE YOUR CODE BELOW ---
    API = {}

    def route(path: str):
        def decorator(func: Callable) -> Callable:
            API[path] = func  # adds the decorated func to API dict ('/delete')
            return func

        return decorator

    class Item(BaseModel):
        id: int

    @route("/delete")
    async def delete_item(payload: Item):  # the function accessed via API[func]
        print(f"Deleted Item no. {payload.id}")

    async def dispatch(path: str, raw_json: dict):
        lookup_func = API[path]  # initializes a callable path to use the func
        item = Item(**raw_json)  # initializes the item
        await lookup_func(
            item
        )  # actual usage of the lookup_func and passing the model we created from raw_json

    await dispatch(path="/delete", raw_json={"id": 42})

    # EXPECTED OUTPUT:
    # 42
    pass


# =============================================================================
# DRILL 33 — Scenario: Registry with Metadata (Class references)
# =============================================================================
async def run_drill_33():
    # SCENARIO: Instead of hardcoding `Item(**raw_json)` in your dispatcher like
    # Drill 32, you want to store the required Pydantic model IN the registry!

    # ACCEPTANCE CRITERIA:
    # 1. Create `SMART_ROUTES = {}`.
    # 2. Define `AuthSchema` with `token` (str).
    # 3. Write a factory `smart_route(path: str, schema: Any)`.
    # 4. The decorator saves `{"func": func, "schema": schema}` to `SMART_ROUTES[path]`.
    # 5. Decorate `login` with `@smart_route("/login", AuthSchema)`.
    # 6. Print `SMART_ROUTES["/login"]["schema"].__name__`.

    # --- WRITE YOUR CODE BELOW ---
    SMART_ROUTES = {}

    class AuthSchema(BaseModel):
        token: str

    def smart_route(path: str, schema: Any):

        def decorator(func: Callable) -> Callable:

            SMART_ROUTES[path] = {"func": func, "schema": schema}
            return func

        return decorator

    @smart_route("/login", AuthSchema)
    async def login():
        print(SMART_ROUTES["/login"]["schema"].__name__)

    await login()
    # EXPECTED OUTPUT:
    # AuthSchema
    pass


# =============================================================================
# DRILL 34 — Scenario: Event Emitter (Lists of Functions)
# =============================================================================
async def run_drill_34():
    # SCENARIO: Unlike web routes (1 URL = 1 func), an event system allows
    # multiple functions to listen to the SAME event string.

    # ACCEPTANCE CRITERIA:
    # 1. Create `LISTENERS: dict[str, list] = {}`.
    # 2. Write a factory `on(event: str)`.
    # 3. Inside the decorator, if `event` is not in dict, set it to `[]`. Append func.
    # 4. Decorate `play_sound` and `send_email` with `@on("notification")`.
    # 5. Print the `len()` of the array stored at `LISTENERS["notification"]`.

    # --- WRITE YOUR CODE BELOW ---
    LISTENERS: dict[str, list] = {}

    def on(event: str):
        def decorator(func: Callable) -> Callable:
            if event not in LISTENERS:
                LISTENERS[event] = []
            LISTENERS[event].append(func)
            return func

        return decorator

    @on("notification")
    async def play_sound():
        pass

    @on("notification")
    async def send_email():
        pass

    print(len(LISTENERS["notification"]))
    # EXPECTED OUTPUT:
    # 2
    pass


# =============================================================================
# DRILL 35 — Scenario: Firing Events (Gathering Callables)
# =============================================================================
async def run_drill_35():
    # SCENARIO: You have an array of functions listening to an event (Drill 34).
    # When the event fires, you need to execute all of them concurrently.

    # ACCEPTANCE CRITERIA:
    # 1. Use the `LISTENERS` and `@on` decorator from Drill 34.
    # 2. Decorate two async functions with `@on("boot")` that print "1" and "2".
    # 3. Write async `fire(event: str)`. Look up the list. Create a list of coroutines
    #    (by calling each func in the list).
    # 4. Await `asyncio.gather(*coroutines)`.
    # 5. Await `fire("boot")`.

    # --- WRITE YOUR CODE BELOW ---
    LISTENERS: dict[str, list] = {}

    def on(event: str):
        def decorator(func: Callable) -> Callable:
            if event not in LISTENERS:
                LISTENERS[event] = []
            LISTENERS[event].append(func)
            return func

        return decorator

    @on("boot")
    async def print_one():
        print(1)

    @on("boot")
    async def print_two():
        print(2)

    async def fire(event: str):
        coroutines = [func() for func in LISTENERS[event]]
        await asyncio.gather(*coroutines)

    await fire("boot")

    # EXPECTED OUTPUT:
    # 1
    # 2
    pass


# =============================================================================
# DRILL 36 — Scenario: Handling Missing Keys Safely
# =============================================================================
async def run_drill_36():
    # SCENARIO: A user tries to hit a URL that doesn't exist. You must handle
    # it without crashing the app with a KeyError.

    # ACCEPTANCE CRITERIA:
    # 1. Create `ENDPOINTS = {}` and a standard registry decorator.
    # 2. Decorate `home()`.
    # 3. Attempt to look up "/about" in `ENDPOINTS` using `.get()`.
    # 4. If `.get()` returns None, print "404 Not Found".

    # --- WRITE YOUR CODE BELOW ---
    ENDPOINTS = {}

    def route(path: str):
        def decorator(func: Callable) -> Callable:
            ENDPOINTS[path] = func
            return func

        return decorator

    @route(path="/home")
    async def home():
        pass

    lookup_about = ENDPOINTS.get("/about")
    if lookup_about is None:
        print("404 Not Found")

    # EXPECTED OUTPUT:
    # 404 Not Found
    pass


# =============================================================================
# DRILL 37 — Scenario: Async Wrapper Converting Model to Dict
# =============================================================================
async def run_drill_37():
    # SCENARIO: The opposite of Drill 22. Your business logic returns a nice
    # Pydantic object, but your JSON serializer needs a raw dictionary.

    # ACCEPTANCE CRITERIA:
    # 1. Define `Score` model with `points` (int).
    # 2. Write a decorator `return_as_dict`.
    # 3. Wrapper awaits func, takes the returned Pydantic object, calls `.model_dump()`,
    #    and returns the dict.
    # 4. Decorate `get_score()` which returns `Score(points=100)`.
    # 5. Await `get_score()` and print the result.

    # --- WRITE YOUR CODE BELOW ---
    class Score(BaseModel):
        points: int

    def return_as_dict(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            object = await func(*args, **kwargs)
            return object.model_dump()

        return wrapper

    @return_as_dict
    async def get_score():
        return Score(points=100)

    result = await get_score()
    print(result)
    # EXPECTED OUTPUT:
    # {'points': 100}
    pass


# =============================================================================
# DRILL 38 — Scenario: Blocking Execution (Auth Middleware)
# =============================================================================
async def run_drill_38():
    # SCENARIO: If a user is not an admin, the wrapper should prevent the
    # target function from running entirely.

    # ACCEPTANCE CRITERIA:
    # 1. Write an async decorator `require_admin`.
    # 2. Wrapper checks `kwargs.get("role")`. If not "admin", raise PermissionError.
    # 3. Decorate `delete_db(**kwargs)` which prints "Deleted!".
    # 4. Inside a try/except, await `delete_db(role="guest")`.
    # 5. Catch PermissionError and print "Access Denied".

    # --- WRITE YOUR CODE BELOW ---
    def require_admin(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            if kwargs.get("role") != "admin":
                raise PermissionError
            return await func(*args, **kwargs)

        return wrapper

    @require_admin
    async def delete_db(**kwargs):
        print("Deleted!")

    try:
        await delete_db(role="guest")
    except PermissionError:
        print("Access Denied")
    # EXPECTED OUTPUT:
    # Access Denied
    pass


# =============================================================================
# DRILL 39 — Scenario: Synthesizing Pydantic Constraints in Registries
# =============================================================================
async def run_drill_39():
    # SCENARIO: You are registering an event that accepts an ID, but it strictly
    # requires the ID to be greater than 0.

    # ACCEPTANCE CRITERIA:
    # 1. Define `Record` model with `id` (int, gt=0).
    # 2. Create `DB_HOOKS = {}` and a registry decorator.
    # 3. Decorate async `update(record: Record)` which prints "Updated".
    # 4. Retrieve `update` from `DB_HOOKS`.
    # 5. In a try/except, pass it `Record(id=-5)`. Catch ValidationError and print "Invalid ID".

    # --- WRITE YOUR CODE BELOW ---
    class Record(BaseModel):
        id: int = Field(gt=0)

    DB_HOOKS = {}

    def register(func: Callable) -> Callable:
        DB_HOOKS[func.__name__] = func
        return func

    @register
    async def update(record: Record):
        print("Updated")

    call_update = DB_HOOKS["update"]
    try:
        await call_update(Record(id=5))
    except ValidationError:
        print("Invalid Id")
    # EXPECTED OUTPUT:
    # Invalid ID
    pass


# =============================================================================
# DRILL 40 — FINAL BOSS: The Mini-Framework
# =============================================================================
async def run_drill_40():
    # SCENARIO: Combine all 4 concepts (Pydantic, Async, Registry, Wrapper)
    # into a single Decorator Factory!

    # ACCEPTANCE CRITERIA:
    # 1. Create `FRAMEWORK_ROUTES = {}`. Define `Body` model with `data` (str).
    # 2. Write a factory `app_route(path: str)`.
    # 3. Inside the factory, define the decorator. Save `func` to `FRAMEWORK_ROUTES[path]`.
    # 4. Inside the decorator, define an async wrapper. The wrapper prints "Validating...",
    #    then awaits the func. Return the wrapper.
    # 5. Decorate async `submit(payload: Body)` with `@app_route("/submit")` that prints `payload.data`.
    # 6. Retrieve the wrapper from `FRAMEWORK_ROUTES["/submit"]` and await it,
    #    passing `payload=Body(data="Hello")`.

    # --- WRITE YOUR CODE BELOW ---
    FRAMEWORK_ROUTES = {}

    class Body(BaseModel):
        data: str

    def app_route(path: str):
        def decorator(func: Callable) -> Callable:

            async def wrapper(*args, **kwargs):

                print("Validating...")
                return await func(*args, **kwargs)

            FRAMEWORK_ROUTES[path] = wrapper

            return wrapper

        return decorator

    @app_route("/submit")
    async def submit(payload: Body):
        print(payload.data)

    call_submit = FRAMEWORK_ROUTES["/submit"]
    await call_submit(payload=Body(data="Hello"))
    # EXPECTED OUTPUT:
    # Validating...
    # Hello
    pass


# =============================================================================
# RUNNER
# =============================================================================
async def main():
    await run_drill_21()
    await run_drill_22()
    await run_drill_23()
    await run_drill_24()
    await run_drill_25()
    await run_drill_26()
    await run_drill_27()
    await run_drill_28()
    await run_drill_29()
    await run_drill_30()
    await run_drill_31()
    await run_drill_32()
    await run_drill_33()
    await run_drill_34()
    await run_drill_35()
    await run_drill_36()
    await run_drill_37()
    await run_drill_38()
    await run_drill_39()
    await run_drill_40()


if __name__ == "__main__":
    asyncio.run(main())
