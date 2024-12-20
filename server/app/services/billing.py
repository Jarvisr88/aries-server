"""
Billing and Insurance Services
Version: 2024-12-14_19-23

This module implements services for the Billing and Insurance domain.
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.core.service import BaseService
from app.models.billing import (
    Invoice,
    InvoiceDetail,
    Payment,
    InsuranceClaim,
    BillingCode,
    PaymentStatus,
    ClaimStatus
)
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceUpdate,
    PaymentCreate,
    PaymentUpdate,
    InsuranceClaimCreate,
    InsuranceClaimUpdate,
    BillingCodeCreate,
    BillingCodeUpdate
)
from app.core.logging import logger

class InvoiceService(BaseService[Invoice, InvoiceCreate, InvoiceUpdate]):
    """Service for managing invoices"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Invoice, db)
    
    async def create(self, schema: InvoiceCreate, current_user_id: int, **kwargs) -> Invoice:
        """Create a new invoice"""
        try:
            # Generate invoice number
            invoice_number = await self._generate_invoice_number()
            
            # Create invoice
            data = schema.model_dump()
            data.update(kwargs)
            data["invoice_number"] = invoice_number
            data["status"] = "PENDING"
            
            db_invoice = Invoice(**data)
            self.db.add(db_invoice)
            
            await self.db.commit()
            await self.db.refresh(db_invoice)
            
            logger.info(f"Created new invoice: {db_invoice.invoice_number}")
            return db_invoice
            
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create invoice"
            ) from e
    
    async def _generate_invoice_number(self) -> str:
        """Generate a unique invoice number"""
        try:
            # Get the latest invoice number
            query = select(Invoice).order_by(Invoice.id.desc())
            result = await self.db.execute(query)
            latest_invoice = result.scalar_one_or_none()
            
            if latest_invoice and latest_invoice.invoice_number:
                # Extract number from INV0000X format
                num = int(latest_invoice.invoice_number[3:]) + 1
            else:
                num = 1
            
            return f"INV{num:05d}"
            
        except Exception as e:
            logger.error(f"Error generating invoice number: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not generate invoice number"
            ) from e
    
    async def get_customer_invoices(
        self,
        customer_id: int,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Invoice]:
        """Get invoices for a customer"""
        try:
            conditions = [Invoice.customer_id == customer_id]
            if status:
                conditions.append(Invoice.status == status)
            
            query = select(Invoice).where(
                and_(*conditions)
            ).order_by(Invoice.created_at.desc())
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting customer invoices: {str(e)}")
            return []

class PaymentService(BaseService[Payment, PaymentCreate, PaymentUpdate]):
    """Service for managing payments"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Payment, db)
    
    async def create(self, schema: PaymentCreate, current_user_id: int, **kwargs) -> Payment:
        """Create a new payment"""
        try:
            # Create payment
            data = schema.model_dump()
            data.update(kwargs)
            data["status"] = PaymentStatus.COMPLETED
            
            db_payment = Payment(**data)
            self.db.add(db_payment)
            
            # Update invoice paid amount
            invoice = await self.db.get(Invoice, schema.invoice_id)
            if invoice:
                invoice.paid_amount = (invoice.paid_amount or Decimal("0")) + schema.amount
                if invoice.paid_amount >= invoice.total:
                    invoice.status = "PAID"
            
            await self.db.commit()
            await self.db.refresh(db_payment)
            
            logger.info(f"Created new payment: {db_payment.id}")
            return db_payment
            
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create payment"
            ) from e
    
    async def void_payment(self, payment_id: int, void_reason: str) -> Payment:
        """Void a payment"""
        try:
            payment = await self.get(payment_id)
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            if payment.status == PaymentStatus.VOIDED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment is already voided"
                )
            
            # Update payment status
            payment.status = PaymentStatus.VOIDED
            payment.void_reason = void_reason
            payment.void_date = datetime.utcnow()
            
            # Update invoice paid amount
            invoice = await self.db.get(Invoice, payment.invoice_id)
            if invoice:
                invoice.paid_amount = (invoice.paid_amount or Decimal("0")) - payment.amount
                if invoice.paid_amount < invoice.total:
                    invoice.status = "PARTIAL"
            
            await self.db.commit()
            await self.db.refresh(payment)
            
            logger.info(f"Voided payment: {payment.id}")
            return payment
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error voiding payment: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not void payment"
            ) from e

class InsuranceClaimService(BaseService[InsuranceClaim, InsuranceClaimCreate, InsuranceClaimUpdate]):
    """Service for managing insurance claims"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InsuranceClaim, db)
    
    async def create(self, schema: InsuranceClaimCreate, current_user_id: int, **kwargs) -> InsuranceClaim:
        """Create a new insurance claim"""
        try:
            # Generate claim number
            claim_number = await self._generate_claim_number()
            
            # Create claim
            data = schema.model_dump()
            data.update(kwargs)
            data["claim_number"] = claim_number
            data["status"] = ClaimStatus.PENDING
            
            db_claim = InsuranceClaim(**data)
            self.db.add(db_claim)
            
            await self.db.commit()
            await self.db.refresh(db_claim)
            
            logger.info(f"Created new insurance claim: {db_claim.claim_number}")
            return db_claim
            
        except Exception as e:
            logger.error(f"Error creating insurance claim: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create insurance claim"
            ) from e
    
    async def _generate_claim_number(self) -> str:
        """Generate a unique claim number"""
        try:
            # Get the latest claim number
            query = select(InsuranceClaim).order_by(InsuranceClaim.id.desc())
            result = await self.db.execute(query)
            latest_claim = result.scalar_one_or_none()
            
            if latest_claim and latest_claim.claim_number:
                # Extract number from CLM0000X format
                num = int(latest_claim.claim_number[3:]) + 1
            else:
                num = 1
            
            return f"CLM{num:05d}"
            
        except Exception as e:
            logger.error(f"Error generating claim number: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not generate claim number"
            ) from e
    
    async def update_status(
        self,
        claim_id: int,
        new_status: ClaimStatus,
        approved_amount: Optional[Decimal] = None,
        notes: Optional[str] = None
    ) -> InsuranceClaim:
        """Update claim status"""
        try:
            claim = await self.get(claim_id)
            if not claim:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance claim not found"
                )
            
            claim.status = new_status
            if approved_amount is not None:
                claim.approved_amount = approved_amount
            if notes:
                claim.notes = notes
            
            # If claim is approved, create payment
            if new_status == ClaimStatus.APPROVED and approved_amount:
                payment_data = PaymentCreate(
                    invoice_id=claim.invoice_id,
                    amount=approved_amount,
                    payment_type="INSURANCE",
                    reference_number=claim.claim_number
                )
                payment_service = PaymentService(self.db)
                await payment_service.create(payment_data, None)
            
            await self.db.commit()
            await self.db.refresh(claim)
            
            logger.info(f"Updated insurance claim status: {claim.claim_number} -> {new_status}")
            return claim
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating insurance claim status: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update insurance claim status"
            ) from e

class BillingCodeService(BaseService[BillingCode, BillingCodeCreate, BillingCodeUpdate]):
    """Service for managing billing codes"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(BillingCode, db)
    
    async def create(self, schema: BillingCodeCreate, current_user_id: int, **kwargs) -> BillingCode:
        """Create a new billing code"""
        try:
            # Check for duplicate code
            query = select(BillingCode).where(BillingCode.code == schema.code)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Billing code already exists"
                )
            
            # Create billing code
            data = schema.model_dump()
            data.update(kwargs)
            db_code = BillingCode(**data)
            self.db.add(db_code)
            
            await self.db.commit()
            await self.db.refresh(db_code)
            
            logger.info(f"Created new billing code: {db_code.code}")
            return db_code
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating billing code: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create billing code"
            ) from e
    
    async def search_codes(
        self,
        query: str,
        category: Optional[str] = None,
        is_active: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[BillingCode]:
        """Search billing codes"""
        try:
            conditions = []
            if query:
                conditions.append(
                    or_(
                        BillingCode.code.ilike(f"%{query}%"),
                        BillingCode.description.ilike(f"%{query}%")
                    )
                )
            if category:
                conditions.append(BillingCode.category == category)
            if is_active is not None:
                conditions.append(BillingCode.is_active == is_active)
            
            query = select(BillingCode)
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching billing codes: {str(e)}")
            return []
