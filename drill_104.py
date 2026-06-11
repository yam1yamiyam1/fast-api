# drill_104.py
# noqa: F401

from fastapi import FastAPI, Depends, HTTPException  # noqa: F401
from fastapi.security import OAuth2PasswordBearer  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from jose import jwt, JWTError  # noqa: F401
from pydantic import BaseModel  # noqa: F401
from datetime import datetime, timezone, timedelta  # noqa: F401


def run_drill_104():
    """
    SCENARIO: Weather Station
    The weather station API serves different endpoints depending on the
    caller's role. Meteorologists can read sensor data. Only admins can
    submit calibration updates. A route checks the current user's role
    and rejects callers who don't have the required role.

    REQUIREMENTS:
    1. SECRET_KEY: str
       The secret used to sign and verify all JWTs. Value: "weather-secret".

    2. ALGORITHM: str
       The signing algorithm. Value: "HS256".

    3. class User(BaseModel)
       Represents an authenticated station operator.
       Fields:
         username: str — the operator's login handle.
         role: str — the operator's role; either "meteorologist" or "admin".

    4. make_token(username: str, role: str, expires_delta: timedelta) -> str
       Builds and returns a signed JWT with "sub", "role", and "exp" claims.
       username: str — stored as "sub".
       role: str — stored as "role".
       expires_delta: timedelta — token lifetime from utcnow.

    5. oauth2_scheme: OAuth2PasswordBearer
       Extracts the bearer token from the Authorization header. tokenUrl="/token".

    6. get_current_user(token: str) -> User
       A dependency. token: str — the raw JWT from the Authorization header.
       Decodes the token, extracts "sub" and "role", returns a User.
       On any failure raises HTTPException status_code=401, detail="Invalid token".

    7. require_role(required_role: str) -> callable
       A dependency factory. required_role: str — the role a caller must have
       to access the route, representing the minimum clearance level.
       Returns a dependency function that takes current_user: User (injected via
       get_current_user) and raises HTTPException status_code=403,
       detail="Forbidden" if current_user.role != required_role.
       Otherwise returns current_user.

    8. GET /sensors
       Protected route — requires role "meteorologist".
       current_user: User — the verified operator, injected via require_role.
       Returns {"data": "sensor readings", "reader": current_user.username}.

    9. POST /calibrate
       Protected route — requires role "admin".
       current_user: User — the verified operator, injected via require_role.
       Returns {"status": "calibrated", "by": current_user.username}.
    """

    app = FastAPI()

    # --- YOUR CODE HERE ---

    client = TestClient(app, raise_server_exceptions=False)

    # Test 1: meteorologist can read sensors
    print("Test 1: meteorologist can read sensors")
    token = make_token("yuna", "meteorologist", timedelta(minutes=5))
    resp = client.get("/sensors", headers={"Authorization": f"Bearer {token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 200
    assert resp.json() == {"data": "sensor readings", "reader": "yuna"}
    print("  PASS")

    # Test 2: meteorologist cannot calibrate
    print("Test 2: meteorologist cannot calibrate")
    resp = client.post("/calibrate", headers={"Authorization": f"Bearer {token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Forbidden"
    print("  PASS")

    # Test 3: admin can calibrate
    print("Test 3: admin can calibrate")
    token = make_token("raj", "admin", timedelta(minutes=5))
    resp = client.post("/calibrate", headers={"Authorization": f"Bearer {token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "calibrated", "by": "raj"}
    print("  PASS")

    # Test 4: admin cannot read sensors (wrong role)
    print("Test 4: admin cannot read sensors (wrong role)")
    resp = client.get("/sensors", headers={"Authorization": f"Bearer {token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Forbidden"
    print("  PASS")

    # Test 5: missing token returns 401
    print("Test 5: missing token returns 401")
    resp = client.get("/sensors")
    print(f"  status={resp.status_code}")
    assert resp.status_code == 401
    print("  PASS")


run_drill_104()

# --- EXPECTED OUTPUT ---
# Test 1: meteorologist can read sensors
#   status=200, body={'data': 'sensor readings', 'reader': 'yuna'}
#   PASS
# Test 2: meteorologist cannot calibrate
#   status=403, body={'detail': 'Forbidden'}
#   PASS
# Test 3: admin can calibrate
#   status=200, body={'status': 'calibrated', 'by': 'raj'}
#   PASS
# Test 4: admin cannot read sensors (wrong role)
#   status=403, body={'detail': 'Forbidden'}
#   PASS
# Test 5: missing token returns 401
#   status=401
#   PASS
