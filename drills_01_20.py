import asyncio
from typing import List, Optional  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401

# =============================================================================
# RECIPE BOOK (Syntax Reference)
# =============================================================================
# --- PYDANTIC ---
# Create Model:      class MyModel(BaseModel): ...
# Add Constraints:   field_name: type = Field(gt=0, min_length=3, max_length=10)
# Default values:    field_name: Optional[str] = Field(default=None)
# Dict to Model:     my_obj = MyModel(**my_dict)
# Model to Dict:     my_dict = my_obj.model_dump()
# Catching errors:   try: ... except ValidationError as e: print(e)
#
# --- ASYNC/AWAIT ---
# Define coroutine:  async def my_task(args): ...
# Call coroutine:    result = await my_task(args)
# Pause loop:        await asyncio.sleep(0.1)  # (0 yields control immediately)
# Concurrency:       results = await asyncio.gather(task1(), task2(), task3())
# =============================================================================


# =============================================================================
# DRILL 01 — Scenario: Core Data Structures
# =============================================================================
async def run_drill_01():
    # SCENARIO: You are building an e-commerce backend. You need a standard
    # data structure to represent an item being added to a shopping cart.

    # ACCEPTANCE CRITERIA:
    # 1. Define a Pydantic model `CartItem`.
    # 2. It requires `name` (str), `price` (float), and `is_taxable` (bool).
    # 3. Instantiate the model with "Laptop", 999.99, and True.
    # 4. Print the resulting object.

    # --- WRITE YOUR CODE BELOW ---
    class CartItem(BaseModel):
        name: str
        price: float
        is_taxable: bool

    print(CartItem(name="Laptop", price=999.99, is_taxable=True))
    # EXPECTED OUTPUT:
    # name='Laptop' price=999.99 is_taxable=True
    pass


# =============================================================================
# DRILL 02 — Scenario: Enforcing Business Rules
# =============================================================================
async def run_drill_02():
    # SCENARIO: Users are bypassing your frontend validation and sending
    # bad data to the registration API. You need to enforce rules on the backend.

    # ACCEPTANCE CRITERIA:
    # 1. Define a model `NewUser`.
    # 2. It requires `username` (string, must be at least 4 characters).
    # 3. It requires `age` (int, must be strictly greater than 17).
    # 4. Instantiate a valid user ("Alice", 25) and print it.

    # --- WRITE YOUR CODE BELOW ---
    class NewUser(BaseModel):
        username: str = Field(min_length=4)
        age: int = Field(gt=17)

    print(NewUser(username="Alice", age=25))
    # EXPECTED OUTPUT:
    # username='Alice' age=25
    pass


# =============================================================================
# DRILL 03 — Scenario: Graceful Error Handling
# =============================================================================
async def run_drill_03():
    # SCENARIO: If a user sends a bad payload, your entire server crashes with
    # a traceback. You need to catch Pydantic's specific validation error.

    # ACCEPTANCE CRITERIA:
    # 1. Reuse the `NewUser` model from Drill 02 (redefine it here).
    # 2. Try to instantiate it with invalid data: username="Bob", age=12.
    # 3. Wrap the instantiation in a try/except block.
    # 4. Catch the specific Pydantic error and print: "Validation failed!"

    # --- WRITE YOUR CODE BELOW ---
    class NewUser(BaseModel):
        username: str = Field(min_length=4)
        age: int = Field(gt=17)

    try:
        print(NewUser(username="Bob", age=12))
    except ValidationError as e:
        print(f"Validation Failed: {e}")
    # EXPECTED OUTPUT:
    # Validation failed!
    pass


# =============================================================================
# DRILL 04 — Scenario: Parsing API Payloads (Dict to Model)
# =============================================================================
async def run_drill_04():
    # SCENARIO: Your web framework receives JSON from the client and converts
    # it into a Python dictionary. You must safely parse this dictionary
    # into a Pydantic model.

    # ACCEPTANCE CRITERIA:
    # 1. Define a model `ServerConfig` with `host` (str) and `port` (int).
    # 2. Create a raw dictionary: payload = {"host": "127.0.0.1", "port": 8080}
    # 3. Convert the dictionary into a `ServerConfig` instance dynamically
    #    (do not hardcode the kwargs).
    # 4. Print the resulting model instance.

    # --- WRITE YOUR CODE BELOW ---
    class ServerConfig(BaseModel):
        host: str
        port: int

    payload = {"host": "127.0.0.1", "port": 8080}
    print(ServerConfig(**payload))
    # EXPECTED OUTPUT:
    # host='127.0.0.1' port=8080
    pass


# =============================================================================
# DRILL 05 — Scenario: Preparing DB Inserts (Model to Dict)
# =============================================================================
async def run_drill_05():
    # SCENARIO: You just finished processing a `ServerConfig` object, but
    # your database driver (like asyncpg) only accepts standard Python dictionaries,
    # not Pydantic objects.

    # ACCEPTANCE CRITERIA:
    # 1. Define the `ServerConfig` model and instantiate it.
    # 2. Convert the Pydantic instance back into a standard dictionary.
    # 3. Print the dictionary.

    # --- WRITE YOUR CODE BELOW ---
    class ServerConfig(BaseModel):
        host: str
        port: int

    payload = ServerConfig(host="127.0.0.1", port=8080)
    print(dict(payload))
    # EXPECTED OUTPUT:
    # {'host': '127.0.0.1', 'port': 8080}
    pass


# =============================================================================
# DRILL 06 — Scenario: Handling Missing Data
# =============================================================================
async def run_drill_06():
    # SCENARIO: Your user profile API allows users to skip providing a
    # biography. The backend must handle this missing field gracefully.

    # ACCEPTANCE CRITERIA:
    # 1. Define a model `Profile`.
    # 2. It requires `nickname` (str).
    # 3. It has `bio`, which is an optional string. Set its default to None.
    # 4. Instantiate the profile passing ONLY the nickname ("Ghost").
    # 5. Print the instance.

    # --- WRITE YOUR CODE BELOW ---
    class Profile(BaseModel):
        nickname: str
        bio: Optional[str] = None

    print(Profile(nickname="Ghost"))
    # EXPECTED OUTPUT:
    # nickname='Ghost' bio=None
    pass


# =============================================================================
# DRILL 07 — Scenario: Complex Nested Payloads
# =============================================================================
async def run_drill_07():
    # SCENARIO: A food delivery app receives an order payload that contains
    # nested address information.

    # ACCEPTANCE CRITERIA:
    # 1. Define an `Address` model with `street` (str) and `zip_code` (str).
    # 2. Define an `Order` model with `order_id` (int) and `delivery_address`
    #    (must be an instance of the Address model).
    # 3. Instantiate an `Order` (you will need to instantiate the Address inside it).
    # 4. Print the nested zip code using dot notation.

    # --- WRITE YOUR CODE BELOW ---
    class Address(BaseModel):
        street: str
        zip_code: str

    class Order(BaseModel):
        order_id: int
        delivery_address: Address

    print(
        Order(
            order_id=101, delivery_address=Address(street="Gen Tinio", zip_code="3100")
        )
    )
    # EXPECTED OUTPUT:
    # (whatever zip code you assigned)
    pass


# =============================================================================
# DRILL 08 — Scenario: Rejecting Wrong Data Types
# =============================================================================
async def run_drill_08():
    # SCENARIO: A client app keeps sending the payment amount as a string
    # ("one hundred") instead of a float (100.0). You need to prove your backend
    # will block it.

    # ACCEPTANCE CRITERIA:
    # 1. Define a `Payment` model with `amount` (float).
    # 2. Try to instantiate it with amount="lots of money".
    # 3. Catch the ValidationError and print the error object itself.

    # --- WRITE YOUR CODE BELOW ---
    class Payment(BaseModel):
        amount: float

    try:
        print(Payment(amount="lots of money"))
    except ValidationError as e:
        print(e)
    # EXPECTED OUTPUT:
    # 1 validation error for Payment... Input should be a valid number...
    pass


# =============================================================================
# DRILL 09 — Scenario: Hard Caps on Input Length
# =============================================================================
async def run_drill_09():
    # SCENARIO: Your database column for "status" can only hold 20 characters.
    # You must prevent strings longer than 20 chars from entering the system.

    # ACCEPTANCE CRITERIA:
    # 1. Define a `StatusUpdate` model with `text` (str, max_length of 20).
    # 2. Try to instantiate it with a 30-character string.
    # 3. Catch the ValidationError and print "Too long!".

    # --- WRITE YOUR CODE BELOW ---
    class StatusUpdate(BaseModel):
        text: str = Field(max_length=20)

    try:
        print(
            StatusUpdate(
                text="wertyuiopsdfghjkldfghjkdfghjkdfghjfghjkfghjkfghjkldfghjkdfghjk"
            )
        )
    except ValidationError as e:
        print(e)
    # EXPECTED OUTPUT:
    # Too long!
    pass


# =============================================================================
# DRILL 10 — Scenario: Validating Arrays of Data
# =============================================================================
async def run_drill_10():
    # SCENARIO: An article can have multiple tags. You need to ensure the
    # payload contains a proper list of strings.

    # ACCEPTANCE CRITERIA:
    # 1. Define an `Article` model with `title` (str) and `tags` (List of strings).
    # 2. Instantiate it with a title and a list of 3 tags.
    # 3. Loop through the `tags` attribute and print each tag.

    # --- WRITE YOUR CODE BELOW ---
    class Article(BaseModel):
        title: str
        tags: list[str]

    article = Article(title="Article 1", tags=["tag1", "tag2", "tag3"])
    for t in article.tags:
        print(t)
    # EXPECTED OUTPUT:
    # tag1
    # tag2
    # tag3
    pass


# =============================================================================
# DRILL 11 — Scenario: Firing an Async Task
# =============================================================================
async def run_drill_11():
    # SCENARIO: You are writing a background script that cleans up temporary files.
    # It must run asynchronously so it doesn't block the main web server.

    # ACCEPTANCE CRITERIA:
    # 1. Define an async function `cleanup_files` that prints "Cleaning...".
    # 2. Execute that function correctly inside `run_drill_11`.

    # --- WRITE YOUR CODE BELOW ---
    async def cleanup_files():
        print("Cleaning...")

    await cleanup_files()
    # EXPECTED OUTPUT:
    # Cleaning...
    pass


# =============================================================================
# DRILL 12 — Scenario: Non-Blocking Delays
# =============================================================================
async def run_drill_12():
    # SCENARIO: You need to introduce an artificial delay to rate-limit requests,
    # but you cannot use `time.sleep()` because it freezes the entire server.

    # ACCEPTANCE CRITERIA:
    # 1. Define an async function `rate_limit_delay`.
    # 2. Inside it, yield to the event loop for 0.1 seconds.
    # 3. Print "Delay complete".
    # 4. Await it.

    # --- WRITE YOUR CODE BELOW ---
    async def rate_limit_display():
        await asyncio.sleep(0.1)
        print("Delay complete")

    await rate_limit_display()
    # EXPECTED OUTPUT:
    # Delay complete
    pass


# =============================================================================
# DRILL 13 — Scenario: Awaiting Data Fetch
# =============================================================================
async def run_drill_13():
    # SCENARIO: A function is querying an external API. You need to retrieve
    # the returned data, but it's an async function.

    # ACCEPTANCE CRITERIA:
    # 1. Define an async function `fetch_api_status` that returns the int 200.
    # 2. Execute the function, capture the returned value in a variable,
    #    and print the variable.

    # --- WRITE YOUR CODE BELOW ---
    async def fetch_api_status():
        return 200

    response = await fetch_api_status()
    print(response)
    # EXPECTED OUTPUT:
    # 200
    pass


# =============================================================================
# DRILL 14 — Scenario: Dependent Async Execution (Sequential)
# =============================================================================
async def run_drill_14():
    # SCENARIO: You must fetch a user's ID from the DB first, and ONLY THEN
    # use that ID to fetch their billing details. They cannot run concurrently.

    # ACCEPTANCE CRITERIA:
    # 1. Define async `get_user_id()` returning 99.
    # 2. Define async `get_billing(user_id)` returning f"Billing for {user_id}".
    # 3. Execute them sequentially: get the ID, then pass it to the billing function.
    # 4. Print the final billing result.

    # --- WRITE YOUR CODE BELOW ---
    async def get_user_id():
        return 99

    async def get_billing(user_id):
        return f"Billing for {user_id}"

    user_id = await get_user_id()
    billing = await get_billing(user_id)
    print(billing)
    # EXPECTED OUTPUT:
    # Billing for 99
    pass


# =============================================================================
# DRILL 15 — Scenario: Independent Async Execution (Concurrent)
# =============================================================================
async def run_drill_15():
    # SCENARIO: You are scraping 3 different websites. They don't rely on
    # each other, so waiting for them sequentially wastes time. You must
    # run them at the exact same time.

    # ACCEPTANCE CRITERIA:
    # 1. Define async `scrape_site(name)` which sleeps for 0.05s and prints f"{name} done".
    # 2. Use the standard asyncio method to trigger `scrape_site("A")`,
    #    `scrape_site("B")`, and `scrape_site("C")` concurrently.

    # --- WRITE YOUR CODE BELOW ---
    async def scrape_site(name):
        await asyncio.sleep(0.05)
        print(f"{name} done")

    await asyncio.gather(scrape_site("A"), scrape_site("B"), scrape_site("C"))
    # EXPECTED OUTPUT:
    # A done
    # B done
    # C done
    pass


# =============================================================================
# DRILL 16 — Scenario: Async Args & Keyword Args
# =============================================================================
async def run_drill_16():
    # SCENARIO: Async functions handle arguments exactly like sync functions.
    # Prove it.

    # ACCEPTANCE CRITERIA:
    # 1. Define async `calculate_discount(price, discount=0.1)`.
    # 2. Return `price * (1 - discount)`.
    # 3. Await it with price=100 and discount=0.2. Print the result.

    # --- WRITE YOUR CODE BELOW ---
    async def calculate_discount(price, discount=0.1):
        return price * (1 - discount)

    result = await calculate_discount(price=100, discount=0.2)
    print(result)
    # EXPECTED OUTPUT:
    # 80.0
    pass


# =============================================================================
# DRILL 17 — Scenario: Async Functions Calling Async Functions
# =============================================================================
async def run_drill_17():
    # SCENARIO: Your Controller layer needs to call your Service layer,
    # which calls your Database layer. All are async.

    # ACCEPTANCE CRITERIA:
    # 1. Define async `db_ping()` returning "db_ok".
    # 2. Define async `service_ping()` which awaits `db_ping()` and returns the result.
    # 3. Inside `run_drill_17`, await `service_ping()` and print the result.
    async def db_ping():
        return "db_ok"

    async def service_ping():
        result = await db_ping()
        print(result)

    await service_ping()
    # --- WRITE YOUR CODE BELOW ---

    # EXPECTED OUTPUT:
    # db_ok
    pass


# =============================================================================
# DRILL 18 — Scenario: Aggregating Concurrent Results
# =============================================================================
async def run_drill_18():
    # SCENARIO: You ran multiple independent tasks concurrently (like in Drill 15),
    # but this time, the tasks return data instead of just printing. You need
    # to capture all their return values into a single list.

    # ACCEPTANCE CRITERIA:
    # 1. Define async `fetch_metric(machine_id)` returning `machine_id * 10`.
    # 2. Run the function concurrently for machine_ids 1, 2, and 3.
    # 3. Capture the aggregated results array and print it.

    # --- WRITE YOUR CODE BELOW ---
    async def fetch_metric(machine_id):
        return machine_id * 10

    result = await asyncio.gather(fetch_metric(1), fetch_metric(2), fetch_metric(3))
    print(result)
    # EXPECTED OUTPUT:
    # [10, 20, 30]
    pass


# =============================================================================
# DRILL 19 — Scenario: Catching Errors in Async Flows
# =============================================================================
async def run_drill_19():
    # SCENARIO: A third-party API is down and throwing errors. You must catch
    # the error so your main server doesn't crash.

    # ACCEPTANCE CRITERIA:
    # 1. Define async `unstable_api()` that raises `ValueError("API offline")`.
    # 2. Await the function inside a try/except block.
    # 3. Catch the ValueError and print its message.

    # --- WRITE YOUR CODE BELOW ---
    async def unstable_api():
        raise ValueError("API offline")

    try:
        await unstable_api()
    except ValueError as e:
        print(e)
    # EXPECTED OUTPUT:
    # API offline
    pass


# =============================================================================
# DRILL 20 — Scenario: Yielding in Heavy Loops
# =============================================================================
async def run_drill_20():
    # SCENARIO: You have a long-running `while` or `for` loop processing thousands
    # of records. If it doesn't pause, it will starve the web server of resources.

    # ACCEPTANCE CRITERIA:
    # 1. Write a `for` loop that iterates from 1 to 3.
    # 2. On every iteration, explicitly yield control to the event loop
    #    (sleep for 0 seconds).
    # 3. Print the loop number.

    # --- WRITE YOUR CODE BELOW ---
    for i in range(1, 4):
        await asyncio.sleep(1)
        print(i)
    # EXPECTED OUTPUT:
    # 1
    # 2
    # 3
    pass


# =============================================================================
# RUNNER
# =============================================================================
async def main():
    await run_drill_01()
    await run_drill_02()
    await run_drill_03()
    await run_drill_04()
    await run_drill_05()
    await run_drill_06()
    await run_drill_07()
    await run_drill_08()
    await run_drill_09()
    await run_drill_10()
    await run_drill_11()
    await run_drill_12()
    await run_drill_13()
    await run_drill_14()
    await run_drill_15()
    await run_drill_16()
    await run_drill_17()
    await run_drill_18()
    await run_drill_19()
    await run_drill_20()


if __name__ == "__main__":
    asyncio.run(main())
