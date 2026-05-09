"""
FHIR resource proxy.

Forwards requests to Epic's FHIR R4 API on behalf of the authenticated user.
The Epic access token never leaves the server — it is retrieved from Redis
using the session cookie and injected into the upstream request.

Endpoints mirror the FHIR REST pattern but are proxied through our backend:
    GET /fhir/Patient/{patient_id}
    GET /fhir/Observation
    GET /fhir/MedicationRequest
    GET /fhir/Condition
"""
import json

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.session_store import SessionStore

router = APIRouter()


async def get_epic_token(request: Request) -> tuple[str, str]:
    """
    Dependency — retrieves the Epic access token and patient ID from Redis.

    Raises 401 if the session cookie is missing or the Redis entry has expired.
    Both values are needed by every proxy endpoint so we return them together.
    """
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    raw = await SessionStore.get(f"session:{session_id}")
    if not raw:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session expired")

    token_data = json.loads(raw)
    access_token = token_data.get("access_token")
    patient_id = token_data.get("patient")

    if not access_token or not patient_id:
        raise HTTPException(status_code=502, detail="Incomplete token data in session")

    return access_token, patient_id


async def _epic_get(path: str, access_token: str, params: dict = None) -> dict:
    # url = f"{settings.EPIC_FHIR_BASE_URL}/{path}"
    url = f"{settings.EPIC_FHIR_API_URL}/{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/fhir+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)

    # Temporary debug logging
    print(f"Epic {path}: {response.status_code}")
    print(f"Epic {path} response: {response.text[:1000]}")

    if response.status_code == 403:
        # Patient doesn't have this resource type — return empty bundle
        return {"resourceType": "Bundle", "total": 0, "entry": []}

    if not response.is_success:
        raise HTTPException(
            status_code=502,
            detail=f"Epic FHIR error {response.status_code}: {response.text}",
        )

    return response.json()


@router.get("/Patient/{patient_id}")
async def get_patient(
    patient_id: str,
    token_and_patient: tuple[str, str] = Depends(get_epic_token),
):
    """
    Fetch a single Patient resource from Epic.

    The patient_id in the URL should match the one returned by the
    auth flow (stored in the session as token_data["patient"]).
    """
    access_token, _ = token_and_patient
    data = await _epic_get(f"Patient/{patient_id}", access_token)
    return JSONResponse(data)


@router.get("/Observation")
async def get_observations(
    token_and_patient: tuple[str, str] = Depends(get_epic_token),
):
    """
    Fetch Observation resources for the authenticated patient.

    Searches by patient ID and sorts by date descending so the most
    recent vitals and labs appear first.
    """
    access_token, patient_id = token_and_patient
    data = await _epic_get(
        "Observation",
        access_token,
        params={
            "patient": patient_id,
            "_sort": "-date",
            "_count": "50",
        },
    )
    return JSONResponse(data)


@router.get("/MedicationRequest")
async def get_medication_requests(
    token_and_patient: tuple[str, str] = Depends(get_epic_token),
):
    """
    Fetch active MedicationRequest resources for the authenticated patient.
    """
    access_token, patient_id = token_and_patient
    data = await _epic_get(
        "MedicationRequest",
        access_token,
        params={
            "patient": patient_id,
            "status": "active",
        },
    )
    return JSONResponse(data)


@router.get("/Condition")
async def get_conditions(
    token_and_patient: tuple[str, str] = Depends(get_epic_token),
):
    """
    Fetch Condition resources for the authenticated patient.
    """
    access_token, patient_id = token_and_patient
    data = await _epic_get(
        "Condition",
        access_token,
        params={
            "patient": patient_id,
            "clinical-status": "active",
        },
    )
    return JSONResponse(data)