"""
Patient API routes - FHIR R4 Patient resource endpoints.
Implements FHIR REST API for Patient resources.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import date
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.bundle import Bundle, BundleEntry
from pydantic import ValidationError

from app.database import get_db
from app.services.patient_service import PatientService


router = APIRouter()


@router.post("/Patient", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def create_patient(
    patient_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new Patient resource.
    
    Validates the input against FHIR R4 Patient specification
    and stores it in the database.
    
    **FHIR Operation:** CREATE
    """
    try:
        # Validate against FHIR specification
        fhir_patient = FHIRPatient(**patient_data)
        
        # Create in database
        db_patient = await PatientService.create_patient(db, fhir_patient)
        await db.commit()
        
        # Convert back to FHIR for response
        response_patient = PatientService.db_to_fhir(db_patient)
        
        return response_patient.model_dump()
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid FHIR Patient resource: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating patient: {str(e)}"
        )


@router.get("/Patient/{patient_id}", response_model=Dict[str, Any])
async def get_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Read a Patient resource by ID.
    
    **FHIR Operation:** READ
    """
    db_patient = await PatientService.get_patient(db, patient_id)
    
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id {patient_id} not found"
        )
    
    # Convert to FHIR resource
    fhir_patient = PatientService.db_to_fhir(db_patient)
    return fhir_patient.model_dump()


@router.put("/Patient/{patient_id}", response_model=Dict[str, Any])
async def update_patient(
    patient_id: UUID,
    patient_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing Patient resource.
    
    **FHIR Operation:** UPDATE
    """
    try:
        # Validate against FHIR specification
        fhir_patient = FHIRPatient(**patient_data)
        
        # Update in database
        db_patient = await PatientService.update_patient(db, patient_id, fhir_patient)
        
        if not db_patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with id {patient_id} not found"
            )
        
        await db.commit()
        
        # Convert back to FHIR for response
        response_patient = PatientService.db_to_fhir(db_patient)
        return response_patient.model_dump()
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid FHIR Patient resource: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating patient: {str(e)}"
        )


@router.get("/Patient", response_model=Dict[str, Any])
async def search_patients(
    name: Optional[str] = Query(None, description="Search by patient name (family or given)"),
    birthdate: Optional[date] = Query(None, description="Search by birth date (YYYY-MM-DD)"),
    identifier: Optional[str] = Query(None, description="Search by identifier (e.g., MRN)"),
    gender: Optional[str] = Query(None, description="Search by gender (male, female, other, unknown)"),
    _count: int = Query(20, ge=1, le=100, description="Number of results to return"),
    _offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for Patient resources.
    
    Supports FHIR search parameters:
    - name: Search by patient name (partial match)
    - birthdate: Exact birth date match
    - identifier: Search by identifier (MRN)
    - gender: Search by gender
    
    **FHIR Operation:** SEARCH
    
    Returns a FHIR Bundle with matching patients.
    """
    try:
        from fhir.resources.bundle import BundleLink
        
        # Get total count
        total_count = await PatientService.count_patients(
            db,
            name=name,
            birthdate=birthdate,
            identifier=identifier,
            gender=gender
        )
        
        # Search database
        db_patients = await PatientService.search_patients(
            db,
            name=name,
            birthdate=birthdate,
            identifier=identifier,
            gender=gender,
            limit=_count,
            offset=_offset
        )
        
        # Build base URL for links
        base_url = "http://localhost:8000/fhir/Patient"
        params = []
        if name:
            params.append(f"name={name}")
        if birthdate:
            params.append(f"birthdate={birthdate}")
        if identifier:
            params.append(f"identifier={identifier}")
        if gender:
            params.append(f"gender={gender}")
        params.append(f"_count={_count}")
        
        # Build links
        links = []
        
        # Self link
        self_params = params + [f"_offset={_offset}"]
        self_url = f"{base_url}?{'&'.join(self_params)}"
        links.append(BundleLink(relation="self", url=self_url))
        
        # Next link (if more results exist)
        if _offset + _count < total_count:
            next_offset = _offset + _count
            next_params = params + [f"_offset={next_offset}"]
            next_url = f"{base_url}?{'&'.join(next_params)}"
            links.append(BundleLink(relation="next", url=next_url))
        
        # Previous link (if not on first page)
        if _offset > 0:
            prev_offset = max(0, _offset - _count)
            prev_params = params + [f"_offset={prev_offset}"]
            prev_url = f"{base_url}?{'&'.join(prev_params)}"
            links.append(BundleLink(relation="previous", url=prev_url))
        
        # Convert to FHIR Bundle
        entries = []
        for db_patient in db_patients:
            fhir_patient = PatientService.db_to_fhir(db_patient)
            entry = BundleEntry(
                fullUrl=f"http://localhost:8000/fhir/Patient/{db_patient.id}",
                resource=fhir_patient
            )
            entries.append(entry)
        
        # Create Bundle with links
        bundle = Bundle(
            type="searchset",
            total=total_count,
            link=links,
            entry=entries if entries else None
        )
        
        return bundle.model_dump()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching patients: {str(e)}"
        )


@router.delete("/Patient/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a Patient resource.
    
    **FHIR Operation:** DELETE
    """
    db_patient = await PatientService.get_patient(db, patient_id)
    
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id {patient_id} not found"
        )
    
    await db.delete(db_patient)
    await db.commit()
    
    return None