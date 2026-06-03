import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel  # noqa: F401


async def run_drill_51():
    # =========================================================================
    # SCENARIO: The Bank Account
    # =========================================================================
    # A BankAccount class has methods that should be blocked when the account
    # is frozen. Instead of checking inside every method, a decorator handles
    # the check automatically before the method runs.
    #
    # REQUIREMENTS:
    #
    # 1. A decorator require_active(func):
    #    - wraps func (preserve original function name)
    #    - inside wrapper, grab the instance from args[0]
    #    - if instance.frozen is True, print "Account is frozen" and return None
    #    - otherwise call and await the original func normally
    #
    # 2. A class BankAccount:
    #    - __init__(self, owner: str, balance: float):
    #        - self.owner = owner
    #        - self.balance = balance
    #        - self.frozen = False
    #    - async method deposit(self, amount: float):
    #        - decorated with @require_active
    #        - adds amount to self.balance
    #        - prints f"  Deposited ${amount}. Balance: ${self.balance}"
    #    - async method withdraw(self, amount: float):
    #        - decorated with @require_active
    #        - subtracts amount from self.balance
    #        - prints f"  Withdrew ${amount}. Balance: ${self.balance}"
    #    - async method freeze(self):
    #        - sets self.frozen = True
    #        - prints f"  Account frozen"
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    def require_active(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            instance = args[0]
            if instance.frozen is True:
                print("Account is frozen")
                return None
            return await func(*args, **kwargs)

        return wrapper

    class BankAccount:
        def __init__(self, owner: str, balance: float):
            self.owner = owner
            self.balance = balance
            self.frozen = False

        @require_active
        async def deposit(self, amount: float):
            self.balance += amount
            print(f"  Deposited ${amount}. Balance: ${self.balance}")

        @require_active
        async def withdraw(self, amount: float):
            self.balance -= amount
            print(f"  Withdrew ${amount}. Balance: ${self.balance}")

        async def freeze(self):
            self.frozen = True
            print("  Account frozen")

    # --- TESTS (do not modify) ---
    account = BankAccount(owner="Alice", balance=500.0)

    print("Test 1: Deposit on active account")
    await account.deposit(100.0)

    print("\nTest 2: Withdraw on active account")
    await account.withdraw(50.0)

    print("\nTest 3: Freeze the account")
    await account.freeze()

    print("\nTest 4: Deposit on frozen account")
    await account.deposit(200.0)

    print("\nTest 5: Withdraw on frozen account")
    await account.withdraw(50.0)

    print("\nTest 6: Confirm balance unchanged after frozen attempts")
    print(f"  Balance: ${account.balance}")

    print("\nTest 7: Confirm decorator preserved method name")
    print(f"  deposit name: {account.deposit.__name__}")
    print(f"  withdraw name: {account.withdraw.__name__}")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Deposit on active account
    #   Deposited $100.0. Balance: $600.0
    #
    # Test 2: Withdraw on active account
    #   Withdrew $50.0. Balance: $550.0
    #
    # Test 3: Freeze the account
    #   Account frozen
    #
    # Test 4: Deposit on frozen account
    #   Account is frozen
    #
    # Test 5: Withdraw on frozen account
    #   Account is frozen
    #
    # Test 6: Confirm balance unchanged after frozen attempts
    #   Balance: $550.0
    #
    # Test 7: Confirm decorator preserved method name
    #   deposit name: deposit
    #   withdraw name: withdraw
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_51())
