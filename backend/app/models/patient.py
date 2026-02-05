"""
Patient model - FHIR Patient resource.
Stores patient demographics, identifiers, and contact information.
"""
from sqlalchemy import Column, String, Date, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.database import Base


class Patient(Base):
    """
    Patient model representing a FHIR Patient resource.
    
    Stores both normalized fields for querying and the complete
    FHIR resource as JSONB for easy serving.
    """
    __tablename__ = "patients"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identifiers
    mrn = Column(String(50), unique=True, nullable=False, index=True, 
                 comment="Medical Record Number - primary identifier")
    ssn_encrypted = Column(String(255), nullable=True,
                          comment="Encrypted SSN for HIPAA compliance")
    
    # Demographics
    family_name = Column(String(100), nullable=False, index=True,
                        comment="Family/last name")
    given_name = Column(String(100), nullable=False, index=True,
                       comment="Given/first name")
    middle_name = Column(String(100), nullable=True,
                        comment="Middle name(s)")
    
    birth_date = Column(Date, nullable=False, index=True,
                       comment="Date of birth")
    gender = Column(String(20), nullable=False,
                   comment="Gender: male, female, other, unknown")
    
    # Contact Information
    phone = Column(String(20), nullable=True,
                  comment="Primary phone number")
    email = Column(String(100), nullable=True,
                  comment="Email address")
    
    # Address
    address_line = Column(String(255), nullable=True,
                         comment="Street address")
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True,
                  comment="State/Province")
    postal_code = Column(String(20), nullable=True)
    country = Column(String(50), nullable=True)
    
    # FHIR Resource Storage
    fhir_resource = Column(JSONB, nullable=False,
                          comment="Complete FHIR Patient resource as JSON")
    
    # Metadata
    version = Column(Integer, default=1, nullable=False, comment="Resource version for optimistic locking")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, 
                       onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Patient(id={self.id}, mrn={self.mrn}, name={self.given_name} {self.family_name})>"