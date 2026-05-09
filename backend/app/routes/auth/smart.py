"""
SMART on FHIR authentication routes.

Implements the SMART App Launch Framework using PKCE (Proof Key for Code Exchange).
No client secret is used — Epic issues public client credentials for patient-facing apps.

Flow:
    1. GET  /auth/login    → generate PKCE, store in Redis, redirect to Epic
    2. GET  /auth/callback → Epic redirects here with auth code
                          → exchange code + verifier for access token
                          → store token in Redis, set session cookie
    3. GET  /auth/session  → frontend polls this to check auth status
    4. POST /auth/logout   → clear session and Redis token
"""
import json
import secrets
import hashlib
import base64
import uuid

import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse

from app.config import settings
from app.services.session_store import SessionStore

router = APIRouter()


def _generate_pkce_pair() -> tuple[str, str]:
    """
    Generate a PKCE code_verifier and code_challenge pair.

    code_verifier: cryptographically random string (64 bytes → 86 char base64url)
    code_challenge: SHA-256 hash of verifier, base64url-encoded (no padding)

    Epic requires S256 challenge method.
    """
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


@router.get("/login")
async def login(request: Request):
    """
    Step 1 — Kick off the SMART on FHIR authorization flow.
    """
    code_verifier, code_challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(32)

    await SessionStore.set(
        f"pkce:{state}",
        json.dumps({"code_verifier": code_verifier}),
        ttl=600,
    )

    params = {
        "response_type": "code",
        "client_id": settings.EPIC_CLIENT_ID,
        "redirect_uri": settings.EPIC_REDIRECT_URI,
        "scope": "openid fhirUser patient/Patient.read patient/Observation.read patient/MedicationRequest.read patient/Condition.read",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "aud": settings.EPIC_FHIR_BASE_URL,
    }

    query = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"{settings.EPIC_AUTH_URL}?{query}"

    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(request: Request, code: str, state: str):
    """
    Step 2 — Epic redirects here after the user authenticates.
    """
    raw = await SessionStore.get(f"pkce:{state}")
    if not raw:
        raise HTTPException(status_code=400, detail="Invalid or expired state. Please try logging in again.")

    await SessionStore.delete(f"pkce:{state}")
    pkce_data = json.loads(raw)
    code_verifier = pkce_data["code_verifier"]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.EPIC_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.EPIC_REDIRECT_URI,
                "client_id": settings.EPIC_CLIENT_ID,
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Token exchange failed: {response.text}"
        )

    token_data = response.json()

    session_id = str(uuid.uuid4())
    expires_in = token_data.get("expires_in", 3600)

    await SessionStore.set(
        f"session:{session_id}",
        json.dumps(token_data),
        ttl=expires_in,
    )

    request.session["session_id"] = session_id

    # JS redirect so Epic's post-auth page doesn't override our redirect
    return HTMLResponse(f"""
        <html>
          <body>
            <script>window.location.replace("{settings.FRONTEND_URL}");</script>
          </body>
        </html>
    """)


@router.get("/session")
async def get_session(request: Request):
    """
    Step 3 — Frontend calls this to check if the user is authenticated.
    """
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    raw = await SessionStore.get(f"session:{session_id}")
    if not raw:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session expired")

    token_data = json.loads(raw)

    return JSONResponse({
        "authenticated": True,
        "patient_id": token_data.get("patient"),
        "expires_in": token_data.get("expires_in"),
    })


@router.post("/logout")
async def logout(request: Request):
    """
    Step 4 — Clear the session from Redis and the cookie.
    """
    session_id = request.session.get("session_id")
    if session_id:
        await SessionStore.delete(f"session:{session_id}")

    request.session.clear()
    return JSONResponse({"message": "Logged out"})