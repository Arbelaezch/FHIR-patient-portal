"""
Patient service - Business logic for Patient resource.
Handles conversion between FHIR resources and database models.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.address import Address
from fhir.resources.identifier import Identifier
from fhir.resources.meta import Meta
from datetime import date

from app.models.patient import Patient as DBPatient


class PatientService:
    """Service for Patient resource operations."""
    
    @staticmethod
    def fhir_to_db(fhir_patient: FHIRPatient, patient_id: Optional[UUID] = None) -> DBPatient:
        """
        Convert FHIR Patient resource to database model.
        
        Args:
            fhir_patient: FHIR Patient resource (validated)
            patient_id: Optional existing patient ID for updates
            
        Returns:
            DBPatient: Database model instance
        """
        # Extract name (use first official or first name in list)
        name = None
        if fhir_patient.name:
            # Try to find official name, otherwise use first
            for n in fhir_patient.name:
                if n.use == "official":
                    name = n
                    break
            if not name:
                name = fhir_patient.name[0]
        
        family_name = name.family if name and name.family else ""
        given_name = name.given[0] if name and name.given else ""
        middle_name = name.given[1] if name and name.given and len(name.given) > 1 else None
        
        # Extract MRN from identifiers
        mrn = None
        if fhir_patient.identifier:
            for identifier in fhir_patient.identifier:
                # Look for MRN identifier (you can customize this logic)
                if identifier.value:
                    mrn = identifier.value
                    break
        
        # Extract contact info
        phone = None
        email = None
        if fhir_patient.telecom:
            for telecom in fhir_patient.telecom:
                if telecom.system == "phone" and not phone:
                    phone = telecom.value
                elif telecom.system == "email" and not email:
                    email = telecom.value
        
        # Extract address
        address_line = None
        city = None
        state = None
        postal_code = None
        country = None
        if fhir_patient.address:
            addr = fhir_patient.address[0]  # Use first address
            if addr.line:
                address_line = ", ".join(addr.line)
            city = addr.city
            state = addr.state
            postal_code = addr.postalCode
            country = addr.country
        
        # Create database model
        db_patient = DBPatient(
            id=patient_id,  # Will be generated if None
            mrn=mrn or f"MRN-{UUID}",  # Generate if not provided
            family_name=family_name,
            given_name=given_name,
            middle_name=middle_name,
            birth_date=fhir_patient.birthDate,
            gender=fhir_patient.gender or "unknown",
            phone=phone,
            email=email,
            address_line=address_line,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            fhir_resource=fhir_patient.model_dump(mode='json')  # Use model_dump() instead of dict()
        )
        
        return db_patient
    
    @staticmethod
    def db_to_fhir(db_patient: DBPatient) -> FHIRPatient:
        """
        Convert database model to FHIR Patient resource.
        
        Args:
            db_patient: Database model instance
            
        Returns:
            FHIRPatient: FHIR Patient resource
        """
        # Start with stored FHIR resource if available
        if db_patient.fhir_resource:
            fhir_patient = FHIRPatient(**db_patient.fhir_resource)
            # Update ID to match database ID
            fhir_patient.id = str(db_patient.id)
            # Add/update meta element
            fhir_patient.meta = Meta(
                versionId=str(db_patient.version),
                lastUpdated=db_patient.updated_at.isoformat() + "Z"
            )
            return fhir_patient
        
        # Otherwise construct from database fields
        # Build name
        name = HumanName(
            use="official",
            family=db_patient.family_name,
            given=[db_patient.given_name]
        )
        if db_patient.middle_name:
            name.given.append(db_patient.middle_name)
        
        # Build identifiers
        identifiers = [
            Identifier(
                system="http://hospital.example.com/mrn",
                value=db_patient.mrn
            )
        ]
        
        # Build telecom
        telecom = []
        if db_patient.phone:
            telecom.append(ContactPoint(
                system="phone",
                value=db_patient.phone,
                use="mobile"
            ))
        if db_patient.email:
            telecom.append(ContactPoint(
                system="email",
                value=db_patient.email
            ))
        
        # Build address
        addresses = []
        if db_patient.address_line or db_patient.city:
            addr = Address(
                use="home",
                line=[db_patient.address_line] if db_patient.address_line else None,
                city=db_patient.city,
                state=db_patient.state,
                postalCode=db_patient.postal_code,
                country=db_patient.country
            )
            addresses.append(addr)
        
        # Create FHIR Patient
        fhir_patient = FHIRPatient(
            id=str(db_patient.id),
            meta=Meta(
                versionId=str(db_patient.version),
                lastUpdated=db_patient.updated_at.isoformat() + "Z"  # ISO 8601 format with Z for UTC
            ),
            identifier=identifiers,
            name=[name],
            gender=db_patient.gender,
            birthDate=db_patient.birth_date,
            telecom=telecom if telecom else None,
            address=addresses if addresses else None
        )
        
        return fhir_patient
    
    @staticmethod
    async def create_patient(db: AsyncSession, fhir_patient: FHIRPatient) -> DBPatient:
        """
        Create a new patient.
        
        Args:
            db: Database session
            fhir_patient: FHIR Patient resource
            
        Returns:
            DBPatient: Created patient
        """
        db_patient = PatientService.fhir_to_db(fhir_patient)
        db.add(db_patient)
        await db.flush()  # Get the ID without committing
        return db_patient
    
    @staticmethod
    async def get_patient(db: AsyncSession, patient_id: UUID) -> Optional[DBPatient]:
        """
        Get patient by ID.
        
        Args:
            db: Database session
            patient_id: Patient UUID
            
        Returns:
            DBPatient or None
        """
        result = await db.execute(
            select(DBPatient).where(DBPatient.id == patient_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_patient(
        db: AsyncSession, 
        patient_id: UUID, 
        fhir_patient: FHIRPatient
    ) -> Optional[DBPatient]:
        """
        Update existing patient.
        
        Args:
            db: Database session
            patient_id: Patient UUID
            fhir_patient: Updated FHIR Patient resource
            
        Returns:
            DBPatient or None if not found
        """
        db_patient = await PatientService.get_patient(db, patient_id)
        if not db_patient:
            return None
        
        # Update fields from FHIR resource
        updated = PatientService.fhir_to_db(fhir_patient, patient_id)
        
        # Copy all fields except id and created_at
        db_patient.mrn = updated.mrn
        db_patient.family_name = updated.family_name
        db_patient.given_name = updated.given_name
        db_patient.middle_name = updated.middle_name
        db_patient.birth_date = updated.birth_date
        db_patient.gender = updated.gender
        db_patient.phone = updated.phone
        db_patient.email = updated.email
        db_patient.address_line = updated.address_line
        db_patient.city = updated.city
        db_patient.state = updated.state
        db_patient.postal_code = updated.postal_code
        db_patient.country = updated.country
        db_patient.fhir_resource = updated.fhir_resource
        db_patient.version = db_patient.version + 1  # Increment version on update
        
        await db.flush()
        return db_patient
    
    @staticmethod
    async def search_patients(
        db: AsyncSession,
        name: Optional[str] = None,
        birthdate: Optional[date] = None,
        identifier: Optional[str] = None,
        gender: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[DBPatient]:
        """
        Search for patients using FHIR search parameters.
        
        Args:
            db: Database session
            name: Search by name (family or given)
            birthdate: Search by birth date
            identifier: Search by identifier (MRN)
            gender: Search by gender
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            List of DBPatient
        """
        query = select(DBPatient)
        
        # Apply filters
        if name:
            # Case-insensitive search on both family and given names
            search_pattern = f"%{name.lower()}%"
            query = query.where(
                or_(
                    DBPatient.family_name.ilike(search_pattern),
                    DBPatient.given_name.ilike(search_pattern)
                )
            )
        
        if birthdate:
            query = query.where(DBPatient.birth_date == birthdate)
        
        if identifier:
            # Handle system|value format or just value
            if "|" in identifier:
                _, value = identifier.split("|", 1)
            else:
                value = identifier
            query = query.where(DBPatient.mrn == value)
        
        if gender:
            query = query.where(DBPatient.gender == gender.lower())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count_patients(
        db: AsyncSession,
        name: Optional[str] = None,
        birthdate: Optional[date] = None,
        identifier: Optional[str] = None,
        gender: Optional[str] = None
    ) -> int:
        """
        Count patients matching search criteria.
        
        Returns:
            Total count of matching patients
        """
        from sqlalchemy import func, select as sql_select
        
        query = sql_select(func.count(DBPatient.id))
        
        # Apply same filters as search_patients
        if name:
            search_pattern = f"%{name.lower()}%"
            query = query.where(
                or_(
                    DBPatient.family_name.ilike(search_pattern),
                    DBPatient.given_name.ilike(search_pattern)
                )
            )
        
        if birthdate:
            query = query.where(DBPatient.birth_date == birthdate)
        
        if identifier:
            if "|" in identifier:
                _, value = identifier.split("|", 1)
            else:
                value = identifier
            query = query.where(DBPatient.mrn == value)
        
        if gender:
            query = query.where(DBPatient.gender == gender.lower())
        
        result = await db.execute(query)
        return result.scalar()