"""
Tests for Insurance Operations API endpoints
Version: 2024-12-19_18-17
"""
import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.tests.utils.utils import random_lower_string
from app.tests.utils.insurance import (
    create_test_insurance_policy,
    create_test_insurance_claim,
    create_test_authorization
)

client = TestClient(app)

# Test Data Setup
@pytest.fixture
def test_policy(db: Session):
    return create_test_insurance_policy(db)

@pytest.fixture
def test_claim(db: Session, test_policy):
    return create_test_insurance_claim(db, test_policy.id)

@pytest.fixture
def test_authorization(db: Session, test_policy):
    return create_test_authorization(db, test_policy.id)

# Eligibility Tests
def test_check_eligibility(db: Session, test_policy):
    """Test eligibility check endpoint."""
    response = client.post(
        "/api/v1/insurance/operations/eligibility/check",
        json={
            "policy_id": test_policy.id,
            "service_date": date.today().isoformat(),
            "service_types": ["OFFICE_VISIT"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_eligible"] is True
    assert "benefits" in data

def test_verify_coverage(db: Session, test_policy):
    """Test coverage verification endpoint."""
    response = client.post(
        "/api/v1/insurance/operations/eligibility/verify-coverage",
        json={
            "policy_id": test_policy.id,
            "service_date": date.today().isoformat(),
            "service_types": ["OFFICE_VISIT"],
            "provider_id": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "coverage_details" in data
    assert "network_status" in data

# Claims Tests
def test_submit_claim(db: Session, test_policy):
    """Test claim submission endpoint."""
    response = client.post(
        "/api/v1/insurance/operations/claims",
        json={
            "policy_id": test_policy.id,
            "service_date": date.today().isoformat(),
            "diagnosis_codes": ["A00.0"],
            "service_lines": [
                {
                    "procedure_code": "99213",
                    "quantity": 1,
                    "charge_amount": 150.00
                }
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "SUBMITTED"
    assert "claim_number" in data

def test_get_claim(db: Session, test_claim):
    """Test get claim details endpoint."""
    response = client.get(f"/api/v1/insurance/operations/claims/{test_claim.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_claim.id
    assert "status" in data

def test_list_claims(db: Session, test_policy, test_claim):
    """Test list claims endpoint."""
    response = client.get(
        "/api/v1/insurance/operations/claims",
        params={"policy_id": test_policy.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["policy_id"] == test_policy.id

def test_update_claim_status(db: Session, test_claim):
    """Test claim status update endpoint."""
    response = client.patch(
        f"/api/v1/insurance/operations/claims/{test_claim.id}/status",
        json={
            "status": "IN_PROCESS",
            "notes": "Processing claim"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_PROCESS"

# Authorization Tests
def test_request_authorization(db: Session, test_policy):
    """Test authorization request endpoint."""
    response = client.post(
        "/api/v1/insurance/operations/authorizations",
        json={
            "policy_id": test_policy.id,
            "service_type": "SURGERY",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
            "diagnosis_codes": ["M54.5"],
            "procedure_codes": ["99213"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert "authorization_number" in data

def test_get_authorization(db: Session, test_authorization):
    """Test get authorization details endpoint."""
    response = client.get(
        f"/api/v1/insurance/operations/authorizations/{test_authorization.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_authorization.id
    assert "status" in data

def test_list_authorizations(db: Session, test_policy, test_authorization):
    """Test list authorizations endpoint."""
    response = client.get(
        "/api/v1/insurance/operations/authorizations",
        params={"policy_id": test_policy.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["policy_id"] == test_policy.id

def test_update_authorization_status(db: Session, test_authorization):
    """Test authorization status update endpoint."""
    response = client.patch(
        f"/api/v1/insurance/operations/authorizations/{test_authorization.id}/status",
        json={
            "status": "APPROVED",
            "notes": "Approved for requested services"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"

def test_check_authorization(db: Session, test_policy, test_authorization):
    """Test authorization check endpoint."""
    response = client.get(
        "/api/v1/insurance/operations/authorizations/check",
        params={
            "policy_id": test_policy.id,
            "service_type": "SURGERY",
            "service_date": date.today().isoformat()
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_authorized" in data

# Verification Tests
def test_verify_insurance(db: Session, test_policy):
    """Test insurance verification endpoint."""
    response = client.post(
        "/api/v1/insurance/operations/verify",
        json={
            "policy_id": test_policy.id,
            "verification_type": "INITIAL",
            "service_types": ["OFFICE_VISIT"],
            "reference_date": date.today().isoformat()
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "policy_verification" in data
    assert "benefits_verification" in data

def test_get_verification_history(db: Session, test_policy):
    """Test verification history endpoint."""
    # First create a verification
    client.post(
        "/api/v1/insurance/operations/verify",
        json={
            "policy_id": test_policy.id,
            "verification_type": "INITIAL",
            "service_types": ["OFFICE_VISIT"]
        }
    )
    
    response = client.get(
        "/api/v1/insurance/operations/verify/history",
        params={"policy_id": test_policy.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["policy_id"] == test_policy.id
