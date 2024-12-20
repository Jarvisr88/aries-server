"""
Invoice Details Module

Contains functions for retrieving and managing invoice details.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.invoice import Invoice, InvoiceDetail
from app.models.payment import Payment
from app.models.order import Order
from app.models.customer import Customer
from app.models.insurance import Insurance


def get_invoice_details(
    session: Session,
    invoice_id: int,
    include_payments: bool = True,
    include_order_info: bool = True,
    include_customer_info: bool = True,
    include_insurance_info: bool = True
) -> Dict[str, Any]:
    """
    Get detailed information about an invoice including optional related data
    
    Args:
        session: Database session
        invoice_id: ID of invoice to retrieve
        include_payments: Whether to include payment history
        include_order_info: Whether to include order information
        include_customer_info: Whether to include customer details
        include_insurance_info: Whether to include insurance information
        
    Returns:
        Dictionary containing invoice details and requested related information
    """
    # Get base invoice and details
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")
        
    result = {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
        "total_amount": invoice.total_amount,
        "balance": invoice.balance,
        "status": invoice.status,
        "details": []
    }
    
    # Add invoice line items
    for detail in invoice.details:
        detail_dict = {
            "detail_id": detail.id,
            "item_id": detail.item_id,
            "description": detail.description,
            "quantity": detail.quantity,
            "unit_price": detail.unit_price,
            "total_price": detail.total_price,
            "tax_amount": detail.tax_amount,
            "discount_amount": detail.discount_amount
        }
        result["details"].append(detail_dict)
        
    # Add payment history if requested
    if include_payments:
        result["payments"] = []
        payments = session.execute(
            select(Payment).where(Payment.invoice_id == invoice_id)
        ).scalars().all()
        
        for payment in payments:
            payment_dict = {
                "payment_id": payment.id,
                "payment_date": payment.payment_date,
                "amount": payment.amount,
                "payment_method": payment.payment_method,
                "reference_number": payment.reference_number,
                "status": payment.status
            }
            result["payments"].append(payment_dict)
            
    # Add order information if requested
    if include_order_info and invoice.order_id:
        order = session.get(Order, invoice.order_id)
        if order:
            result["order"] = {
                "order_id": order.id,
                "order_number": order.order_number,
                "order_date": order.order_date,
                "status": order.status,
                "po_number": order.po_number
            }
            
    # Add customer information if requested
    if include_customer_info and invoice.customer_id:
        customer = session.get(Customer, invoice.customer_id)
        if customer:
            result["customer"] = {
                "customer_id": customer.id,
                "name": f"{customer.first_name} {customer.last_name}",
                "email": customer.email,
                "phone": customer.phone,
                "address": {
                    "street": customer.address_street,
                    "city": customer.address_city,
                    "state": customer.address_state,
                    "zip": customer.address_zip
                }
            }
            
    # Add insurance information if requested
    if include_insurance_info and invoice.insurance_id:
        insurance = session.get(Insurance, invoice.insurance_id)
        if insurance:
            result["insurance"] = {
                "insurance_id": insurance.id,
                "provider": insurance.provider_name,
                "policy_number": insurance.policy_number,
                "group_number": insurance.group_number,
                "coverage_type": insurance.coverage_type
            }
            
    return result
