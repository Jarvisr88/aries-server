"""
Billing and Insurance Services Tests
Version: 2024-12-14_19-23
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing import (
    InvoiceService,
    PaymentService,
    InsuranceClaimService,
    BillingCodeService
)
from app.schemas.billing import (
    InvoiceCreate,
    PaymentCreate,
    InsuranceClaimCreate,
    BillingCodeCreate
)
from app.models.billing import PaymentStatus, ClaimStatus

@pytest.mark.asyncio
class TestInvoiceService:
    async def test_create_invoice(self, db: AsyncSession):
        # Arrange
        service = InvoiceService(db)
        invoice_data = InvoiceCreate(
            order_id=1,
            customer_id=1,
            subtotal=Decimal("1000.00"),
            tax=Decimal("80.00"),
            total=Decimal("1080.00"),
            due_date=datetime.utcnow() + timedelta(days=30)
        )

        # Act
        invoice = await service.create(invoice_data, current_user_id=1)

        # Assert
        assert invoice.id is not None
        assert invoice.invoice_number is not None
        assert invoice.total == Decimal("1080.00")

    async def test_generate_invoice_number(self, db: AsyncSession):
        # Arrange
        service = InvoiceService(db)
        invoice_data = InvoiceCreate(
            order_id=1,
            customer_id=1,
            total=Decimal("100.00")
        )

        # Act
        invoice1 = await service.create(invoice_data, current_user_id=1)
        invoice2 = await service.create(invoice_data, current_user_id=1)

        # Assert
        assert invoice1.invoice_number != invoice2.invoice_number
        assert invoice1.invoice_number.startswith("INV")
        assert invoice2.invoice_number.startswith("INV")

    async def test_get_customer_invoices(self, db: AsyncSession):
        # Arrange
        service = InvoiceService(db)
        customer_id = 1
        
        # Create test invoices
        for _ in range(3):
            await service.create(
                InvoiceCreate(
                    order_id=1,
                    customer_id=customer_id,
                    total=Decimal("100.00")
                ),
                current_user_id=1
            )

        # Act
        invoices = await service.get_customer_invoices(customer_id)

        # Assert
        assert len(invoices) == 3
        assert all(inv.customer_id == customer_id for inv in invoices)

@pytest.mark.asyncio
class TestPaymentService:
    async def test_create_payment(self, db: AsyncSession):
        # Arrange
        service = PaymentService(db)
        payment_data = PaymentCreate(
            invoice_id=1,
            amount=Decimal("100.00"),
            payment_type="CREDIT_CARD",
            reference_number="REF123",
            payment_date=datetime.utcnow()
        )

        # Act
        payment = await service.create(payment_data, current_user_id=1)

        # Assert
        assert payment.id is not None
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.amount == Decimal("100.00")

    async def test_void_payment(self, db: AsyncSession):
        # Arrange
        service = PaymentService(db)
        payment_data = PaymentCreate(
            invoice_id=1,
            amount=Decimal("100.00"),
            payment_type="CREDIT_CARD"
        )
        payment = await service.create(payment_data, current_user_id=1)

        # Act
        voided_payment = await service.void_payment(payment.id, "Test void reason")

        # Assert
        assert voided_payment.status == PaymentStatus.VOIDED
        assert voided_payment.void_reason == "Test void reason"

@pytest.mark.asyncio
class TestInsuranceClaimService:
    async def test_create_claim(self, db: AsyncSession):
        # Arrange
        service = InsuranceClaimService(db)
        claim_data = InsuranceClaimCreate(
            invoice_id=1,
            insurance_policy_id=1,
            claim_amount=Decimal("1000.00"),
            diagnosis_codes=["Z99.89"],
            procedure_codes=["E1399"]
        )

        # Act
        claim = await service.create(claim_data, current_user_id=1)

        # Assert
        assert claim.id is not None
        assert claim.claim_number is not None
        assert claim.status == ClaimStatus.PENDING

    async def test_update_claim_status(self, db: AsyncSession):
        # Arrange
        service = InsuranceClaimService(db)
        claim_data = InsuranceClaimCreate(
            invoice_id=1,
            insurance_policy_id=1,
            claim_amount=Decimal("1000.00")
        )
        claim = await service.create(claim_data, current_user_id=1)

        # Act
        updated_claim = await service.update_status(
            claim.id,
            ClaimStatus.APPROVED,
            approved_amount=Decimal("900.00"),
            notes="Partial approval"
        )

        # Assert
        assert updated_claim.status == ClaimStatus.APPROVED
        assert updated_claim.approved_amount == Decimal("900.00")

@pytest.mark.asyncio
class TestBillingCodeService:
    async def test_create_billing_code(self, db: AsyncSession):
        # Arrange
        service = BillingCodeService(db)
        code_data = BillingCodeCreate(
            code="E1399",
            description="Durable Medical Equipment",
            category="DME",
            unit_price=Decimal("100.00")
        )

        # Act
        billing_code = await service.create(code_data, current_user_id=1)

        # Assert
        assert billing_code.id is not None
        assert billing_code.code == "E1399"

    async def test_search_billing_codes(self, db: AsyncSession):
        # Arrange
        service = BillingCodeService(db)
        codes = [
            BillingCodeCreate(
                code=f"E{i}",
                description=f"Test Code {i}",
                category="DME"
            ) for i in range(1, 4)
        ]
        
        for code in codes:
            await service.create(code, current_user_id=1)

        # Act
        search_results = await service.search_codes(query="Test Code", limit=2)

        # Assert
        assert len(search_results) == 2
        assert all("Test Code" in code.description for code in search_results)
