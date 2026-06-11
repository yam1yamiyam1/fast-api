# drill_103.py
# noqa: F401

from datetime import datetime, timedelta, timezone  # noqa: F401

from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
from fastapi.security import OAuth2PasswordBearer  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from jose import JWTError, jwt  # noqa: F401
from pydantic import BaseModel  # noqa: F401


def run_drill_103():
    """
    SCENARIO: Broadcast Studio
    The studio's internal API issues JWTs to authenticated staff. Each JWT
    carries the staff member's username and role. A shared dependency decodes
    the token and returns a fully populated User object — so every protected
    route receives a real user, not a raw token string.

    REQUIREMENTS:
    1. SECRET_KEY: str
       The secret used to sign and verify all JWTs. Value: "studio-secret".

    2. ALGORITHM: str
       The signing algorithm. Value: "HS256".

    3. class User(BaseModel)
       The model representing an authenticated staff member.
       Fields:
         username: str — the staff member's login handle.
         role: str — the staff member's role in the studio (e.g. "editor", "producer").

    4. make_token(username: str, role: str, expires_delta: timedelta) -> str
       Builds and returns a signed JWT.
       username: str — the staff member's login handle, stored as the "sub" claim.
       role: str — the staff member's role, stored as the "role" claim.
       expires_delta: timedelta — how long until the token expires.
       Sets "exp" to utcnow + expires_delta.

    5. oauth2_scheme: OAuth2PasswordBearer
       Extracts the bearer token from the Authorization header. tokenUrl="/token".

    6. get_current_user(token: str) -> User
       A dependency. token: str — the raw JWT string from the Authorization header.
       Decodes the token. Extracts "sub" and "role" from the payload.
       Returns a User built from those values.
       If decoding fails or "sub"/"role" are missing, raises HTTPException
       status_code=401, detail="Invalid token".

    7. GET /me
       Protected route. current_user: User — the authenticated staff member,
       injected by get_current_user via Depends.
       Returns {"username": current_user.username, "role": current_user.role}.
    """

    # --- YOUR CODE HERE ---
    SECRET_KEY: str = "studio-secret"
    ALGORITHM: str = "HS256"

    class User(BaseModel):
        username: str
        role: str

    def make_token(username: str, role: str, expires_delta: timedelta):

        return jwt.encode(
            {
                "sub": username,
                "role": role,
                "exp": datetime.now(timezone.utc) + expires_delta,
            },
            key=SECRET_KEY,
            algorithm=ALGORITHM,
        )

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def get_current_user(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        sub, role = payload["sub"], payload["role"]
        return User(username=sub, role=role)

    app = FastAPI()

    @app.get("/me")
    def get_me(current_user: User = Depends(get_current_user)):
        username, role = current_user.username, current_user.role
        return {"username": username, "role": role}

    client = TestClient(app, raise_server_exceptions=False)

    # Test 1: valid token returns username and role
    print("Test 1: valid token returns username and role")
    token = make_token(
        username="ana", role="editor", expires_delta=timedelta(minutes=5)
    )
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 200
    assert resp.json() == {"username": "ana", "role": "editor"}
    print("  PASS")

    # Test 2: different role is returned correctly
    print("Test 2: different role is returned correctly")
    token = make_token(
        username="marco", role="producer", expires_delta=timedelta(minutes=5)
    )
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 200
    assert resp.json() == {"username": "marco", "role": "producer"}
    print("  PASS")

    # Test 3: expired token returns 401
    print("Test 3: expired token returns 401")
    token = make_token(
        username="ana", role="editor", expires_delta=timedelta(seconds=-1)
    )
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"
    print("  PASS")

    # Test 4: tampered token returns 401
    print("Test 4: tampered token returns 401")
    resp = client.get("/me", headers={"Authorization": "Bearer garbage.token.here"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"
    print("  PASS")

    # Test 5: missing token returns 401
    print("Test 5: missing token returns 401")
    resp = client.get("/me")
    print(f"  status={resp.status_code}")
    assert resp.status_code == 401
    print("  PASS")


run_drill_103()

# --- EXPECTED OUTPUT ---
# Test 1: valid token returns username and role
#   status=200, body={'username': 'ana', 'role': 'editor'}
#   PASS
# Test 2: different role is returned correctly
#   status=200, body={'username': 'marco', 'role': 'producer'}
#   PASS
# Test 3: expired token returns 401
#   status=401, body={'detail': 'Invalid token'}
#   PASS
# Test 4: tampered token returns 401
#   status=401, body={'detail': 'Invalid token'}
#   PASS
# Test 5: missing token returns 401
#   status=401
#   PASS
