import asyncio  # noqa: F401
import time  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_72():
    # =========================================================================
    # SCENARIO: The University
    # =========================================================================
    # A university enrollment system exposes an API for submitting course
    # applications. To prevent the system from being overwhelmed, each
    # endpoint is rate-limited: it enforces a minimum delay between calls
    # on a per-instance basis.
    #
    # A decorator tracks the last call time and sleeps for the remaining
    # cooldown before the method runs. The method itself knows nothing
    # about rate limiting.
    #
    # NEW CONCEPT: async rate limiter with asyncio.sleep
    # - The decorator records when a method was last called, per instance
    # - On each call it computes how much of the cooldown period remains
    # - If time remaining > 0, it sleeps that long before proceeding
    # - asyncio.sleep() is non-blocking — it yields to the event loop
    # - time.monotonic() is the right clock: never goes backwards,
    #   not affected by system clock changes
    #
    # REQUIREMENTS:
    #
    # 1. A Pydantic model ApplicationForm:
    #    - student_name: str (min_length=2)
    #    - course_code: str
    #
    # 2. A decorator factory rate_limit(cooldown: float):
    #    - cooldown is in seconds (e.g. 0.1)
    #    - wraps func
    #    - tracks the last call time independently per instance
    #      (two instances of the same class must not share rate limit state)
    #    - on each call: if the cooldown period has not elapsed since the
    #      last call on this instance, sleep for the remaining time
    #    - after sleeping (if needed), call and await func
    #    - record the call time and return the result
    #
    # 3. A class EnrollmentSystem:
    #    - __init__(self, university: str):
    #        - self.university = university
    #        - self.applications = []
    #    - async method submit_application(self, form: ApplicationForm):
    #        - decorated with @rate_limit(cooldown=0.1)
    #        - appends form to self.applications
    #        - prints f"  Enrolled: {form.student_name} in {form.course_code}"
    #        - returns form.course_code
    #    - async method check_status(self, form: ApplicationForm):
    #        - decorated with @rate_limit(cooldown=0.1)
    #        - prints f"  Status check: {form.student_name}"
    #        - returns {"student": form.student_name, "status": "pending"}
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class ApplicationForm(BaseModel):
        student_name: str = Field(min_length=2)
        course_code: str

    def rate_limit(cooldown: float):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                instance = args[0]
                timer = f"_last_call_time_{func.__name__}"
                last_call_time = getattr(instance, timer, 0.0)
                now = time.monotonic()
                elapsed = now - last_call_time
                if elapsed < cooldown:
                    remaining_time = cooldown - elapsed
                    await asyncio.sleep(remaining_time)

                setattr(instance, timer, time.monotonic())
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    class EnrollmentSystem:
        def __init__(self, university: str):
            self.university = university
            self.applications = []

        @rate_limit(cooldown=0.1)
        async def submit_application(self, form: ApplicationForm):
            self.applications.append(form)
            print(f"  Enrolled: {form.student_name} in {form.course_code}")
            return form.course_code

        @rate_limit(cooldown=0.1)
        async def check_status(self, form: ApplicationForm):
            print(f"  Status check: {form.student_name}")
            return {"student": form.student_name, "status": "pending"}

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    system = EnrollmentSystem(university="UP Diliman")  # noqa: F821
    form_a = ApplicationForm(student_name="Alice", course_code="CS101")  # noqa: F821
    form_b = ApplicationForm(student_name="Bob", course_code="CS102")  # noqa: F821

    print("Test 1: Single submission works")
    result = await system.submit_application(form_a)
    assert result == "CS101", f"Expected 'CS101', got {result!r}"
    assert len(system.applications) == 1
    print("  PASS")

    print("\nTest 2: Rate limit enforces delay between calls")
    t0 = time.monotonic()
    await system.submit_application(form_b)
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.09, f"Expected >= 0.09s delay, got {elapsed:.3f}s"
    print(f"  PASS (waited {elapsed:.3f}s)")

    print("\nTest 3: check_status works and returns correct shape")
    await asyncio.sleep(0.15)  # clear the cooldown
    result = await system.check_status(form_a)
    assert result == {"student": "Alice", "status": "pending"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 4: Two instances have independent rate limit state")
    system2 = EnrollmentSystem(university="DLSU")  # noqa: F821
    await asyncio.sleep(0.15)  # clear cooldown on system
    t0 = time.monotonic()
    await system.submit_application(form_a)  # system — no wait (cooldown cleared)
    elapsed = time.monotonic() - t0
    assert elapsed < 0.09, f"system should not have waited, but elapsed={elapsed:.3f}s"
    t0 = time.monotonic()
    await system2.submit_application(form_b)  # system2 — also no wait (fresh instance)
    elapsed = time.monotonic() - t0
    assert elapsed < 0.09, f"system2 should not have waited, but elapsed={elapsed:.3f}s"
    print("  PASS")

    print("\nTest 5: Decorator preserved method names")
    assert system.submit_application.__name__ == "submit_application"
    assert system.check_status.__name__ == "check_status"
    print("  PASS")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Single submission works
    #   Enrolled: Alice in CS101
    #   PASS
    #
    # Test 2: Rate limit enforces delay between calls
    #   Enrolled: Bob in CS102
    #   PASS (waited 0.1XXs)
    #
    # Test 3: check_status works and returns correct shape
    #   Status check: Alice
    #   PASS
    #
    # Test 4: Two instances have independent rate limit state
    #   Enrolled: Alice in CS101
    #   Enrolled: Bob in CS102
    #   PASS
    #
    # Test 5: Decorator preserved method names
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_72())
