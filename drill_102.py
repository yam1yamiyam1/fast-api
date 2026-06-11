# drill_102.py
# noqa: F401

from datetime import datetime, timedelta, timezone  # noqa: F401

from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
from fastapi.security import OAuth2PasswordBearer  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from jose import JWTError, jwt  # noqa: F401


def run_drill_102():
    """
    SCENARIO: Veterinary Clinic
    The clinic's patient portal issues signed JWT tokens to authenticated
    vets. Every protected request carries a JWT. The server must decode
    and verify the token's signature and expiry before granting access.
    An expired or tampered token must be rejected.

    REQUIREMENTS:
    1. SECRET_KEY: str
       The secret string used to sign and verify all JWTs.
       Value: "clinic-secret".

    2. ALGORITHM: str
       The signing algorithm. Value: "HS256".

    3. make_token(sub: str, expires_delta: timedelta) -> str
       A helper that builds and returns a signed JWT.
       sub: str — the subject claim, representing the vet's identifier.
       expires_delta: timedelta — how long until the token expires,
         representing the token's valid lifetime.
       Sets the "exp" claim to utcnow + expires_delta.
       Encodes with SECRET_KEY and ALGORITHM.

    4. oauth2_scheme: OAuth2PasswordBearer
       Extracts the bearer token from the Authorization header. tokenUrl="/token".

    5. verify_token(token: str) -> dict
       A dependency. token: str — the raw JWT string extracted from the header,
         representing the caller's credential.
       Decodes the token using SECRET_KEY and ALGORITHM.
       If decoding succeeds, returns the payload dict.
       If JWTError is raised (bad signature, expired, malformed),
         raises HTTPException status_code=401, detail="Invalid or expired token".

    6. GET /record
       Protected route. payload: dict — the decoded JWT claims, injected by
         verify_token via Depends, representing the verified vet identity.
       Returns {"sub": payload["sub"]}.
    """

    # --- YOUR CODE HERE ---
    SECRET_KEY: str = "clinic-secret"
    ALGORITHM: str = "HS256"

    def make_token(sub: str, expires_delta: timedelta):
        return jwt.encode(
            {"sub": sub, "exp": datetime.now(timezone.utc) + expires_delta},
            key=SECRET_KEY,
            algorithm=ALGORITHM,
        )

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def verify_token(token: str = Depends(oauth2_scheme)):
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return decoded

    app = FastAPI()

    @app.get("/record")
    def get_record(payload: dict = Depends(verify_token)):
        return {"sub": payload["sub"]}

    client = TestClient(app, raise_server_exceptions=False)

    # Test 1: valid token returns sub claim
    print("Test 1: valid token returns sub claim")
    token = make_token(sub="vet-dr-jones", expires_delta=timedelta(minutes=5))
    resp = client.get("/record", headers={"Authorization": f"Bearer {token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 200
    assert resp.json() == {"sub": "vet-dr-jones"}
    print("  PASS")

    # Test 2: expired token returns 401
    print("Test 2: expired token returns 401")
    expired_token = make_token(sub="vet-dr-jones", expires_delta=timedelta(seconds=-1))
    resp = client.get("/record", headers={"Authorization": f"Bearer {expired_token}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or expired token"
    print("  PASS")

    # Test 3: tampered token returns 401
    print("Test 3: tampered token returns 401")
    resp = client.get("/record", headers={"Authorization": "Bearer not.a.valid.jwt"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or expired token"
    print("  PASS")

    # Test 4: missing token returns 401
    print("Test 4: missing token returns 401")
    resp = client.get("/record")
    print(f"  status={resp.status_code}")
    assert resp.status_code == 401
    print("  PASS")


run_drill_102()

# --- EXPECTED OUTPUT ---
# Test 1: valid token returns sub claim
#   status=200, body={'sub': 'vet-dr-jones'}
#   PASS
# Test 2: expired token returns 401
#   status=401, body={'detail': 'Invalid or expired token'}
#   PASS
# Test 3: tampered token returns 401
#   status=401, body={'detail': 'Invalid or expired token'}
#   PASS
# Test 4: missing token returns 401
#   status=401
#   PASS
