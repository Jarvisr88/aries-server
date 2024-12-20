"""
Payments By Customer Module

Contains functions for retrieving and analyzing payments by customer.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.customer import Customer


def get_payments_by_customer(
    session: Session,
    customer_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get payments for a specific customer or all customers with optional filtering
    
    Args:
        session: Database session
        customer_id: Optional customer ID to filter by
        start_date: Optional start date filter
        end_date: Optional end date filter
        payment_method: Optional payment method filter
        status: Optional payment status filter
        
    Returns:
        List of dictionaries containing payment information by customer
    """
    # Build base query joining payments to invoices and customers
    query = (
        select(Payment, Invoice, Customer)
        .join(Invoice, Payment.invoice_id == Invoice.id)
        .join(Customer, Invoice.customer_id == Customer.id)
    )
    
    # Add filters
    if customer_id:
        query = query.where(Customer.id == customer_id)
    if start_date:
        query = query.where(Payment.payment_date >= start_date)
    if end_date:
        query = query.where(Payment.payment_date <= end_date)
    if payment_method:
        query = query.where(Payment.payment_method == payment_method)
    if status:
        query = query.where(Payment.status == status)
        
    # Execute query
    results = session.execute(query).all()
    
    # Group by customer
    customers = {}
    for payment, invoice, customer in results:
        if customer.id not in customers:
            customers[customer.id] = {
                "customer_id": customer.id,
                "customer_name": f"{customer.first_name} {customer.last_name}",
                "total_amount": Decimal('0.00'),
                "payment_count": 0,
                "payment_methods": {},
                "statuses": {},
                "latest_payment": None,
                "payments": []
            }
            
        cust = customers[customer.id]
        cust["total_amount"] += payment.amount
        cust["payment_count"] += 1
        
        # Track payment methods
        method = payment.payment_method
        if method in cust["payment_methods"]:
            cust["payment_methods"][method]["count"] += 1
            cust["payment_methods"][method]["amount"] += payment.amount
        else:
            cust["payment_methods"][method] = {
                "count": 1,
                "amount": payment.amount
            }
            
        # Track payment statuses
        status = payment.status
        if status in cust["statuses"]:
            cust["statuses"][status]["count"] += 1
            cust["statuses"][status]["amount"] += payment.amount
        else:
            cust["statuses"][status] = {
                "count": 1,
                "amount": payment.amount
            }
            
        # Track latest payment
        if (not cust["latest_payment"] or 
            payment.payment_date > cust["latest_payment"]["payment_date"]):
            cust["latest_payment"] = {
                "payment_id": payment.id,
                "payment_date": payment.payment_date,
                "amount": payment.amount,
                "payment_method": payment.payment_method,
                "status": payment.status
            }
            
        # Add to payments list
        cust["payments"].append({
            "payment_id": payment.id,
            "payment_date": payment.payment_date,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "status": payment.status,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number
        })
        
    # Convert to sorted list
    result = list(customers.values())
    result.sort(key=lambda x: x["total_amount"], reverse=True)
    
    return result


def get_customer_payment_summary(
    session: Session,
    customer_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get a summary of payment activity for a specific customer
    
    Args:
        session: Database session
        customer_id: Customer ID to get summary for
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Dictionary containing payment summary information
    """
    payments = get_payments_by_customer(
        session,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not payments:
        return {
            "customer_id": customer_id,
            "total_payments": 0,
            "total_amount": Decimal('0.00'),
            "payment_methods": {},
            "payment_statuses": {},
            "latest_payment": None,
            "start_date": start_date,
            "end_date": end_date
        }
        
    customer_data = payments[0]  # Will only be one customer since we filtered
    
    return {
        "customer_id": customer_id,
        "customer_name": customer_data["customer_name"],
        "total_payments": customer_data["payment_count"],
        "total_amount": customer_data["total_amount"],
        "payment_methods": customer_data["payment_methods"],
        "payment_statuses": customer_data["statuses"],
        "latest_payment": customer_data["latest_payment"],
        "average_payment": (
            customer_data["total_amount"] / customer_data["payment_count"]
            if customer_data["payment_count"] > 0
            else Decimal('0.00')
        ),
        "start_date": start_date,
        "end_date": end_date
    }
