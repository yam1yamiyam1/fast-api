# drill_101.py
# noqa: F401

import pytest  # noqa: F401
from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
from fastapi.security import OAuth2PasswordBearer  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401


def run_drill_101():
    """
    SCENARIO: Blood Bank
    The blood bank's donor portal is protected. Every API request must carry
    a bearer token in the Authorization header. The server extracts the token
    and checks it against a known registry of valid donor tokens before
    granting access to the donor's record.

    REQUIREMENTS:
    1. VALID_TOKENS: dict[str, str]
       The in-memory token registry mapping raw token string to donor name.
       Pre-populated with two entries: "token-alice" → "Alice", "token-bob" → "Bob".

    2. oauth2_scheme: OAuth2PasswordBearer
       The scheme instance that extracts the bearer token from the
       Authorization header on every protected request. tokenUrl="/token".

    3. get_donor_name(token: str) → str
       A dependency function. token: str — the raw bearer token extracted from
       the Authorization header, representing the caller's identity credential.
       Looks up token in VALID_TOKENS. If found, returns the donor name.
       If not found, raises HTTPException with status_code=401 and
       detail="Invalid token".

    4. GET /donor
       Protected route. donor_name: str — the verified name of the authenticated
       donor, injected by get_donor_name via Depends.
       Returns {"donor": donor_name}.
    """

    # --- YOUR CODE HERE ---
    VALID_TOKENS: dict[str, str] = {"token-alice": "Alice", "token-bob": "Bob"}
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def get_donor_name(token: str = Depends(oauth2_scheme)):

        if token not in VALID_TOKENS:
            raise HTTPException(status_code=401, detail="Invalid token")
        return VALID_TOKENS[token]

    app = FastAPI()

    @app.get("/donor")
    def get_donor(donor_name: str = Depends(get_donor_name)):
        return {"donor": donor_name}

    client = TestClient(app, raise_server_exceptions=False)

    # Test 1: valid token for Alice
    print("Test 1: valid token returns donor name for Alice")
    resp = client.get("/donor", headers={"Authorization": "Bearer token-alice"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 200
    assert resp.json() == {"donor": "Alice"}
    print("  PASS")

    # Test 2: valid token for Bob
    print("Test 2: valid token returns donor name for Bob")
    resp = client.get("/donor", headers={"Authorization": "Bearer token-bob"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 200
    assert resp.json() == {"donor": "Bob"}
    print("  PASS")

    # Test 3: invalid token returns 401
    print("Test 3: invalid token returns 401")
    resp = client.get("/donor", headers={"Authorization": "Bearer token-unknown"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"
    print("  PASS")

    # Test 4: missing Authorization header returns 401
    print("Test 4: missing Authorization header returns 401")
    resp = client.get("/donor")
    print(f"  status={resp.status_code}")
    assert resp.status_code == 401
    print("  PASS")


run_drill_101()

# --- EXPECTED OUTPUT ---
# Test 1: valid token returns donor name for Alice
#   status=200, body={'donor': 'Alice'}
#   PASS
# Test 2: valid token returns donor name for Bob
#   status=200, body={'donor': 'Bob'}
#   PASS
# Test 3: invalid token returns 401
#   status=401, body={'detail': 'Invalid token'}
#   PASS
# Test 4: missing Authorization header returns 401
#   status=401
#   PASS
