import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401


async def run_drill_41():
    # =========================================================================
    # THE SCENARIO: The Secure Payment Gateway
    # =========================================================================
    # You are building the core router for a payment processing system.
    #
    # SYSTEM REQUIREMENTS:
    # 1. We need a central registry called `GATEWAY`.
    # 2. We need a Pydantic model called `Payment` that requires an `amount` (float).
    # 3. We need a custom decorator called `@secure_endpoint(path, required_role)`.
    #    When applied to a function, this decorator must:
    #      - Register the function into the `GATEWAY` dictionary under the given path.
    #      - Preserve the original function's name (metadata).
    #      - Wrap the function to check if the caller has the `required_role`.
    #        (Assume the caller's role is passed into the function as `kwargs["role"]`).
    #        If they don't have the required role, raise a PermissionError("Access Denied").
    #
    # 4. We need a target async function named `process_refund` that takes a
    #    `Payment` object and `**kwargs`. It should print: "Refunding ${amount}".
    #    It must be secured at the path "/refund" and require the "admin" role.
    #
    # 5. We need an async function `dispatch(path: str, raw_payload: dict, role: str)`.
    #    It must:
    #      - Look up the correct function in the GATEWAY.
    #      - Convert the raw_payload into a Payment Pydantic object.
    #      - Execute the function, passing the Payment object and the role.
    #      - Gracefully catch a `PermissionError` and print "Error: Access Denied".
    #      - Gracefully catch a Pydantic `ValidationError` and print "Error: Bad Data".
    # =========================================================================

    # --- WRITE YOUR CODE BELOW ---
    GATEWAY = {}

    class Payment(BaseModel):
        amount: float

    def secure_endpoint(path: str, allowed_roles: list[str]):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):

                if kwargs.get("role") not in allowed_roles:
                    raise PermissionError("Access Denied")
                return await func(*args, **kwargs)

            GATEWAY[path] = {"func": wrapper, "allowed_roles": allowed_roles}
            return wrapper

        return decorator

    @secure_endpoint(path="/refund", allowed_roles=["admin"])
    async def process_refund(payment: Payment, **kwargs):
        print(f"Refunding ${payment.amount}")

    async def dispatch(path: str, raw_payload: dict, role: str):
        try:
            process = GATEWAY[path]["func"]
            payment_obj = Payment(**raw_payload)
            await process(payment_obj, role=role)
        except PermissionError:
            print("Error: Access Denied")
        except ValidationError:
            print("Error: Bad Data")

    await dispatch("/refund", {"amount": 50.50}, role=["admin"])
    # --- EXECUTION TESTS (Do not modify these) ---
    print(f"Registered Name: {GATEWAY['/refund']['func'].__name__}")

    print("\nTest 1: Valid Admin & Valid Data")
    await dispatch("/refund", {"amount": 50.50}, role=["admin"])

    print("\nTest 2: Invalid Role")
    await dispatch("/refund", {"amount": 50.50}, role=["user"])

    print("\nTest 3: Invalid Data")
    await dispatch("/refund", {"amount": "five dollars"}, role=["admin"])

    # =========================================================================
    # EXPECTED OUTPUT:
    # Registered Name: process_refund
    #
    # Test 1: Valid Admin & Valid Data
    # Refunding $50.5
    #
    # Test 2: Invalid Role
    # Error: Access Denied
    #
    # Test 3: Invalid Data
    # Error: Bad Data
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_41())
