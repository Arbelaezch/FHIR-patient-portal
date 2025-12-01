# FHIR Patient Portal

A patient portal web application implementing FHIR R4 (Fast Healthcare Interoperability Resources) standard. Demonstrates both server-side FHIR API implementation and client-side integration with external FHIR servers via SMART on FHIR authentication.

## 🎯 Project Overview

This project showcases:
- **FHIR R4 Server**: Building FHIR-compliant APIs for Patient, Observation, Medication, and Condition resources
- **FHIR Client**: Consuming external FHIR APIs using SMART on FHIR OAuth2
- **Healthcare Standards**: Implementation of LOINC, RxNorm, and ICD-10 coding systems
- **Modern Stack**: FastAPI, PostgreSQL, async SQLAlchemy, Docker

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16 with asyncpg
- **FHIR**: fhir.resources (R4)
- **ORM**: SQLAlchemy 2.0 (async)
- **Container**: Docker & Docker Compose

### Project Structure
```
FHIR-patient-portal/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routes/              # API endpoints
│   │   │   └── fhir/           # FHIR resources
│   │   ├── services/           # Business logic
│   │   └── utils/              # Utilities
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Tests (pytest)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                   # (To be built)
├── docker-compose.yml
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd FHIR-patient-portal
   ```

2. **Set up environment variables**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   # From the root directory
   docker-compose up --build
   ```

   This will:
   - Start PostgreSQL on port 5432
   - Start FastAPI on port 8000
   - Initialize the database

4. **Access the API**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Development

**Run in development mode (with hot reload):**
```bash
docker-compose up
```

**View logs:**
```bash
docker-compose logs -f backend
```

**Stop the application:**
```bash
docker-compose down
```

**Reset database:**
```bash
docker-compose down -v  # Remove volumes
docker-compose up --build
```

## 📚 API Documentation

### Health Check
```bash
curl http://localhost:8000/health
```

### FHIR Resources (Coming Soon)
- `POST /fhir/Patient` - Create patient
- `GET /fhir/Patient/{id}` - Get patient
- `GET /fhir/Patient?name={name}` - Search patients
- And more...

## 🧪 Testing

```bash
# Run tests (pytest - to be configured)
docker-compose exec backend pytest
```

## 📖 FHIR Resources

### Implemented
- ⏳ Patient
- ⏳ Observation
- ⏳ MedicationRequest
- ⏳ Condition

### Standards
- **FHIR Version**: R4
- **Terminologies**: 
  - LOINC (observations)
  - RxNorm (medications)
  - ICD-10 (conditions)
  - SNOMED CT (clinical findings)

## 🔐 Authentication

- Local authentication with JWT
- SMART on FHIR OAuth2 (for external EHR integration)
