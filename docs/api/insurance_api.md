# Insurance Management API Documentation
Version: 2024-12-19_18-47

## Overview
The Insurance Management API provides comprehensive endpoints for managing insurance operations including policy management, eligibility verification, claims processing, prior authorizations, and insurance verification.

## Base URL
```
/api/v1/insurance
```

## Authentication
All endpoints require authentication using JWT Bearer token:
```http
Authorization: Bearer <your_token>
```

## Common Response Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Basic Insurance Management

### Insurance Companies

#### Create Insurance Company
```http
POST /companies
```

Request Body:
```json
{
  "name": "Blue Cross Blue Shield",
  "code": "BCBS",
  "tax_id": "123456789",
  "npi": "1234567890",
  "address": {
    "street": "123 Main St",
    "city": "Chicago",
    "state": "IL",
    "zip": "60601"
  },
  "contact": {
    "phone": "800-123-4567",
    "email": "contact@bcbs.com"
  }
}
```

Response:
```json
{
  "id": 1,
  "name": "Blue Cross Blue Shield",
  "code": "BCBS",
  "tax_id": "123456789",
  "npi": "1234567890",
  "address": {
    "street": "123 Main St",
    "city": "Chicago",
    "state": "IL",
    "zip": "60601"
  },
  "contact": {
    "phone": "800-123-4567",
    "email": "contact@bcbs.com"
  },
  "is_active": true,
  "created_at": "2024-12-19T18:47:37-06:00",
  "updated_at": "2024-12-19T18:47:37-06:00"
}
```

#### Get Insurance Company
```http
GET /companies/{company_id}
```

Response:
```json
{
  "id": 1,
  "name": "Blue Cross Blue Shield",
  "code": "BCBS",
  // ... other fields as in create response
}
```

### Insurance Policies

#### Create Insurance Policy
```http
POST /policies
```

Request Body:
```json
{
  "policy_number": "POL-123456",
  "payer_id": 1,
  "type_id": 1,
  "patient_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "group_number": "GRP-789",
  "subscriber_id": "SUB-456",
  "subscriber_name": "John Doe",
  "subscriber_relationship": "SELF"
}
```

Response:
```json
{
  "id": 1,
  "policy_number": "POL-123456",
  "payer_id": 1,
  "type_id": 1,
  "patient_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "group_number": "GRP-789",
  "subscriber_id": "SUB-456",
  "subscriber_name": "John Doe",
  "subscriber_relationship": "SELF",
  "status": "ACTIVE",
  "created_at": "2024-12-19T18:47:37-06:00",
  "updated_at": "2024-12-19T18:47:37-06:00"
}
```

## Insurance Operations

### Eligibility Verification

#### Check Eligibility
```http
POST /operations/eligibility/check
```

Request Body:
```json
{
  "policy_id": 1,
  "service_date": "2024-12-19",
  "service_types": ["OFFICE_VISIT"]
}
```

Response:
```json
{
  "is_eligible": true,
  "policy_number": "POL-123456",
  "coverage_status": "ACTIVE",
  "benefits": {
    "deductible": 1000.00,
    "deductible_met": 500.00,
    "out_of_pocket_max": 5000.00,
    "out_of_pocket_met": 1000.00,
    "copay": 25.00,
    "coinsurance": 20.00
  },
  "verification_date": "2024-12-19T18:47:37-06:00"
}
```

### Claims Management

#### Submit Claim
```http
POST /operations/claims
```

Request Body:
```json
{
  "policy_id": 1,
  "service_date": "2024-12-19",
  "diagnosis_codes": ["A00.0"],
  "service_lines": [
    {
      "procedure_code": "99213",
      "quantity": 1,
      "charge_amount": 150.00,
      "diagnosis_pointers": [1]
    }
  ],
  "provider_id": 1,
  "facility_id": 1
}
```

Response:
```json
{
  "id": 1,
  "claim_number": "CLM-123456",
  "policy_id": 1,
  "service_date": "2024-12-19",
  "diagnosis_codes": ["A00.0"],
  "service_lines": [
    {
      "procedure_code": "99213",
      "quantity": 1,
      "charge_amount": 150.00,
      "diagnosis_pointers": [1]
    }
  ],
  "status": "SUBMITTED",
  "total_charge": 150.00,
  "created_at": "2024-12-19T18:47:37-06:00",
  "updated_at": "2024-12-19T18:47:37-06:00"
}
```

### Prior Authorization

#### Request Authorization
```http
POST /operations/authorizations
```

Request Body:
```json
{
  "policy_id": 1,
  "service_type": "SURGERY",
  "start_date": "2024-12-19",
  "end_date": "2025-01-19",
  "diagnosis_codes": ["M54.5"],
  "procedure_codes": ["99213"],
  "provider_id": 1,
  "facility_id": 1
}
```

Response:
```json
{
  "id": 1,
  "authorization_number": "AUTH-123456",
  "policy_id": 1,
  "service_type": "SURGERY",
  "start_date": "2024-12-19",
  "end_date": "2025-01-19",
  "diagnosis_codes": ["M54.5"],
  "procedure_codes": ["99213"],
  "status": "PENDING",
  "created_at": "2024-12-19T18:47:37-06:00",
  "updated_at": "2024-12-19T18:47:37-06:00"
}
```

### Insurance Verification

#### Verify Insurance
```http
POST /operations/verify
```

Request Body:
```json
{
  "policy_id": 1,
  "verification_type": "INITIAL",
  "service_types": ["OFFICE_VISIT"],
  "reference_date": "2024-12-19"
}
```

Response:
```json
{
  "id": 1,
  "policy_verification": {
    "is_active": true,
    "coverage_dates": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "payer_info": {
      "payer_id": "BCBS123",
      "payer_name": "Blue Cross Blue Shield"
    }
  },
  "benefits_verification": {
    "deductible": 1000.00,
    "deductible_met": 500.00,
    "out_of_pocket_max": 5000.00,
    "out_of_pocket_met": 1000.00
  },
  "verification_date": "2024-12-19T18:47:37-06:00",
  "created_at": "2024-12-19T18:47:37-06:00",
  "updated_at": "2024-12-19T18:47:37-06:00"
}
```

## Error Responses

### Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "policy_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Resource Not Found
```json
{
  "detail": "Policy with id 999 not found"
}
```

### External Service Error
```json
{
  "detail": "External service unavailable",
  "error_code": "EXT_SERVICE_ERROR",
  "service": "eligibility_verification"
}
```

## Rate Limiting
- Default rate limit: 100 requests per minute per API key
- Bulk operations: 10 requests per minute
- Headers:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time until rate limit resets

## Webhooks
Webhook notifications are available for:
- Claim status changes
- Authorization status updates
- Policy updates
- Verification completions

Configure webhooks in your account settings with a secure endpoint URL.

## Best Practices
1. Always include appropriate error handling
2. Use pagination for list endpoints
3. Implement retry logic for external service calls
4. Store webhook signatures for security
5. Cache frequently accessed data
6. Use appropriate HTTP methods for operations

## Support
For API support:
- Email: api-support@example.com
- Documentation: https://docs.example.com/api
- Status page: https://status.example.com
