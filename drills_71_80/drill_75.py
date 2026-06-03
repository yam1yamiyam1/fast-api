import asyncio  # noqa: F401
from functools import wraps  # noqa: F401
from typing import Callable  # noqa: F401

from pydantic import BaseModel, Field, ValidationError  # noqa: F401


async def run_drill_75():
    # =========================================================================
    # SCENARIO: The Pharmacy
    # =========================================================================
    # A pharmacy prescription system resolves multiple checks before filling
    # a prescription. Each check is independent — they don't need each other's
    # results. Running them sequentially wastes time. Running them in parallel
    # with asyncio.gather() resolves all checks at once.
    #
    # NEW CONCEPT: parallel dependency resolution with asyncio.gather
    # - When multiple async functions are independent of each other,
    #   gather() runs them all concurrently and returns all results at once
    # - gather() returns results in the same order as the coroutines passed in,
    #   regardless of which finishes first
    # - If any coroutine raises, gather() raises that exception immediately
    # - Shape: results = await asyncio.gather(dep1(), dep2(), dep3())
    # - This is how FastAPI resolves multiple independent Depends() calls
    #
    # REQUIREMENTS:
    #
    # 1. A Pydantic model Prescription:
    #    - patient_id: str
    #    - drug: str
    #    - dosage_mg: float (gt=0)
    #
    # 2. Three async dependency functions:
    #    - async def verify_patient(patient_id: str) -> dict:
    #        - simulates I/O with asyncio.sleep(0.05)
    #        - if patient_id == "banned", raise ValueError("Patient is banned")
    #        - otherwise return {"patient_id": patient_id, "verified": True}
    #    - async def check_drug_inventory(drug: str) -> dict:
    #        - simulates I/O with asyncio.sleep(0.05)
    #        - if drug == "unavailable", raise ValueError("Drug out of stock")
    #        - otherwise return {"drug": drug, "in_stock": True}
    #    - async def check_insurance(patient_id: str) -> dict:
    #        - simulates I/O with asyncio.sleep(0.05)
    #        - if patient_id == "uninsured", raise ValueError("No insurance coverage")
    #        - otherwise return {"patient_id": patient_id, "covered": True}
    #
    # 3. A registry: ROUTES = {}
    #
    # 4. A decorator @route(action: str):
    #    - stores handler in ROUTES under action
    #    - returns func unchanged
    #
    # 5. An async handler fill_prescription(rx: Prescription, patient: dict, inventory: dict, insurance: dict) -> dict:
    #    - decorated with @route("fill")
    #    - returns {
    #        "patient_id": rx.patient_id,
    #        "drug": rx.drug,
    #        "dosage_mg": rx.dosage_mg,
    #        "patient_verified": patient["verified"],
    #        "in_stock": inventory["in_stock"],
    #        "covered": insurance["covered"],
    #        "status": "filled"
    #      }
    #
    # 6. An async dispatch(action: str, raw_payload: dict) -> dict:
    #    - if action not in ROUTES, return {"error": f"unknown action: {action}"}
    #    - validate raw_payload into Prescription
    #      - if ValidationError, return {"error": "invalid prescription"}
    #    - resolve all three dependencies IN PARALLEL using asyncio.gather
    #      passing the appropriate fields from the validated Prescription
    #    - if any dependency raises ValueError, return {"error": str(e)}
    #    - call and await the handler passing rx and all three resolved results
    #    - return the result
    #
    # =========================================================================

    # --- YOUR CODE HERE ---
    class Prescription(BaseModel):
        patient_id: str
        drug: str
        dosage_mg: float = Field(gt=0)

    async def verify_patient(patient_id: str) -> dict:
        await asyncio.sleep(0.05)
        if patient_id == "banned":
            raise ValueError("Patient is banned")
        return {"patient_id": patient_id, "verified": True}

    async def check_drug_inventory(drug: str) -> dict:
        await asyncio.sleep(0.05)
        if drug == "unavailable":
            raise ValueError("Drug out of stock")
        return {"drug": drug, "in_stock": True}

    async def check_insurance(patient_id: str) -> dict:
        await asyncio.sleep(0.05)
        if patient_id == "uninsured":
            raise ValueError("No insurance coverage")
        return {"patient_id": patient_id, "covered": True}

    ROUTES = {}

    def route(action: str):
        def decorator(func: Callable):
            ROUTES[action] = func
            return func

        return decorator

    @route("fill")
    async def fill_prescription(
        rx: Prescription, patient: dict, inventory: dict, insurance: dict
    ):
        return {
            "patient_id": rx.patient_id,
            "drug": rx.drug,
            "dosage_mg": rx.dosage_mg,
            "patient_verified": patient["verified"],
            "in_stock": inventory["in_stock"],
            "covered": insurance["covered"],
            "status": "filled",
        }

    async def dispatch(action: str, raw_payload: dict):
        if action not in ROUTES:
            return {"error": f"unknown action: {action}"}
        try:
            valid_pd = Prescription(**raw_payload)
        except ValidationError:
            return {"error": "invalid prescription"}
        try:
            results = await asyncio.gather(
                verify_patient(valid_pd.patient_id),
                check_drug_inventory(valid_pd.drug),
                check_insurance(valid_pd.patient_id),
            )

        except ValueError as e:
            return {"error": str(e)}

        patient, inventory, insurance = results
        return await ROUTES[action](valid_pd, patient, inventory, insurance)

    # =========================================================================
    # TESTS (do not modify)
    # =========================================================================
    import time  # noqa: F401

    print("Test 1: valid prescription — all deps resolve in parallel")
    t0 = time.monotonic()
    result = await dispatch(
        "fill", {"patient_id": "P-001", "drug": "Amoxicillin", "dosage_mg": 500.0}
    )  # noqa: F821
    elapsed = time.monotonic() - t0
    print(f"  {result}")
    assert result == {
        "patient_id": "P-001",
        "drug": "Amoxicillin",
        "dosage_mg": 500.0,
        "patient_verified": True,
        "in_stock": True,
        "covered": True,
        "status": "filled",
    }, f"Got {result!r}"
    # three 0.05s sleeps in parallel should finish in ~0.05s, not ~0.15s
    assert elapsed < 0.12, f"Expected parallel execution (~0.05s), got {elapsed:.3f}s"
    print(f"  elapsed: {elapsed:.3f}s (parallel)")
    print("  PASS")

    print("\nTest 2: banned patient — dep raises ValueError")
    result = await dispatch(
        "fill", {"patient_id": "banned", "drug": "Amoxicillin", "dosage_mg": 500.0}
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "Patient is banned"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 3: unavailable drug — dep raises ValueError")
    result = await dispatch(
        "fill", {"patient_id": "P-002", "drug": "unavailable", "dosage_mg": 100.0}
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "Drug out of stock"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 4: uninsured patient — dep raises ValueError")
    result = await dispatch(
        "fill", {"patient_id": "uninsured", "drug": "Aspirin", "dosage_mg": 100.0}
    )  # noqa: F821
    print(f"  {result}")
    assert result["error"] in ("No insurance coverage", "Patient is banned"), (
        f"Got {result!r}"
    )
    print("  PASS")

    print("\nTest 5: invalid payload — dosage_mg <= 0")
    result = await dispatch(
        "fill", {"patient_id": "P-003", "drug": "Aspirin", "dosage_mg": -1.0}
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "invalid prescription"}, f"Got {result!r}"
    print("  PASS")

    print("\nTest 6: unknown action")
    result = await dispatch(
        "refund", {"patient_id": "P-001", "drug": "Aspirin", "dosage_mg": 100.0}
    )  # noqa: F821
    print(f"  {result}")
    assert result == {"error": "unknown action: refund"}, f"Got {result!r}"
    print("  PASS")

    # =========================================================================
    # EXPECTED OUTPUT:
    #
    # Test 1: valid prescription — all deps resolve in parallel
    #   {'patient_id': 'P-001', 'drug': 'Amoxicillin', 'dosage_mg': 500.0,
    #    'patient_verified': True, 'in_stock': True, 'covered': True, 'status': 'filled'}
    #   elapsed: 0.0XXs (parallel)
    #   PASS
    #
    # Test 2: banned patient — dep raises ValueError
    #   {'error': 'Patient is banned'}
    #   PASS
    #
    # Test 3: unavailable drug — dep raises ValueError
    #   {'error': 'Drug out of stock'}
    #   PASS
    #
    # Test 4: uninsured patient — dep raises ValueError
    #   {'error': 'No insurance coverage'}  (or 'Patient is banned' — gather order)
    #   PASS
    #
    # Test 5: invalid payload — dosage_mg <= 0
    #   {'error': 'invalid prescription'}
    #   PASS
    #
    # Test 6: unknown action
    #   {'error': 'unknown action: refund'}
    #   PASS
    # =========================================================================


if __name__ == "__main__":
    asyncio.run(run_drill_75())
