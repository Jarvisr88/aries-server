"""
Invoice Balance Module

Contains functions for calculating and managing invoice balances.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.invoice import Invoice, InvoiceDetail
from app.models.payment import Payment
from app.models.adjustment import Adjustment


def get_invoice_balance(
    session: Session,
    invoice_id: int,
    as_of_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculate current balance and payment status for an invoice
    
    Args:
        session: Database session
        invoice_id: ID of invoice to calculate balance for
        as_of_date: Optional date to calculate balance as of
        
    Returns:
        Dictionary containing balance information
    """
    # Get invoice
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")
        
    # Calculate original amount
    original_amount = Decimal('0.00')
    for detail in invoice.details:
        original_amount += detail.total_price + detail.tax_amount - detail.discount_amount
        
    # Get payments up to as_of_date
    payments_query = select(Payment).where(
        Payment.invoice_id == invoice_id,
        Payment.status == 'Completed'  # Only count completed payments
    )
    if as_of_date:
        payments_query = payments_query.where(Payment.payment_date <= as_of_date)
        
    total_payments = sum(
        payment.amount 
        for payment in session.execute(payments_query).scalars().all()
    )
    
    # Get adjustments up to as_of_date
    adjustments_query = select(Adjustment).where(
        Adjustment.invoice_id == invoice_id,
        Adjustment.status == 'Approved'  # Only count approved adjustments
    )
    if as_of_date:
        adjustments_query = adjustments_query.where(Adjustment.adjustment_date <= as_of_date)
        
    adjustments = session.execute(adjustments_query).scalars().all()
    total_adjustments = sum(adj.amount for adj in adjustments)
    
    # Calculate current balance
    current_balance = original_amount - total_payments + total_adjustments
    
    # Determine payment status
    payment_status = _determine_payment_status(
        original_amount, 
        current_balance,
        invoice.due_date,
        as_of_date or datetime.now()
    )
    
    return {
        "invoice_id": invoice_id,
        "original_amount": original_amount,
        "total_payments": total_payments,
        "total_adjustments": total_adjustments,
        "current_balance": current_balance,
        "payment_status": payment_status,
        "last_payment_date": max(
            (p.payment_date for p in invoice.payments if p.status == 'Completed'),
            default=None
        ),
        "last_adjustment_date": max(
            (a.adjustment_date for a in adjustments),
            default=None
        ),
        "as_of_date": as_of_date or datetime.now()
    }


def _determine_payment_status(
    original_amount: Decimal,
    current_balance: Decimal,
    due_date: datetime,
    as_of_date: datetime
) -> str:
    """
    Determine payment status based on balance and dates
    
    Args:
        original_amount: Original invoice amount
        current_balance: Current balance
        due_date: Invoice due date
        as_of_date: Date to check status as of
        
    Returns:
        Payment status string
    """
    if current_balance <= 0:
        return "Paid in Full"
        
    if current_balance >= original_amount:
        if as_of_date > due_date:
            return "Past Due"
        else:
            return "Not Paid"
            
    if current_balance > 0:
        if as_of_date > due_date:
            return "Partially Paid - Past Due"
        else:
            return "Partially Paid"
            
    return "Unknown"


def get_aging_info(
    session: Session,
    invoice_id: int,
    as_of_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get aging information for an invoice
    
    Args:
        session: Database session
        invoice_id: ID of invoice to get aging for
        as_of_date: Optional date to calculate aging as of
        
    Returns:
        Dictionary containing aging information
    """
    balance_info = get_invoice_balance(session, invoice_id, as_of_date)
    invoice = session.get(Invoice, invoice_id)
    
    as_of = as_of_date or datetime.now()
    days_outstanding = (as_of - invoice.due_date).days if as_of > invoice.due_date else 0
    
    aging_buckets = {
        "current": Decimal('0.00'),
        "30_days": Decimal('0.00'),
        "60_days": Decimal('0.00'),
        "90_days": Decimal('0.00'),
        "120_plus_days": Decimal('0.00')
    }
    
    if days_outstanding <= 0:
        aging_buckets["current"] = balance_info["current_balance"]
    elif days_outstanding <= 30:
        aging_buckets["30_days"] = balance_info["current_balance"]
    elif days_outstanding <= 60:
        aging_buckets["60_days"] = balance_info["current_balance"]
    elif days_outstanding <= 90:
        aging_buckets["90_days"] = balance_info["current_balance"]
    else:
        aging_buckets["120_plus_days"] = balance_info["current_balance"]
        
    return {
        "invoice_id": invoice_id,
        "days_outstanding": days_outstanding,
        "aging_buckets": aging_buckets,
        "as_of_date": as_of,
        "current_balance": balance_info["current_balance"],
        "payment_status": balance_info["payment_status"]
    }
