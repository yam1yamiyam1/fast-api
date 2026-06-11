# drill_105.py
# noqa: F401

from datetime import datetime, timedelta, timezone  # noqa: F401

from fastapi import Body, Depends, FastAPI, HTTPException  # noqa: F401
from fastapi.security import OAuth2PasswordBearer  # noqa: F401
from fastapi.testclient import TestClient  # noqa: F401
from jose import JWTError, jwt  # noqa: F401
from pydantic import BaseModel  # noqa: F401


def run_drill_105():
    """
    SCENARIO: Satellite Control Room
    The control room issues short-lived access tokens and long-lived refresh
    tokens. When an access token expires, the client sends the refresh token
    to get a new access token — without logging in again. The server verifies
    the refresh token's type claim before issuing a new access token.

    REQUIREMENTS:
    1. SECRET_KEY: str
       The secret used to sign and verify all JWTs. Value: "satellite-secret".

    2. ALGORITHM: str
       The signing algorithm. Value: "HS256".

    3. make_access_token(username: str) -> str
       Builds a signed JWT for normal API access.
       username: str — the operator's login handle, stored as "sub".
       Sets "type" claim to "access" and "exp" to utcnow + 15 minutes.

    4. make_refresh_token(username: str) -> str
       Builds a signed JWT used only for obtaining new access tokens.
       username: str — the operator's login handle, stored as "sub".
       Sets "type" claim to "refresh" and "exp" to utcnow + 7 days.

    5. oauth2_scheme: OAuth2PasswordBearer
       Extracts the bearer token from the Authorization header. tokenUrl="/token".

    6. get_current_user(token: str) -> str
       A dependency. token: str — the raw JWT from the Authorization header.
       Decodes the token. If "type" claim is not "access", raises HTTPException
       status_code=401, detail="Not an access token".
       If decoding fails, raises HTTPException status_code=401,
       detail="Invalid token".
       Returns the "sub" claim string.

    7. GET /telemetry
       Protected route — requires a valid access token.
       username: str — the verified operator's handle, injected by get_current_user.
       Returns {"feed": "live telemetry", "operator": username}.

    8. POST /refresh
       Accepts a JSON body with one field:
         refresh_token: str — the long-lived token submitted by the client,
           representing the operator's request for a new access token.
       Decodes refresh_token. If "type" claim is not "refresh", raises
       HTTPException status_code=401, detail="Not a refresh token".
       If decoding fails, raises HTTPException status_code=401,
       detail="Invalid token".
       Returns {"access_token": <new access token>, "token_type": "bearer"}.
    """

    # --- YOUR CODE HERE ---
    SECRET_KEY: str = "satellite-secret"
    ALGORITHM: str = "HS256"

    class RefreshRequest(BaseModel):
        refresh_token: str

    def make_access_token(username: str):
        return jwt.encode(
            {
                "sub": username,
                "type": "access",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            },
            SECRET_KEY,
            ALGORITHM,
        )

    def make_refresh_token(username: str):
        return jwt.encode(
            {
                "sub": username,
                "type": "refresh",
                "exp": datetime.now(timezone.utc) + timedelta(days=7),
            },
            SECRET_KEY,
            ALGORITHM,
        )

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

    def get_current_user(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        sub, token_type = payload["sub"], payload["type"]
        if token_type != "access":
            raise HTTPException(status_code=401, detail="Not an access token")
        return sub

    app = FastAPI()

    @app.get("/telemetry")
    def get_telemetry(username: str = Depends(get_current_user)):
        return {"feed": "live telemetry", "operator": username}

    @app.post("/refresh")
    def refresh(body: RefreshRequest):
        try:
            payload = jwt.decode(
                token=body.refresh_token, key=SECRET_KEY, algorithms=[ALGORITHM]
            )
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        sub, token_type = payload["sub"], payload["type"]
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        return {"access_token": make_access_token(sub), "token_type": "bearer"}

    client = TestClient(app, raise_server_exceptions=False)

    # Test 1: valid access token grants telemetry
    print("Test 1: valid access token grants telemetry")
    access = make_access_token("operator-chen")
    resp = client.get("/telemetry", headers={"Authorization": f"Bearer {access}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 200
    assert resp.json() == {"feed": "live telemetry", "operator": "operator-chen"}
    print("  PASS")

    # Test 2: refresh token rejected on /telemetry
    print("Test 2: refresh token rejected on /telemetry")
    refresh = make_refresh_token("operator-chen")
    resp = client.get("/telemetry", headers={"Authorization": f"Bearer {refresh}"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not an access token"
    print("  PASS")

    # Test 3: valid refresh token returns new access token
    print("Test 3: valid refresh token returns new access token")
    resp = client.post("/refresh", json={"refresh_token": refresh})

    print(f"  status={resp.status_code}, body keys={list(resp.json().keys())}")
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    print("  PASS")

    # Test 4: access token rejected on /refresh
    print("Test 4: access token rejected on /refresh")
    resp = client.post("/refresh", json={"refresh_token": access})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not a refresh token"
    print("  PASS")

    # Test 5: tampered refresh token returns 401
    print("Test 5: tampered refresh token returns 401")
    resp = client.post("/refresh", json={"refresh_token": "bad.token.here"})
    print(f"  status={resp.status_code}, body={resp.json()}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"
    print("  PASS")


run_drill_105()

# --- EXPECTED OUTPUT ---
# Test 1: valid access token grants telemetry
#   status=200, body={'feed': 'live telemetry', 'operator': 'operator-chen'}
#   PASS
# Test 2: refresh token rejected on /telemetry
#   status=401, body={'detail': 'Not an access token'}
#   PASS
# Test 3: valid refresh token returns new access token
#   status=200, body keys=['access_token', 'token_type']
#   PASS
# Test 4: access token rejected on /refresh
#   status=401, body={'detail': 'Not a refresh token'}
#   PASS
# Test 5: tampered refresh token returns 401
#   status=401, body={'detail': 'Invalid token'}
#   PASS
