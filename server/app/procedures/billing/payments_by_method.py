"""
Payments By Method Module

Contains functions for retrieving and analyzing payments by payment method.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.payment import Payment


def get_payments_by_method(
    session: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get payments grouped by payment method with optional filtering
    
    Args:
        session: Database session
        start_date: Optional start date filter
        end_date: Optional end date filter
        status: Optional payment status filter
        
    Returns:
        List of dictionaries containing payment information by method
    """
    # Build base query
    query = select(Payment)
    
    # Add filters
    if start_date:
        query = query.where(Payment.payment_date >= start_date)
    if end_date:
        query = query.where(Payment.payment_date <= end_date)
    if status:
        query = query.where(Payment.status == status)
        
    # Execute query
    payments = session.execute(query).scalars().all()
    
    # Group by payment method
    methods = {}
    for payment in payments:
        method = payment.payment_method
        if method not in methods:
            methods[method] = {
                "payment_method": method,
                "total_amount": Decimal('0.00'),
                "payment_count": 0,
                "average_amount": Decimal('0.00'),
                "statuses": {},
                "latest_payment": None,
                "payments": []
            }
            
        meth = methods[method]
        meth["total_amount"] += payment.amount
        meth["payment_count"] += 1
        
        # Track payment statuses
        status = payment.status
        if status in meth["statuses"]:
            meth["statuses"][status]["count"] += 1
            meth["statuses"][status]["amount"] += payment.amount
        else:
            meth["statuses"][status] = {
                "count": 1,
                "amount": payment.amount
            }
            
        # Track latest payment
        if (not meth["latest_payment"] or 
            payment.payment_date > meth["latest_payment"]["payment_date"]):
            meth["latest_payment"] = {
                "payment_id": payment.id,
                "payment_date": payment.payment_date,
                "amount": payment.amount,
                "status": payment.status
            }
            
        # Add to payments list
        meth["payments"].append({
            "payment_id": payment.id,
            "payment_date": payment.payment_date,
            "amount": payment.amount,
            "status": payment.status,
            "invoice_id": payment.invoice_id
        })
        
    # Calculate averages and sort payments
    for method in methods.values():
        method["average_amount"] = (
            method["total_amount"] / method["payment_count"]
            if method["payment_count"] > 0
            else Decimal('0.00')
        )
        method["payments"].sort(key=lambda x: x["payment_date"], reverse=True)
        
    # Convert to sorted list
    result = list(methods.values())
    result.sort(key=lambda x: x["total_amount"], reverse=True)
    
    return result


def get_payment_method_trends(
    session: Session,
    start_date: datetime,
    end_date: datetime,
    method: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get trend analysis for payment methods over time
    
    Args:
        session: Database session
        start_date: Start date for analysis
        end_date: End date for analysis
        method: Optional specific payment method to analyze
        
    Returns:
        Dictionary containing trend analysis
    """
    # Get base payment data
    query = select(Payment).where(
        and_(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        )
    )
    if method:
        query = query.where(Payment.payment_method == method)
        
    payments = session.execute(query).scalars().all()
    
    if not payments:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "payment_method": method,
            "total_payments": 0,
            "total_amount": Decimal('0.00'),
            "trend": "No data available"
        }
        
    # Group payments by method and month
    methods = {}
    for payment in payments:
        month_key = payment.payment_date.replace(day=1)
        method_key = payment.payment_method
        
        if method_key not in methods:
            methods[method_key] = {
                "months": {},
                "total_amount": Decimal('0.00'),
                "payment_count": 0
            }
            
        meth = methods[method_key]
        if month_key not in meth["months"]:
            meth["months"][month_key] = {
                "amount": Decimal('0.00'),
                "count": 0
            }
            
        meth["months"][month_key]["amount"] += payment.amount
        meth["months"][month_key]["count"] += 1
        meth["total_amount"] += payment.amount
        meth["payment_count"] += 1
        
    # Calculate trends for each method
    result = {
        "start_date": start_date,
        "end_date": end_date,
        "methods": {}
    }
    
    for method_key, data in methods.items():
        months = sorted(data["months"].keys())
        if len(months) >= 2:
            first_half = months[:len(months)//2]
            second_half = months[len(months)//2:]
            
            first_half_avg = (
                sum(data["months"][m]["amount"] for m in first_half) /
                len(first_half)
            )
            second_half_avg = (
                sum(data["months"][m]["amount"] for m in second_half) /
                len(second_half)
            )
            
            if second_half_avg > first_half_avg * Decimal('1.1'):
                trend = "Increasing"
            elif second_half_avg < first_half_avg * Decimal('0.9'):
                trend = "Decreasing"
            else:
                trend = "Stable"
        else:
            trend = "Insufficient data for trend analysis"
            
        result["methods"][method_key] = {
            "total_amount": data["total_amount"],
            "payment_count": data["payment_count"],
            "average_per_month": data["total_amount"] / len(months),
            "trend": trend,
            "monthly_data": [
                {
                    "month": month,
                    "amount": data["months"][month]["amount"],
                    "count": data["months"][month]["count"]
                }
                for month in sorted(data["months"].keys())
            ]
        }
        
    return result
