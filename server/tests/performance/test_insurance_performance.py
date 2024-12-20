"""
Performance Tests for Insurance System
Version: 2024-12-19_18-36

These tests verify the performance characteristics of the insurance system
under various load conditions.
"""
import pytest
import time
import asyncio
import concurrent.futures
from datetime import date, datetime, timedelta
from typing import List
from statistics import mean, stdev
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.tests.utils.insurance import (
    create_test_insurance_policy,
    create_test_insurance_claim,
    create_test_authorization
)

client = TestClient(app)

class PerformanceMetrics:
    """Helper class to track performance metrics."""
    def __init__(self):
        self.response_times = []
        self.error_count = 0
        self.success_count = 0
    
    def add_result(self, response_time: float, success: bool):
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @property
    def avg_response_time(self) -> float:
        return mean(self.response_times) if self.response_times else 0
    
    @property
    def std_response_time(self) -> float:
        return stdev(self.response_times) if len(self.response_times) > 1 else 0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0

async def measure_endpoint_performance(
    endpoint: str,
    method: str = "GET",
    payload: dict = None,
    num_requests: int = 100,
    concurrent_users: int = 10
) -> PerformanceMetrics:
    """Measure performance metrics for an endpoint under load."""
    metrics = PerformanceMetrics()
    
    async def make_request():
        start_time = time.time()
        try:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=payload)
            success = 200 <= response.status_code < 300
        except Exception:
            success = False
        
        end_time = time.time()
        metrics.add_result(end_time - start_time, success)
    
    # Create tasks for concurrent requests
    tasks = []
    for _ in range(num_requests):
        tasks.append(make_request())
    
    # Execute requests with concurrency limit
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        loop = asyncio.get_event_loop()
        await asyncio.gather(*tasks)
    
    return metrics

# Performance Tests

@pytest.mark.performance
async def test_eligibility_check_performance(db: Session, test_policy):
    """Test performance of eligibility check endpoint."""
    endpoint = "/api/v1/insurance/operations/eligibility/check"
    payload = {
        "policy_id": test_policy.id,
        "service_date": date.today().isoformat(),
        "service_types": ["OFFICE_VISIT"]
    }
    
    metrics = await measure_endpoint_performance(
        endpoint=endpoint,
        method="POST",
        payload=payload,
        num_requests=100,
        concurrent_users=10
    )
    
    # Assert performance requirements
    assert metrics.success_rate >= 99.0  # 99% success rate
    assert metrics.avg_response_time < 1.0  # Less than 1 second average
    assert metrics.std_response_time < 0.5  # Low variance

@pytest.mark.performance
async def test_claim_submission_performance(db: Session, test_policy):
    """Test performance of claim submission endpoint."""
    endpoint = "/api/v1/insurance/operations/claims"
    payload = {
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
    
    metrics = await measure_endpoint_performance(
        endpoint=endpoint,
        method="POST",
        payload=payload,
        num_requests=50,
        concurrent_users=5
    )
    
    assert metrics.success_rate >= 99.0
    assert metrics.avg_response_time < 2.0  # Less than 2 seconds average
    assert metrics.std_response_time < 1.0

@pytest.mark.performance
async def test_authorization_request_performance(db: Session, test_policy):
    """Test performance of authorization request endpoint."""
    endpoint = "/api/v1/insurance/operations/authorizations"
    payload = {
        "policy_id": test_policy.id,
        "service_type": "SURGERY",
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=30)).isoformat(),
        "diagnosis_codes": ["M54.5"],
        "procedure_codes": ["99213"]
    }
    
    metrics = await measure_endpoint_performance(
        endpoint=endpoint,
        method="POST",
        payload=payload,
        num_requests=50,
        concurrent_users=5
    )
    
    assert metrics.success_rate >= 99.0
    assert metrics.avg_response_time < 2.0
    assert metrics.std_response_time < 1.0

@pytest.mark.performance
async def test_verification_performance(db: Session, test_policy):
    """Test performance of insurance verification endpoint."""
    endpoint = "/api/v1/insurance/operations/verify"
    payload = {
        "policy_id": test_policy.id,
        "verification_type": "INITIAL",
        "service_types": ["OFFICE_VISIT"],
        "reference_date": date.today().isoformat()
    }
    
    metrics = await measure_endpoint_performance(
        endpoint=endpoint,
        method="POST",
        payload=payload,
        num_requests=50,
        concurrent_users=5
    )
    
    assert metrics.success_rate >= 99.0
    assert metrics.avg_response_time < 3.0  # Less than 3 seconds average
    assert metrics.std_response_time < 1.5

@pytest.mark.performance
async def test_database_query_performance(db: Session):
    """Test performance of database queries."""
    # Create test data
    policies = []
    for _ in range(100):
        policy = create_test_insurance_policy(db)
        policies.append(policy)
    
    start_time = time.time()
    
    # Test policy listing with filtering
    response = client.get(
        "/api/v1/insurance/policies",
        params={
            "skip": 0,
            "limit": 100,
            "status": "ACTIVE"
        }
    )
    
    query_time = time.time() - start_time
    assert response.status_code == 200
    assert query_time < 1.0  # Less than 1 second for 100 records

@pytest.mark.performance
async def test_system_load_performance(db: Session, test_policy):
    """Test system performance under heavy load."""
    # Define test scenarios
    scenarios = [
        {
            "endpoint": "/api/v1/insurance/operations/eligibility/check",
            "method": "POST",
            "payload": {
                "policy_id": test_policy.id,
                "service_date": date.today().isoformat(),
                "service_types": ["OFFICE_VISIT"]
            }
        },
        {
            "endpoint": "/api/v1/insurance/operations/claims",
            "method": "POST",
            "payload": {
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
        }
    ]
    
    # Run scenarios concurrently
    tasks = []
    for scenario in scenarios:
        tasks.append(
            measure_endpoint_performance(
                endpoint=scenario["endpoint"],
                method=scenario["method"],
                payload=scenario["payload"],
                num_requests=25,
                concurrent_users=5
            )
        )
    
    results = await asyncio.gather(*tasks)
    
    # Verify system stability under load
    for metrics in results:
        assert metrics.success_rate >= 95.0  # Allow slightly lower success rate under heavy load
        assert metrics.avg_response_time < 5.0  # Allow higher response time under load
        assert metrics.error_count < 3  # Maximum 2 errors allowed per scenario
