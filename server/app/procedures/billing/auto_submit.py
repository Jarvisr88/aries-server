"""
Invoice Auto-Submit Procedure

Python implementation of the InvoiceDetails_AddAutoSubmit stored procedure.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple
from sqlalchemy import select, and_, or_, case
from sqlalchemy.orm import joinedload
from app.models.billing import (
    Invoice,
    InvoiceDetail,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.models.customer import CustomerInsurance
from app.procedures.base import BaseProcedure


class InvoiceDetailsAutoSubmit(BaseProcedure):
    """
    Adds auto-submit transactions for invoice details.
    
    This procedure:
    1. Validates insurance information
    2. Creates auto-submit transactions
    3. Updates invoice detail status
    """

    async def _execute(
        self,
        invoice_details_id: int,
        insurance_company_id: int,
        transaction_date: datetime,
        last_update_user_id: int
    ) -> Dict[str, str]:
        """Execute the auto-submit procedure"""
        # Step 1: Get invoice details and validate insurance
        invoice_info = await self._get_invoice_info(
            invoice_details_id,
            insurance_company_id
        )
        
        if not invoice_info:
            return {'result': 'InvoiceDetailsNotFound'}

        if not invoice_info['transmitted_insurance_company_id']:
            return {'result': 'InsuranceCompanyNotFound'}

        # Step 2: Check for existing auto-submit
        if await self._has_existing_autosubmit(
            invoice_info['customer_id'],
            invoice_info['invoice_id'],
            invoice_info['invoice_details_id'],
            insurance_company_id
        ):
            return {'result': 'AlreadySubmitted'}

        # Step 3: Create auto-submit transaction
        await self._create_autosubmit_transaction(
            invoice_info,
            transaction_date,
            last_update_user_id
        )

        return {'result': 'Success'}

    async def _get_invoice_info(
        self,
        invoice_details_id: int,
        insurance_company_id: int
    ) -> Optional[Dict]:
        """Get invoice details and validate insurance information"""
        query = (
            select(
                InvoiceDetail.customer_id,
                InvoiceDetail.invoice_id,
                InvoiceDetail.id.label('invoice_details_id'),
                # Determine transmitted insurance ID
                case(
                    (
                        and_(
                            CustomerInsurance.insurance_company_id == insurance_company_id,
                            InvoiceDetail.bill_ins1 == 1
                        ),
                        CustomerInsurance.id
                    ),
                    else_=None
                ).label('transmitted_customer_insurance_id'),
                # Determine transmitted company ID
                case(
                    (
                        and_(
                            CustomerInsurance.insurance_company_id == insurance_company_id,
                            InvoiceDetail.bill_ins1 == 1
                        ),
                        CustomerInsurance.insurance_company_id
                    ),
                    else_=None
                ).label('transmitted_insurance_company_id'),
                InvoiceDetail.billable_amount,
                InvoiceDetail.quantity
            )
            .select_from(InvoiceDetail)
            .join(
                Invoice,
                and_(
                    InvoiceDetail.invoice_id == Invoice.id,
                    InvoiceDetail.customer_id == Invoice.customer_id
                )
            )
            .outerjoin(
                CustomerInsurance,
                and_(
                    CustomerInsurance.id == Invoice.customer_insurance1_id,
                    CustomerInsurance.customer_id == Invoice.customer_id,
                    InvoiceDetail.bill_ins1 == 1
                )
            )
            .where(InvoiceDetail.id == invoice_details_id)
        )

        result = await self.db.execute(query)
        row = result.first()
        
        return dict(row) if row else None

    async def _has_existing_autosubmit(
        self,
        customer_id: int,
        invoice_id: int,
        invoice_details_id: int,
        insurance_company_id: int
    ) -> bool:
        """Check if auto-submit transaction already exists"""
        # Get auto-submit transaction type
        auto_submit_type = await self._get_autosubmit_transaction_type()

        query = (
            select(InvoiceTransaction)
            .where(
                and_(
                    InvoiceTransaction.customer_id == customer_id,
                    InvoiceTransaction.invoice_id == invoice_id,
                    InvoiceTransaction.invoice_details_id == invoice_details_id,
                    InvoiceTransaction.insurance_company_id == insurance_company_id,
                    InvoiceTransaction.transaction_type_id == auto_submit_type.id
                )
            )
        )
        
        result = await self.db.execute(query)
        return result.first() is not None

    async def _get_autosubmit_transaction_type(self) -> InvoiceTransactionType:
        """Get or create Auto-Submit transaction type"""
        query = (
            select(InvoiceTransactionType)
            .where(InvoiceTransactionType.name == 'Auto-Submit')
        )
        auto_submit_type = (await self.db.execute(query)).scalar_one_or_none()

        if not auto_submit_type:
            auto_submit_type = InvoiceTransactionType(
                name='Auto-Submit',
                description='Auto-submitted to insurance'
            )
            self.db.add(auto_submit_type)
            await self.db.flush()

        return auto_submit_type

    async def _create_autosubmit_transaction(
        self,
        invoice_info: Dict,
        transaction_date: datetime,
        last_update_user_id: int
    ) -> None:
        """Create auto-submit transaction"""
        auto_submit_type = await self._get_autosubmit_transaction_type()

        # Create transaction
        transaction = InvoiceTransaction(
            customer_id=invoice_info['customer_id'],
            invoice_id=invoice_info['invoice_id'],
            invoice_details_id=invoice_info['invoice_details_id'],
            transaction_type_id=auto_submit_type.id,
            transaction_date=transaction_date,
            insurance_company_id=invoice_info['transmitted_insurance_company_id'],
            customer_insurance_id=invoice_info['transmitted_customer_insurance_id'],
            amount=invoice_info['billable_amount'],
            quantity=invoice_info['quantity'],
            created_date=func.now(),
            created_by=last_update_user_id
        )
        self.db.add(transaction)

        # Update invoice detail status
        await self._update_invoice_detail_status(
            invoice_info['invoice_details_id'],
            last_update_user_id
        )

    async def _update_invoice_detail_status(
        self,
        invoice_details_id: int,
        last_update_user_id: int
    ) -> None:
        """Update invoice detail status"""
        update_stmt = (
            update(InvoiceDetail)
            .where(InvoiceDetail.id == invoice_details_id)
            .values(
                status='Submitted',
                modified_date=func.now(),
                modified_by=last_update_user_id
            )
        )
        await self.db.execute(update_stmt)
