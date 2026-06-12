# =============================================================================
# CONCEPT INTRO — JWT Decode with python-jose
# =============================================================================
#
# WHAT IT SOLVES
# --------------
# In D101 tokens were opaque strings looked up in a dict — the server had to
# store every valid token. JWTs (JSON Web Tokens) are self-contained: the
# server encodes claims into the token and signs it. On the next request it
# only needs to verify the signature and expiry — no lookup table needed.
#
# NEW IMPORTS
# -----------
# from jose import jwt, JWTError
#   └─ jwt        — encodes and decodes JWT tokens
#   └─ JWTError   — raised when decode fails (bad signature, expired, malformed)
#
# Install: pip install python-jose
#
# NEW FUNCTIONS
# -------------
# jwt.encode(claims: dict, key: str, algorithm: str) -> str
#   claims    : dict — payload to embed in the token (e.g. {"sub": "alice"})
#   key       : str  — secret used to sign; must match on decode
#   algorithm : str  — signing algorithm, always use "HS256" for now
#   Returns   : str  — the encoded JWT string
#
# jwt.decode(token: str, key: str, algorithms: list[str]) -> dict
#   token      : str        — the JWT string to verify and decode
#   key        : str        — same secret used during encode
#   algorithms : list[str]  — list of allowed algorithms, e.g. ["HS256"]
#   Returns    : dict       — the decoded claims payload
#   Raises     : JWTError   — if signature is invalid, token is expired,
#                             or token is malformed in any way
#
# EXPIRY
# ------
# Add "exp" to claims with a future UTC timestamp — jose checks it automatically:
#
#   from datetime import datetime, timezone, timedelta
#   exp = datetime.now(timezone.utc) + timedelta(minutes=30)
#   claims = {"sub": "alice", "exp": exp}
#   token = jwt.encode(claims, SECRET, algorithm="HS256")
#
# If exp is in the past, jwt.decode raises JWTError automatically.
#
# PURE PYTHON TRANSLATION
# -----------------------
# Pure Python (D101 — opaque token lookup):  FastAPI + JWT:
# ─────────────────────────────────────────  ──────────────────────────────────
# VALID_TOKENS = {"token-alice": {...}}       no lookup table needed
# user = VALID_TOKENS.get(token)             payload = jwt.decode(token, KEY, [...])
# if not user: raise 401                     except JWTError: raise 401
# return user                                return {"sub": payload["sub"]}
#
# MINIMAL WIRING EXAMPLE
# ----------------------
# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer
# from fastapi.testclient import TestClient
# from jose import jwt, JWTError
# from contextlib import asynccontextmanager
# from datetime import datetime, timezone, timedelta
#
# SECRET = "mysecret"
# APP_STATE = {}
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     APP_STATE["secret"] = SECRET
#     try:
#         yield
#     finally:
#         APP_STATE.clear()
#
# app = FastAPI(lifespan=lifespan)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
#
# def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
#     try:
#         payload = jwt.decode(token, APP_STATE["secret"], algorithms=["HS256"])
#     except JWTError:
#         raise HTTPException(status_code=401, detail="invalid token")
#     return {"username": payload["sub"]}
#
# @app.get("/me")
# def me(user: dict = Depends(get_current_user)):
#     return user
#
# # --- making a valid token for tests ---
# def make_token(username: str, secret: str, minutes: int = 30) -> str:
#     exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
#     return jwt.encode({"sub": username, "exp": exp}, secret, algorithm="HS256")
#
# with TestClient(app) as client:
#     token = make_token("alice", SECRET)
#     r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
#     # → 200, {"username": "alice"}
# =============================================================================


def run_drill_102():
    # =========================================================================
    # SCENARIO: Veterinary Clinic
    #
    # A veterinary clinic API lets authenticated vets look up patient animal
    # records. Authentication uses JWTs — each vet receives a signed token
    # encoding their username. The token must be verified on every request.
    # Animal records are stored in-memory and looked up by animal ID.
    #
    # REQUIREMENTS
    # ------------
    # 1. SECRET_KEY: str
    #       The HS256 signing secret used to sign and verify all JWTs.
    #       Value: "clinic-secret-key"
    #
    # 2. APP_STATE: dict
    #       Module-level shared state dict, starts empty.
    #       Lifespan loads "secret" into it at startup and clears at shutdown.
    #
    # 3. ANIMALS: dict[int, dict]
    #       In-memory map from animal ID (int) to animal record dict.
    #       Represents the clinic's patient registry.
    #       Pre-populate with:
    #         1: {"id": 1, "name": "Rex",   "species": "dog",  "owner": "alice", "internal_notes": "aggressive"}
    #         2: {"id": 2, "name": "Whiskers", "species": "cat", "owner": "bob", "internal_notes": "diabetic"}
    #         3: {"id": 3, "name": "Tweety", "species": "bird", "owner": "alice", "internal_notes": "wing injury"}
    #
    # 4. AnimalOut: BaseModel
    #       Response schema for a single animal record.
    #       Fields: id: int, name: str, species: str, owner: str
    #       (internal_notes intentionally excluded)
    #
    # 5. lifespan: asynccontextmanager
    #       Startup: loads APP_STATE["secret"] = SECRET_KEY
    #       Shutdown: clears APP_STATE
    #       Passed to FastAPI(lifespan=lifespan)
    #
    # 6. oauth2_scheme: OAuth2PasswordBearer
    #       Extracts bearer token from Authorization header.
    #       tokenUrl should be "/token"
    #
    # 7. make_token(username: str, secret: str, minutes: int) -> str
    #       username : str — the vet's username to embed as the "sub" claim,
    #                        representing who the token belongs to.
    #       secret   : str — the signing key used to sign the token.
    #       minutes  : int — how many minutes from now until expiry,
    #                        representing the token's validity window.
    #       Encodes {"sub": username, "exp": <utc now + minutes>} using HS256.
    #       Returns the encoded JWT string.
    #
    # 8. get_current_vet(token: str) -> dict
    #       token: str — the raw bearer token from the Authorization header,
    #                    representing the caller's JWT credential.
    #       Must declare: token: str = Depends(oauth2_scheme)
    #       Decodes token using APP_STATE["secret"] and algorithms=["HS256"].
    #       Raises HTTPException(401, detail="invalid token") on JWTError.
    #       Returns {"username": payload["sub"]}
    #
    # 9. GET /animals
    #       Query param: owner: Optional[str] = None — a filter string
    #           representing the owner's name to narrow results.
    #           When None, all animals are returned.
    #       Protected by: Depends(get_current_vet)
    #       response_model: list[AnimalOut]
    #       Returns all animals matching owner filter (or all if None).
    #       internal_notes must be stripped from every response item.
    #
    # 10. GET /animals/{animal_id}
    #       animal_id: int — the numeric identifier of a specific animal
    #                        in the clinic's patient registry.
    #       Protected by: Depends(get_current_vet)
    #       response_model: AnimalOut
    #       Raises HTTPException(404, detail="animal not found") if not found.
    #       Returns the matching animal. internal_notes must be stripped.
    # =========================================================================

    from contextlib import asynccontextmanager  # noqa: F401
    from datetime import datetime, timedelta, timezone  # noqa: F401
    from typing import Optional  # noqa: F401

    from fastapi import Depends, FastAPI, HTTPException  # noqa: F401
    from fastapi.security import OAuth2PasswordBearer  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401
    from jose import JWTError, jwt  # noqa: F401
    from pydantic import BaseModel  # noqa: F401

    # --- YOUR CODE HERE ---

    # ── Tests ─────────────────────────────────────────────────────────────────

    with TestClient(app) as client:

        valid_token = make_token("dr-smith", SECRET_KEY, minutes=30)
        auth = {"Authorization": f"Bearer {valid_token}"}

        # Test 1: valid token — list all animals
        print("Test 1: valid token returns all animals")
        r = client.get("/animals", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        assert all("internal_notes" not in a for a in data)
        print(f"  animals returned: {len(data)}, internal_notes stripped: {all('internal_notes' not in a for a in data)}")
        print("  PASS")

        # Test 2: filter by owner
        print("Test 2: owner filter returns matching animals only")
        r = client.get("/animals?owner=alice", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert all(a["owner"] == "alice" for a in data)
        print(f"  alice's animals: {len(data)}")
        print("  PASS")

        # Test 3: get animal by ID
        print("Test 3: valid token fetches animal by ID")
        r = client.get("/animals/2", headers=auth)
        assert r.status_code == 200
        animal = r.json()
        assert animal["id"] == 2
        assert animal["name"] == "Whiskers"
        assert "internal_notes" not in animal
        print(f"  id: {animal['id']}, name: {animal['name']}, internal_notes present: {'internal_notes' in animal}")
        print("  PASS")

        # Test 4: missing token → 401
        print("Test 4: missing token → 401")
        r = client.get("/animals")
        assert r.status_code == 401
        print(f"  status: {r.status_code}")
        print("  PASS")

        # Test 5: bad signature → 401
        print("Test 5: token signed with wrong key → 401")
        bad_token = make_token("dr-smith", "wrong-secret", minutes=30)
        r = client.get("/animals", headers={"Authorization": f"Bearer {bad_token}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 6: expired token → 401
        print("Test 6: expired token → 401")
        expired_token = make_token("dr-smith", SECRET_KEY, minutes=-1)
        r = client.get("/animals", headers={"Authorization": f"Bearer {expired_token}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "invalid token"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 7: animal not found → 404
        print("Test 7: unknown animal_id → 404")
        r = client.get("/animals/999", headers=auth)
        assert r.status_code == 404
        assert r.json()["detail"] == "animal not found"
        print(f"  status: {r.status_code}, detail: {r.json()['detail']}")
        print("  PASS")

        # Test 8: secret loaded into APP_STATE during lifespan
        print("Test 8: APP_STATE has secret during request lifecycle")
        assert APP_STATE.get("secret") == SECRET_KEY
        print(f"  secret present: {APP_STATE.get('secret') == SECRET_KEY}")
        print("  PASS")


run_drill_102()

# =============================================================================
# EXPECTED OUTPUT
# =============================================================================
# Test 1: valid token returns all animals
#   animals returned: 3, internal_notes stripped: True
#   PASS
# Test 2: owner filter returns matching animals only
#   alice's animals: 2
#   PASS
# Test 3: valid token fetches animal by ID
#   id: 2, name: Whiskers, internal_notes present: False
#   PASS
# Test 4: missing token → 401
#   status: 401
#   PASS
# Test 5: token signed with wrong key → 401
#   status: 401, detail: invalid token
#   PASS
# Test 6: expired token → 401
#   status: 401, detail: invalid token
#   PASS
# Test 7: unknown animal_id → 404
#   status: 404, detail: animal not found
#   PASS
# Test 8: APP_STATE has secret during request lifecycle
#   secret present: True
#   PASS
# =============================================================================
