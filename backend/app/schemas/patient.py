"""
Pydantic schemas for Patient resource.
Handles request/response validation and serialization.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class PatientBase(BaseModel):
    """Base schema with common patient fields"""
    mrn: str = Field(..., min_length=1, max_length=50, description="Medical Record Number")
    family_name: str = Field(..., min_length=1, max_length=100)
    given_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    birth_date: date
    gender: str = Field(..., description="Gender: male, female, other, unknown")
    
    # Contact info (all optional)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    
    # Address (all optional)
    address_line: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=50)
    
    @validator('gender')
    def validate_gender(cls, v):
        allowed = ['male', 'female', 'other', 'unknown']
        if v.lower() not in allowed:
            raise ValueError(f'Gender must be one of: {", ".join(allowed)}')
        return v.lower()


class PatientCreate(PatientBase):
    """Schema for creating a new patient"""
    ssn_encrypted: Optional[str] = Field(None, max_length=255)


class PatientUpdate(BaseModel):
    """Schema for updating a patient - all fields optional"""
    family_name: Optional[str] = Field(None, max_length=100)
    given_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address_line: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=50)


class PatientResponse(PatientBase):
    """Schema for patient responses"""
    id: UUID
    fhir_resource: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Allows creation from SQLAlchemy models


class PatientList(BaseModel):
    """Schema for paginated patient list responses"""
    total: int
    patients: list[PatientResponse]
    page: int = 1
    page_size: int = 20