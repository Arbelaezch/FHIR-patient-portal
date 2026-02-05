"""
Metadata endpoint - FHIR CapabilityStatement.
Describes what this FHIR server supports.
"""
from fastapi import APIRouter
from typing import Dict, Any
from fhir.resources.capabilitystatement import (
    CapabilityStatement,
    CapabilityStatementRest,
    CapabilityStatementRestResource,
    CapabilityStatementRestResourceOperation,
    CapabilityStatementRestResourceSearchParam
)
from datetime import datetime, timezone

router = APIRouter()


@router.get("/metadata", response_model=Dict[str, Any])
async def get_capability_statement():
    """
    Return FHIR CapabilityStatement describing server capabilities.
    
    **FHIR Operation:** capabilities
    """
    
    # Define Patient resource capabilities
    patient_resource = CapabilityStatementRestResource(
        type="Patient",
        profile="http://hl7.org/fhir/StructureDefinition/Patient",
        interaction=[
            {"code": "read"},
            {"code": "create"},
            {"code": "update"},
            {"code": "delete"},
            {"code": "search-type"}
        ],
        searchParam=[
            CapabilityStatementRestResourceSearchParam(
                name="name",
                type="string",
                documentation="Search by patient name (family or given)"
            ),
            CapabilityStatementRestResourceSearchParam(
                name="birthdate",
                type="date",
                documentation="Search by birth date"
            ),
            CapabilityStatementRestResourceSearchParam(
                name="gender",
                type="token",
                documentation="Search by gender"
            ),
            CapabilityStatementRestResourceSearchParam(
                name="identifier",
                type="token",
                documentation="Search by identifier (e.g., MRN)"
            ),
            CapabilityStatementRestResourceSearchParam(
                name="_count",
                type="number",
                documentation="Number of results per page"
            ),
            CapabilityStatementRestResourceSearchParam(
                name="_offset",
                type="number",
                documentation="Pagination offset"
            )
        ]
    )
    
    # Build REST configuration
    rest = CapabilityStatementRest(
        mode="server",
        resource=[patient_resource]
    )
    
    # Create CapabilityStatement
    capability = CapabilityStatement(
        status="active",
        date=datetime.now(timezone.utc),
        kind="instance",
        fhirVersion="4.0.1",
        format=["application/fhir+json"],
        rest=[rest],
        software={
            "name": "FHIR Patient Portal",
            "version": "1.0.0"
        },
        implementation={
            "description": "A FHIR R4-compliant patient portal API",
            "url": "http://localhost:8000/fhir"
        }
    )
    
    return capability.model_dump()