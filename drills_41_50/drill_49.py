import asyncio  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, ValidationError  # noqa: F401

# STARTED 727PM


async def run_drill_49():
    # =========================================================================
    # SCENARIO: The Hospital
    # =========================================================================
    # A hospital has multiple wards. Each ward has a set of dependency
    # functions that resolve into real objects before the handler runs.
    # If any dependency fails, access is blocked immediately.
    #
    # REQUIREMENTS:
    #
    # 1. A registry: WARDS = {}
    #
    # 2. A Pydantic model Patient with two fields:
    #    - name: str
    #    - blood_type: str
    #
    # 3. A Pydantic model Doctor with two fields:
    #    - name: str
    #    - specialty: str
    #
    # 4. Two async dependency functions:
    #    - get_patient(token: str) -> Patient
    #      - if token != "patient-token", raise ValueError("Invalid patient token")
    #      - otherwise return Patient(name="Alice", blood_type="A+")
    #    - get_doctor(token: str) -> Doctor
    #      - if token != "patient-token", raise ValueError("Invalid doctor token")
    #      - otherwise return Doctor(name="Dr. Smith", specialty="Cardiology")
    #
    # 5. A decorator @register(ward_name, dependencies: dict)
    #    - dependencies maps argument name to async dependency function
    #    - create an object in WARDS with handler as func, and dependencies as dependencies
    #    - return func
    #
    # 6. An async handler ward_handler(patient, doctor) (you write this):
    #    - prints f"  Patient: {patient.name} ({patient.blood_type})"
    #    - prints f"  Doctor: {doctor.name} ({doctor.specialty})"
    #
    # 7. Apply @register to ward_handler:
    #    ward_name    = "cardio_ward"
    #    dependencies = {"patient": get_patient, "doctor": get_doctor}
    #
    # 8. An async dispatch(ward_name: str, token: str):
    #    - if ward not found, print "404" and stop
    #    - create resolved = {}
    #    - loop through dependencies, await each one passing the token
    #    - collect results into resolved
    #    - if any dependency raises ValueError, print "Access Denied: <msg>" and stop
    #    - call the handler with **resolved
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    WARDS = {}

    class Patient(BaseModel):
        name: str
        blood_type: str

    class Doctor(BaseModel):
        name: str
        specialty: str

    async def get_patient(token: str) -> Patient:
        if token != "patient-token":
            raise ValueError("Invalid patient token")
        return Patient(name="Alice", blood_type="A+")

    async def get_doctor(token: str) -> Doctor:
        if token != "patient-token":
            raise ValueError("Invalid doctor token")
        return Doctor(name="Dr. Smith", specialty="Cardiology")

    def register(ward_name, dependencies: dict):
        def decorator(func: Callable) -> Callable:
            WARDS[ward_name] = {"handler": func, "dependencies": dependencies}
            return func

        return decorator

    @register(
        ward_name="cardio_ward",
        dependencies={"patient": get_patient, "doctor": get_doctor},
    )
    async def ward_handler(patient, doctor):
        print(f"  Patient: {patient.name} ({patient.blood_type})")
        print(f"  Doctor: {doctor.name} ({doctor.specialty})")

    async def dispatch(ward_name: str, token: str):
        if ward_name not in WARDS:
            print("404")
            return
        route = WARDS[ward_name]
        resolved = {}
        for arg_name, func in route["dependencies"].items():
            try:
                resolved[arg_name] = await func(token)
            except ValueError as msg:
                print(f"Access Denied: {msg}")
                return
        return await route["handler"](**resolved)

    # --- TESTS (do not modify) ---
    print("Test 1: Valid token")
    await dispatch("cardio_ward", token="patient-token")

    print("\nTest 2: Invalid token")
    await dispatch("cardio_ward", token="wrong-token")

    print("\nTest 3: Unknown ward")
    await dispatch("unknown_ward", token="patient-token")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: Valid token
    #   Patient: Alice (A+)
    #   Doctor: Dr. Smith (Cardiology)
    #
    # Test 2: Invalid token
    #   Access Denied: Invalid patient token
    #
    # Test 3: Unknown ward
    #   404
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_49())
