"""
Customer Management Services Tests
Version: 2024-12-14_19-14
"""
import pytest
from datetime import date
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.customer import (
    CustomerService,
    CustomerAddressService,
    InsuranceCompanyService,
    InsurancePlanService,
    CustomerInsuranceService
)
from app.schemas.customer import (
    CustomerCreate,
    CustomerAddressCreate,
    InsuranceCompanyCreate,
    InsurancePlanCreate,
    CustomerInsuranceCreate
)

@pytest.mark.asyncio
class TestCustomerService:
    async def test_create_customer(self, db: AsyncSession):
        # Arrange
        service = CustomerService(db)
        customer_data = CustomerCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="123-456-7890",
            date_of_birth=date(1990, 1, 1),
            ssn_tax_id="123-45-6789"
        )

        # Act
        customer = await service.create(customer_data, current_user_id=1)

        # Assert
        assert customer.id is not None
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.email == "john@example.com"
        assert customer.ssn_tax_id == "123-45-6789"

    async def test_create_duplicate_customer(self, db: AsyncSession):
        # Arrange
        service = CustomerService(db)
        customer_data = CustomerCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            ssn_tax_id="123-45-6789"
        )

        # Act & Assert
        await service.create(customer_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(customer_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Customer with this SSN/Tax ID already exists" in exc.value.detail

@pytest.mark.asyncio
class TestCustomerAddressService:
    async def test_create_address(self, db: AsyncSession):
        # Arrange
        customer_service = CustomerService(db)
        address_service = CustomerAddressService(db)

        customer_data = CustomerCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        customer = await customer_service.create(customer_data, current_user_id=1)

        address_data = CustomerAddressCreate(
            customer_id=customer.id,
            street="123 Main St",
            city="Anytown",
            state="ST",
            postal_code="12345",
            is_primary=True
        )

        # Act
        address = await address_service.create(address_data, current_user_id=1)

        # Assert
        assert address.id is not None
        assert address.customer_id == customer.id
        assert address.street == "123 Main St"
        assert address.is_primary == True

    async def test_create_multiple_primary_addresses(self, db: AsyncSession):
        # Arrange
        customer_service = CustomerService(db)
        address_service = CustomerAddressService(db)

        customer = await customer_service.create(
            CustomerCreate(first_name="John", last_name="Doe", email="john@example.com"),
            current_user_id=1
        )

        # Create first primary address
        address1_data = CustomerAddressCreate(
            customer_id=customer.id,
            street="123 Main St",
            city="Anytown",
            state="ST",
            postal_code="12345",
            is_primary=True
        )
        address1 = await address_service.create(address1_data, current_user_id=1)

        # Create second primary address
        address2_data = CustomerAddressCreate(
            customer_id=customer.id,
            street="456 Oak St",
            city="Othertown",
            state="ST",
            postal_code="67890",
            is_primary=True
        )
        address2 = await address_service.create(address2_data, current_user_id=1)

        # Assert
        await db.refresh(address1)
        assert address1.is_primary == False
        assert address2.is_primary == True

@pytest.mark.asyncio
class TestInsuranceCompanyService:
    async def test_create_company(self, db: AsyncSession):
        # Arrange
        service = InsuranceCompanyService(db)
        company_data = InsuranceCompanyCreate(
            name="Test Insurance Co",
            contact_email="contact@insurance.com",
            contact_phone="123-456-7890"
        )

        # Act
        company = await service.create(company_data, current_user_id=1)

        # Assert
        assert company.id is not None
        assert company.name == "Test Insurance Co"
        assert company.contact_email == "contact@insurance.com"

    async def test_create_duplicate_company(self, db: AsyncSession):
        # Arrange
        service = InsuranceCompanyService(db)
        company_data = InsuranceCompanyCreate(
            name="Test Insurance Co",
            contact_email="contact@insurance.com"
        )

        # Act & Assert
        await service.create(company_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(company_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Insurance company with this name already exists" in exc.value.detail

@pytest.mark.asyncio
class TestInsurancePlanService:
    async def test_create_plan(self, db: AsyncSession):
        # Arrange
        company_service = InsuranceCompanyService(db)
        plan_service = InsurancePlanService(db)

        company = await company_service.create(
            InsuranceCompanyCreate(name="Test Insurance Co"),
            current_user_id=1
        )

        plan_data = InsurancePlanCreate(
            company_id=company.id,
            name="Basic Plan",
            plan_number="BP001",
            coverage_details={"type": "basic", "coverage": "80%"}
        )

        # Act
        plan = await plan_service.create(plan_data, current_user_id=1)

        # Assert
        assert plan.id is not None
        assert plan.company_id == company.id
        assert plan.name == "Basic Plan"
        assert plan.plan_number == "BP001"

@pytest.mark.asyncio
class TestCustomerInsuranceService:
    async def test_create_customer_insurance(self, db: AsyncSession):
        # Arrange
        customer_service = CustomerService(db)
        company_service = InsuranceCompanyService(db)
        plan_service = InsurancePlanService(db)
        insurance_service = CustomerInsuranceService(db)

        # Create customer
        customer = await customer_service.create(
            CustomerCreate(first_name="John", last_name="Doe", email="john@example.com"),
            current_user_id=1
        )

        # Create insurance company and plan
        company = await company_service.create(
            InsuranceCompanyCreate(name="Test Insurance Co"),
            current_user_id=1
        )
        plan = await plan_service.create(
            InsurancePlanCreate(
                company_id=company.id,
                name="Basic Plan",
                plan_number="BP001"
            ),
            current_user_id=1
        )

        # Create customer insurance
        insurance_data = CustomerInsuranceCreate(
            customer_id=customer.id,
            plan_id=plan.id,
            policy_number="POL123",
            is_primary=True
        )

        # Act
        insurance = await insurance_service.create(insurance_data, current_user_id=1)

        # Assert
        assert insurance.id is not None
        assert insurance.customer_id == customer.id
        assert insurance.plan_id == plan.id
        assert insurance.policy_number == "POL123"
        assert insurance.is_primary == True

    async def test_create_multiple_primary_insurance(self, db: AsyncSession):
        # Arrange
        customer_service = CustomerService(db)
        company_service = InsuranceCompanyService(db)
        plan_service = InsurancePlanService(db)
        insurance_service = CustomerInsuranceService(db)

        # Create customer
        customer = await customer_service.create(
            CustomerCreate(first_name="John", last_name="Doe", email="john@example.com"),
            current_user_id=1
        )

        # Create insurance company and plans
        company = await company_service.create(
            InsuranceCompanyCreate(name="Test Insurance Co"),
            current_user_id=1
        )
        plan1 = await plan_service.create(
            InsurancePlanCreate(
                company_id=company.id,
                name="Plan 1",
                plan_number="P001"
            ),
            current_user_id=1
        )
        plan2 = await plan_service.create(
            InsurancePlanCreate(
                company_id=company.id,
                name="Plan 2",
                plan_number="P002"
            ),
            current_user_id=1
        )

        # Create first primary insurance
        insurance1 = await insurance_service.create(
            CustomerInsuranceCreate(
                customer_id=customer.id,
                plan_id=plan1.id,
                policy_number="POL1",
                is_primary=True
            ),
            current_user_id=1
        )

        # Create second primary insurance
        insurance2 = await insurance_service.create(
            CustomerInsuranceCreate(
                customer_id=customer.id,
                plan_id=plan2.id,
                policy_number="POL2",
                is_primary=True
            ),
            current_user_id=1
        )

        # Assert
        await db.refresh(insurance1)
        assert insurance1.is_primary == False
        assert insurance2.is_primary == True
