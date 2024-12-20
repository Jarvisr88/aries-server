"""
Invoice Payments Module

Contains functions for retrieving and managing invoice payments.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.payment import Payment


def get_invoice_payments(
    session: Session,
    invoice_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get payment history for an invoice with optional filtering
    
    Args:
        session: Database session
        invoice_id: ID of invoice to get payments for
        start_date: Optional start date filter
        end_date: Optional end date filter
        payment_method: Optional payment method filter
        status: Optional payment status filter
        
    Returns:
        List of dictionaries containing payment information
    """
    # Build base query
    query = select(Payment).where(Payment.invoice_id == invoice_id)
    
    # Add date range filter if provided
    if start_date:
        query = query.where(Payment.payment_date >= start_date)
    if end_date:
        query = query.where(Payment.payment_date <= end_date)
        
    # Add payment method filter if provided
    if payment_method:
        query = query.where(Payment.payment_method == payment_method)
        
    # Add status filter if provided
    if status:
        query = query.where(Payment.status == status)
        
    # Execute query and format results
    payments = session.execute(query).scalars().all()
    
    result = []
    for payment in payments:
        payment_dict = {
            "payment_id": payment.id,
            "payment_date": payment.payment_date,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "reference_number": payment.reference_number,
            "status": payment.status,
            "created_at": payment.created_at,
            "created_by": payment.created_by,
            "updated_at": payment.updated_at,
            "updated_by": payment.updated_by
        }
        
        # Add any payment-specific fields
        if payment.check_number:
            payment_dict["check_number"] = payment.check_number
        if payment.card_last4:
            payment_dict["card_last4"] = payment.card_last4
        if payment.card_type:
            payment_dict["card_type"] = payment.card_type
        if payment.authorization_code:
            payment_dict["authorization_code"] = payment.authorization_code
            
        result.append(payment_dict)
        
    return result


def get_payment_summary(
    session: Session,
    invoice_id: int
) -> Dict[str, Any]:
    """
    Get a summary of payments for an invoice
    
    Args:
        session: Database session
        invoice_id: ID of invoice to get payment summary for
        
    Returns:
        Dictionary containing payment summary information
    """
    payments = get_invoice_payments(session, invoice_id)
    
    total_paid = sum(payment["amount"] for payment in payments)
    payment_methods = {}
    payment_statuses = {}
    
    for payment in payments:
        # Count by payment method
        method = payment["payment_method"]
        if method in payment_methods:
            payment_methods[method]["count"] += 1
            payment_methods[method]["total"] += payment["amount"]
        else:
            payment_methods[method] = {
                "count": 1,
                "total": payment["amount"]
            }
            
        # Count by status
        status = payment["status"]
        if status in payment_statuses:
            payment_statuses[status]["count"] += 1
            payment_statuses[status]["total"] += payment["amount"]
        else:
            payment_statuses[status] = {
                "count": 1,
                "total": payment["amount"]
            }
            
    return {
        "total_payments": len(payments),
        "total_amount_paid": total_paid,
        "payment_methods": payment_methods,
        "payment_statuses": payment_statuses,
        "first_payment_date": min(p["payment_date"] for p in payments) if payments else None,
        "last_payment_date": max(p["payment_date"] for p in payments) if payments else None
    }
