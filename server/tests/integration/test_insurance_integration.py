"""
Integration Tests for Insurance System
Version: 2024-12-19_18-36

These tests verify the integration between different components
of the insurance system and external services.
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.services.insurance_eligibility import InsuranceEligibilityService
from app.services.insurance_claim import InsuranceClaimService
from app.services.insurance_authorization import InsuranceAuthorizationService
from app.services.insurance_verification import InsuranceVerificationService
from app.tests.utils.insurance import (
    create_test_insurance_policy,
    create_test_insurance_claim,
    create_test_authorization
)

client = TestClient(app)

# Mock External Services
@pytest.fixture
def mock_external_eligibility_service():
    """Mock for external eligibility verification service."""
    with patch("app.services.external.eligibility.ExternalEligibilityService") as mock:
        mock.return_value.verify_eligibility.return_value = {
            "is_eligible": True,
            "coverage_details": {
                "plan_type": "PPO",
                "network_status": "IN_NETWORK",
                "benefits": {
                    "deductible": 1000.00,
                    "deductible_met": 500.00,
                    "out_of_pocket_max": 5000.00,
                    "out_of_pocket_met": 1000.00
                }
            }
        }
        yield mock

@pytest.fixture
def mock_external_claim_service():
    """Mock for external claim processing service."""
    with patch("app.services.external.claims.ExternalClaimService") as mock:
        mock.return_value.submit_claim.return_value = {
            "claim_id": "EXT-12345",
            "status": "RECEIVED",
            "acknowledgement": {
                "timestamp": datetime.now().isoformat(),
                "tracking_number": "TRK-67890"
            }
        }
        yield mock

@pytest.fixture
def mock_external_authorization_service():
    """Mock for external authorization service."""
    with patch("app.services.external.authorization.ExternalAuthorizationService") as mock:
        mock.return_value.request_authorization.return_value = {
            "authorization_number": "AUTH-12345",
            "status": "APPROVED",
            "valid_from": date.today().isoformat(),
            "valid_to": (date.today() + timedelta(days=30)).isoformat(),
            "approved_services": ["99213"]
        }
        yield mock

# Integration Tests

def test_full_eligibility_workflow(
    db: Session,
    test_policy,
    mock_external_eligibility_service
):
    """Test complete eligibility verification workflow."""
    # 1. Check eligibility
    response = client.post(
        "/api/v1/insurance/operations/eligibility/check",
        json={
            "policy_id": test_policy.id,
            "service_date": date.today().isoformat(),
            "service_types": ["OFFICE_VISIT"]
        }
    )
    assert response.status_code == 200
    eligibility_data = response.json()
    
    # 2. Verify coverage details
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
    coverage_data = response.json()
    
    # 3. Verify external service calls
    mock_external_eligibility_service.return_value.verify_eligibility.assert_called()
    
    # 4. Verify data consistency
    assert eligibility_data["is_eligible"] == True
    assert "benefits" in coverage_data
    assert coverage_data["network_status"] == "IN_NETWORK"

def test_full_claim_workflow(
    db: Session,
    test_policy,
    mock_external_claim_service
):
    """Test complete claim submission and processing workflow."""
    # 1. Submit claim
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
    claim_data = response.json()
    claim_id = claim_data["id"]
    
    # 2. Check claim status
    response = client.get(f"/api/v1/insurance/operations/claims/{claim_id}")
    assert response.status_code == 200
    
    # 3. Update claim status
    response = client.patch(
        f"/api/v1/insurance/operations/claims/{claim_id}/status",
        json={
            "status": "IN_PROCESS",
            "notes": "Processing claim"
        }
    )
    assert response.status_code == 200
    
    # 4. Verify external service calls
    mock_external_claim_service.return_value.submit_claim.assert_called()
    
    # 5. Verify data consistency
    assert "claim_number" in claim_data
    assert claim_data["status"] in ["SUBMITTED", "IN_PROCESS"]

def test_full_authorization_workflow(
    db: Session,
    test_policy,
    mock_external_authorization_service
):
    """Test complete authorization request and processing workflow."""
    # 1. Submit authorization request
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
    auth_data = response.json()
    auth_id = auth_data["id"]
    
    # 2. Check authorization status
    response = client.get(f"/api/v1/insurance/operations/authorizations/{auth_id}")
    assert response.status_code == 200
    
    # 3. Update authorization status
    response = client.patch(
        f"/api/v1/insurance/operations/authorizations/{auth_id}/status",
        json={
            "status": "APPROVED",
            "notes": "Approved for requested services"
        }
    )
    assert response.status_code == 200
    
    # 4. Verify service authorization
    response = client.get(
        "/api/v1/insurance/operations/authorizations/check",
        params={
            "policy_id": test_policy.id,
            "service_type": "SURGERY",
            "service_date": date.today().isoformat()
        }
    )
    assert response.status_code == 200
    
    # 5. Verify external service calls
    mock_external_authorization_service.return_value.request_authorization.assert_called()
    
    # 6. Verify data consistency
    assert "authorization_number" in auth_data
    assert auth_data["status"] in ["PENDING", "APPROVED"]

def test_full_verification_workflow(
    db: Session,
    test_policy,
    mock_external_eligibility_service
):
    """Test complete insurance verification workflow."""
    # 1. Perform verification
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
    verification_data = response.json()
    
    # 2. Check verification history
    response = client.get(
        "/api/v1/insurance/operations/verify/history",
        params={"policy_id": test_policy.id}
    )
    assert response.status_code == 200
    history_data = response.json()
    
    # 3. Verify external service calls
    mock_external_eligibility_service.return_value.verify_eligibility.assert_called()
    
    # 4. Verify data consistency
    assert "policy_verification" in verification_data
    assert "benefits_verification" in verification_data
    assert len(history_data) > 0
    assert history_data[0]["policy_id"] == test_policy.id

def test_error_handling(
    db: Session,
    test_policy,
    mock_external_eligibility_service
):
    """Test error handling in integration scenarios."""
    # 1. Test invalid policy ID
    response = client.post(
        "/api/v1/insurance/operations/eligibility/check",
        json={
            "policy_id": 99999,  # Non-existent policy
            "service_date": date.today().isoformat(),
            "service_types": ["OFFICE_VISIT"]
        }
    )
    assert response.status_code == 404
    
    # 2. Test invalid service type
    response = client.post(
        "/api/v1/insurance/operations/eligibility/check",
        json={
            "policy_id": test_policy.id,
            "service_date": date.today().isoformat(),
            "service_types": ["INVALID_SERVICE"]
        }
    )
    assert response.status_code == 400
    
    # 3. Test external service failure
    mock_external_eligibility_service.return_value.verify_eligibility.side_effect = Exception("External service error")
    response = client.post(
        "/api/v1/insurance/operations/eligibility/check",
        json={
            "policy_id": test_policy.id,
            "service_date": date.today().isoformat(),
            "service_types": ["OFFICE_VISIT"]
        }
    )
    assert response.status_code == 500

def test_concurrent_operations(
    db: Session,
    test_policy,
    mock_external_claim_service
):
    """Test handling of concurrent operations."""
    import asyncio
    import concurrent.futures
    
    async def submit_claims(num_claims):
        tasks = []
        for _ in range(num_claims):
            tasks.append(
                client.post(
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
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            loop = asyncio.get_event_loop()
            responses = await asyncio.gather(*tasks)
            return responses
    
    # Submit multiple claims concurrently
    responses = asyncio.run(submit_claims(3))
    
    # Verify all claims were processed
    assert all(r.status_code == 201 for r in responses)
    assert len(set(r.json()["id"] for r in responses)) == 3  # All claims have unique IDs
